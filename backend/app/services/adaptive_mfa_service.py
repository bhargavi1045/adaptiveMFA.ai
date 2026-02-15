from typing import Dict, Any, Optional, Tuple, List
from sqlalchemy.orm import Session
import hashlib
from datetime import datetime, timezone

from app.models.user import User
from app.models.login_event import LoginEvent
from app.services.auth_service import AuthService
from app.utils.logger import logger
from app.services.risk_service import RiskAssessmentService


class RiskBasedAdaptiveMFA:

    def __init__(self):
        self.risk_service = RiskAssessmentService()
        logger.info("Risk-Based Adaptive MFA initialized")

    def assess_login(
        self,
        user_id: str,
        login_event: Dict[str, Any],
        db: Session,
    ) -> Dict[str, Any]:
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.error(f"User not found: {user_id}")
                return self._error_response()

            # Risk assessment
            risk_data = self.risk_service.assess_login(login_event, user, db)
            risk_score = risk_data["risk_score"]
            risk_level = risk_data["risk_level"]

            # Determine MFA requirement
            mfa_methods = []
            if user.mfa_enabled:
                if risk_score > 0.3:
                    mfa_methods.append("totp")

            # Block if critical risk
            blocked = False
            block_reason = None
            if (risk_score > 0.95 and 
                not risk_data["device_known"] and 
                risk_data["behavior_risk"] == "high"):
                blocked = True
                block_reason = "Critical risk: Unknown device with anomalous behavior"
                logger.warning(f"Login blocked for {user.email}: {block_reason}")

            return {
                "blocked": blocked,
                "block_reason": block_reason,
                "risk_score": risk_data["risk_score"],
                "risk_level": risk_level,
                "explanation": risk_data["explanation"],
                "device_fingerprint": risk_data["device_fingerprint"],
                "device_known": risk_data["device_known"],
                "last_seen": risk_data["last_seen"],
                "behavior_risk": risk_data["behavior_risk"],
                "mfa_methods_required": mfa_methods,
                "mfa_required": bool(mfa_methods),
            }

        except Exception as e:
            logger.error(f"Login risk assessment failed: {e}")
            return self._error_response()

    @staticmethod
    def _error_response() -> Dict[str, Any]:
        return {
            "blocked": False,
            "block_reason": None,
            "risk_score": 0.5,
            "risk_level": "medium",
            "explanation": "Unable to assess risk - defaulting to MFA",
            "device_fingerprint": None,
            "device_known": False,
            "last_seen": None,
            "behavior_risk": "medium",
            "mfa_methods_required": ["totp"],
            "mfa_required": True,
        }


class AdaptiveMFARouter:

    @staticmethod
    def get_login_response(
        risk_assessment: Dict[str, Any], user: User, db: Session
    ) -> Dict[str, Any]:
        try:
            risk_level = risk_assessment.get("risk_level", "medium")
            risk_score = risk_assessment.get("risk_score", 0.5)

            # Low-risk: issue tokens immediately
            if risk_level == "low" and user.mfa_enabled is False:
                access_token, access_jti, access_exp = AuthService.create_access_token(str(user.id))
                refresh_token, refresh_jti, refresh_exp = AuthService.create_refresh_token(str(user.id))

                AuthService.create_session(
                    db, str(user.id), access_jti, access_exp,
                    token_type="access",
                    device_fingerprint=risk_assessment.get("device_fingerprint"),
                    ip_address=risk_assessment.get("ip_address")
                )
                AuthService.create_session(
                    db, str(user.id), refresh_jti, refresh_exp,
                    token_type="refresh"
                )

                logger.info(f"Low-risk login (no MFA required): {user.email}")

                return {
                    "message": "Login successful",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer",
                    "user": {
                        "id": str(user.id),
                        "email": user.email,
                        "is_active": user.is_active,
                        "is_verified": user.is_verified,
                        "mfa_enabled": user.mfa_enabled,
                        "created_at": user.created_at,
                    },
                    "mfa_required": False,
                    "risk_score": risk_score,
                    "risk_level": risk_level,
                    "instructions": "Welcome back!",
                }

            mfa_token, mfa_jti, mfa_exp = AuthService.create_mfa_token(str(user.id))
            AuthService.create_session(
                db, str(user.id), mfa_jti, mfa_exp,
                token_type="mfa"
            )

            response = {
                "message": "Password verified - MFA required",
                "mfa_token": mfa_token,
                "token_type": "bearer",
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "is_active": user.is_active,
                    "is_verified": user.is_verified,
                    "mfa_enabled": user.mfa_enabled,
                    "created_at": user.created_at,
                },
                "mfa_required": True,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "device_known": risk_assessment.get("device_known", False),
                "instructions": AdaptiveMFARouter._get_instructions(risk_assessment),
            }

            if risk_assessment.get("blocked"):
                logger.warning(f"Login blocked: {risk_assessment.get('block_reason')}")
                response["blocked"] = True
                response["block_reason"] = risk_assessment.get("block_reason")

            return response

        except Exception as e:
            logger.error(f"Login response generation failed: {e}")
            raise

    @staticmethod
    def _get_instructions(risk_assessment: Dict[str, Any]) -> str:
        
        risk_level = risk_assessment.get("risk_level", "medium")
        behavior_risk = risk_assessment.get("behavior_risk", "low")
        device_known = risk_assessment.get("device_known", False)

        if risk_level == "high" and behavior_risk == "high":
            return "Unusual activity detected. Please verify with your authenticator."
        elif risk_level == "high" and not device_known:
            return "Unknown device detected. Please verify with your authenticator."
        elif risk_level == "medium":
            return "Standard MFA verification required."

        return "Please verify with your authenticator app."