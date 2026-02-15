from typing import TypedDict, Any, Literal, Optional
from datetime import datetime
from langgraph.graph import StateGraph, END
from app.config import settings
from app.utils.logger import logger
from app.services.anomaly_service import AnomalyService
from app.services.risk_service import RiskAssessmentService
from app.services.rag_service import RAGService


from groq import Groq


class RiskAssessmentState(TypedDict):
    """State passed through LangGraph nodes"""
    login_event: dict
    user_history: Optional[dict]
    anomaly_score: float
    risk_score: float
    should_do_rag: bool
    similar_cases: list
    explanation: str
    action_required: bool
    recommendation: str


class LangGraphWorkflow:
    """Orchestrates multi-stage risk assessment workflow using LangGraph"""

    def __init__(
        self,
        anomaly_service: AnomalyService,
        rag_service: RAGService,
        groq_api_key: str,
        groq_model_name: str = "openai/gpt-oss-20b"
    ):
        # Initialize Groq client
        self.anomaly_service = anomaly_service
        self.rag_service = rag_service

        # Initialize Groq client
        self.llm = Groq(api_key=groq_api_key)
        self.groq_model_name = groq_model_name

        self.graph = self._build_graph()
        logger.info("LangGraph workflow compiled")

    def _build_graph(self) -> Any:
        """Build LangGraph workflow"""
        workflow = StateGraph(RiskAssessmentState)

        # Add nodes
        workflow.add_node("detect_anomaly", self.detect_anomaly_node)
        workflow.add_node("score_risk", self.score_risk_node)
        workflow.add_node("retrieve_context", self.retrieve_context_node)
        workflow.add_node("generate_explanation", self.generate_explanation_node)

        # Add edges
        workflow.set_entry_point("detect_anomaly")
        workflow.add_edge("detect_anomaly", "score_risk")

        # Conditional routing: medium/high risk go to RAG
        workflow.add_conditional_edges(
            "score_risk",
            self.should_do_rag,
            {
                "retrieve": "retrieve_context",
                "skip": "generate_explanation"
            }
        )

        workflow.add_edge("retrieve_context", "generate_explanation")
        workflow.add_edge("generate_explanation", END)

        return workflow.compile()

    def detect_anomaly_node(self, state: RiskAssessmentState) -> RiskAssessmentState:
        """Step 1: Detect anomalies using ML"""
        logger.info("Detecting anomaly...")
        try:
            anomaly_score = self.anomaly_service.detect_anomaly(state["login_event"])
            logger.info(f"Anomaly detected: {anomaly_score:.3f}")
            return {**state, "anomaly_score": anomaly_score}
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
            return {**state, "anomaly_score": 0.5}

    def score_risk_node(self, state: RiskAssessmentState) -> RiskAssessmentState:
        """Step 2: Calculate overall risk score"""
        logger.info("Scoring risk...")
        try:
            risk_score = RiskAssessmentService.calculate_risk_score(
                state["anomaly_score"],
                state["login_event"],
                state.get("user_history")
            )
            recommendation = RiskAssessmentService.get_recommendation(risk_score)
            action_required = risk_score > settings.RISK_THRESHOLD_HIGH
            logger.info(f"Risk scored: {risk_score:.3f} ({RiskAssessmentService.get_risk_level(risk_score)})")
            return {
                **state,
                "risk_score": risk_score,
                "recommendation": recommendation,
                "action_required": action_required
            }
        except Exception as e:
            logger.error(f"Error in risk scoring: {e}")
            return {"risk_score": 0.5, "recommendation": "verify", "action_required": True}

    def should_do_rag(self, state: RiskAssessmentState) -> Literal["retrieve", "skip"]:
        """Conditional: Do RAG for medium-to-high risk logins"""
        if state["risk_score"] < settings.RISK_THRESHOLD_LOW:
            logger.info(f"Risk {state['risk_score']:.3f} - skipping RAG")
            return "skip"
        else:
            logger.info(f"Risk {state['risk_score']:.3f} - retrieving similar cases")
            return "retrieve"

    def retrieve_context_node(self, state: RiskAssessmentState) -> RiskAssessmentState:
        """Step 3: Retrieve similar cases from vector DB"""
        logger.info("Retrieving similar cases...")
        try:
            similar_cases = self.rag_service.retrieve_similar_cases(state["login_event"], top_k=3)
            logger.info(f"Retrieved {len(similar_cases)} similar cases")
            return {**state, "similar_cases": similar_cases}
        except Exception as e:
            logger.error(f"Error retrieving similar cases: {e}")
            return {**state, "similar_cases": []}

    def generate_explanation_node(self, state: RiskAssessmentState) -> RiskAssessmentState:
        """Step 4: Generate explanation using Groq"""
        logger.info("Generating explanation...")
        try:
            context = self._build_llm_context(state)
            prompt = self._build_explanation_prompt(context, state)

            # Groq chat API call
            response = self.llm.chat.completions.create(
                model=self.groq_model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            explanation = response.choices[0].message.content

            logger.info("Explanation generated")
            return {**state, "explanation": explanation}

        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            return {**state, "explanation": f"Risk assessment complete. Score: {state['risk_score']:.1%}"}

    def _build_llm_context(self, state: RiskAssessmentState) -> str:
        
        login = state["login_event"]
        context = f"""
                    Login Information:
                        - User ID: {login.get('user_id', 'unknown')}
                        - IP Address: {login.get('ip_address', 'unknown')}
                        - Location: {login.get('location', 'unknown')}
                        - Device: {login.get('device_fingerprint', 'unknown')[:16]}...
                        - Timestamp: {login.get('timestamp', 'unknown')}

                    Risk Scores:
                        - Anomaly Score: {state['anomaly_score']:.1%}
                        - Overall Risk: {state['risk_score']:.1%}
                  """
        
        if state["similar_cases"]:
            context += "\nSimilar Historical Cases:\n"
            for i, case in enumerate(state["similar_cases"], 1):
                context += f"{i}. {case.get('explanation', 'N/A')}\n"
                context += f"   Outcome: {case.get('outcome', 'unknown')}\n"
        return context

    def _build_explanation_prompt(self, context: str, state: RiskAssessmentState) -> str:
        """Build prompt for LLM explanation"""
        risk_level = RiskAssessmentService.get_risk_level(state["risk_score"])
        prompt = f"""You are a security analyst. Analyze the following login attempt and provide a concise explanation of the risk in 2-3 sentences.

{context}

Risk Level: {risk_level}
Recommendation: {state["recommendation"].upper()}

Provide a brief, clear explanation suitable for a security dashboard."""
        return prompt

    def invoke(self, login_event: dict, user_history: Optional[dict] = None) -> dict:
        """Run the complete workflow"""
        logger.info("="*50)
        logger.info("Starting risk assessment workflow")
        logger.info("="*50)

        initial_state: RiskAssessmentState = {
            "login_event": login_event,
            "user_history": user_history,
            "anomaly_score": 0.0,
            "risk_score": 0.0,
            "should_do_rag": False,
            "similar_cases": [],
            "explanation": "",
            "action_required": False,
            "recommendation": "verify"
        }

        try:
            result = self.graph.invoke(initial_state)
            logger.info("="*50)
            logger.info(f"Workflow completed - Risk: {result['risk_score']:.1%}")
            logger.info("="*50)

            return {
                "risk_score": result["risk_score"],
                "anomaly_score": result["anomaly_score"],
                "explanation": result["explanation"],
                "similar_cases": result["similar_cases"],
                "action_required": result["action_required"],
                "recommendation": result["recommendation"],
            }
        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            return {
                "risk_score": 0.5,
                "anomaly_score": 0.5,
                "explanation": f"Error during assessment: {str(e)}",
                "similar_cases": [],
                "action_required": True,
                "recommendation": "verify",
            }