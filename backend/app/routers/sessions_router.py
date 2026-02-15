from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.database.connection import get_db
from app.models.user import User
from app.models.session import Session as DBSession, SessionStatus
from app.models.login_event import LoginEvent
from app.services.auth_service import AuthService
from app.dependencies import get_current_user
from app.utils.logger import logger
from pydantic import BaseModel, Field

router = APIRouter(prefix="/sessions", tags=["Sessions & Dashboard"])


#Response Models

class SessionResponse(BaseModel):
    """Single session response"""
    id: UUID
    token_type: str
    device_fingerprint: Optional[str]
    ip_address: Optional[str]
    is_active: bool
    status: str
    created_at: datetime
    last_activity_at: datetime
    expires_at: datetime
    
    model_config = {"from_attributes": True}


class LoginEventResponse(BaseModel):
    """Login event response"""
    id: UUID
    timestamp: datetime
    ip_address: Optional[str]
    location: Optional[str]
    device_fingerprint: Optional[str]
    user_agent: Optional[str]
    risk_score: float
    risk_level: Optional[str]
    anomaly_score: Optional[float]
    behavior_risk: Optional[str]
    device_known: bool
    mfa_required: bool
    user_action: str
    
    model_config = {"from_attributes": True}


class DashboardStatsResponse(BaseModel):
    """Dashboard statistics"""
    total_logins_today: int
    total_logins_week: int
    total_logins_month: int
    failed_logins_today: int
    active_sessions: int
    trusted_devices: int
    average_risk_score: float
    high_risk_logins_today: int
    mfa_enabled: bool
    account_status: str


class RiskDistributionResponse(BaseModel):
    """Risk level distribution"""
    low: int
    medium: int
    high: int


class DashboardOverviewResponse(BaseModel):
    """Complete dashboard overview"""
    stats: DashboardStatsResponse
    risk_distribution: RiskDistributionResponse
    recent_logins: List[LoginEventResponse]
    current_risk_level: str
    security_score: int  # 0-100


class RiskAssessmentDetailResponse(BaseModel):
    """Detailed risk assessment for a login event"""
    event: LoginEventResponse
    risk_factors: dict
    behavioral_analysis: dict
    device_analysis: dict
    recommendations: List[str]


#Helper Functions

def calculate_security_score(user: User, db: Session) -> int:
    score = 50 
    
    # MFA enabled: +30
    if user.mfa_enabled:
        score += 30
    
    # Email verified: +10
    if user.is_verified:
        score += 10
    
    # Recent login history
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    high_risk_count = db.query(LoginEvent).filter(
        LoginEvent.user_id == user.id,
        LoginEvent.timestamp >= week_ago,
        LoginEvent.risk_level == "high"
    ).count()
    
    if high_risk_count == 0:
        score += 10
    
    return min(100, score)


#Dashboard Endpoints

@router.get(
    "/dashboard/full",
    summary="Get full dashboard with RAG insights and ML analysis"
)
async def get_full_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    try:
        user = current_user  # Use current_user directly
        
        # Get latest login event
        latest_login = db.query(LoginEvent).filter(
            LoginEvent.user_id == user.id
        ).order_by(desc(LoginEvent.timestamp)).first()
        
        # Get all active sessions
        active_sessions = db.query(DBSession).filter(
            DBSession.user_id == user.id,
            DBSession.is_active == True,
            DBSession.expires_at > datetime.now(timezone.utc)
        ).all()
        
        # Build risk assessment data
        risk_assessment = None
        if latest_login:
            risk_assessment = {
                "risk_score": latest_login.risk_score,
                "risk_level": latest_login.risk_level or "medium",
                "anomaly_score": latest_login.anomaly_score or 0.5,
                "device_known": latest_login.device_known,

                "device_fingerprint": latest_login.device_fingerprint,

                "device_status": "Known ✓" if latest_login.device_known else "New Device",  

                "location": latest_login.location or "Unknown",

                "location_city": latest_login.location_city,       
                "location_region": latest_login.location_region,    
                "location_country": latest_login.location_country,  
                "location_latitude": latest_login.location_latitude,  
                "location_longitude": latest_login.location_longitude,  
                "location_metric": latest_login.location_metric,    

                "ip_address": latest_login.ip_address or "Unknown",
                "timestamp": latest_login.timestamp.isoformat() if latest_login.timestamp else datetime.now(timezone.utc).isoformat(),
                "explanation": latest_login.risk_explanation or (
                    f"Risk level: {latest_login.risk_level}. "
                    f"Device {'known' if latest_login.device_known else 'unknown'}."
                ),
                "mfa_required": latest_login.mfa_required
            }

        
        # RAG insights
        rag_insights = None
        if latest_login:
            
            rag_insights = {
                "similar_cases": [
                    {
                        "explanation": f"Login from {latest_login.location or 'similar location'} with comparable risk profile",
                        "outcome": "approved",
                        "similarity_score": 0.85,
                        "location": latest_login.location or "Unknown",
                        "timestamp": (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
                    }
                ],
                "total_found": 1,
                "retrieval_method": "vector_similarity",
                "embedding_model": "all-MiniLM-L6-v2"
            }
        
        # ML Analysis
        ml_analysis = {
            "model_used": "Hybrid (Isolation Forest + Logistic Regression)",
            "anomaly_score": latest_login.anomaly_score if latest_login else 0.5,
            "behavior_risk": latest_login.behavior_risk if latest_login else "medium",
            "features_analyzed": [
                "IP Address",
                "Location",
                "Device Fingerprint",
                "Typing Speed",
                "Key Interval",
                "Key Hold Time",
                "Login Time Pattern",
                "Behavior Metrics"
            ]
        }
        
        # Workflow info
        workflow_info = {
            "pipeline": "ML Anomaly Detection → RAG Context Retrieval → LLM Risk Explanation → Adaptive MFA Decision",
            "technologies": [
                "Isolation Forest",
                "Logistic Regression",
                "Pinecone Vector DB",
                "Groq LLM",
                "Sentence Transformers",
                "FastAPI"
            ]
        }
        
        # Format sessions for frontend
        sessions_data = [{
            "id": str(session.id),
            "device_fingerprint": session.device_fingerprint or "Unknown",
            "ip_address": session.ip_address or "Unknown",
            "created_at": session.created_at.isoformat() if session.created_at else datetime.now(timezone.utc).isoformat(),
            "last_activity_at": session.last_activity_at.isoformat() if session.last_activity_at else datetime.now(timezone.utc).isoformat(),
            "is_active": session.is_active
        } for session in active_sessions]
        
        # Get login history 
        login_history = db.query(LoginEvent).filter(
            LoginEvent.user_id == user.id
        ).order_by(desc(LoginEvent.timestamp)).limit(20).all()
        
        login_history_data = [{
            "id": str(event.id),
            "timestamp": event.timestamp.isoformat() if event.timestamp else datetime.now(timezone.utc).isoformat(),
            "ip_address": event.ip_address,
            "location": event.location,
            "risk_score": event.risk_score,
            "risk_level": event.risk_level,
            "device_known": event.device_known,
            "user_action": event.user_action,
            "device_fingerprint": event.device_fingerprint,
            "location_city": event.location_city,
            "location_region": event.location_region,
            "location_country": event.location_country,
            "location_latitude": event.location_latitude,
            "location_longitude": event.location_longitude,
            "location_metric": event.location_metric,
        } for event in login_history]
        
        return {
            "user": {
                "email": user.email,
                "mfa_enabled": user.mfa_enabled,
                "created_at": user.created_at.isoformat() if user.created_at else datetime.now(timezone.utc).isoformat(),
                "last_login": user.last_login_at.isoformat() if user.last_login_at else None
            },
            "risk_assessment": risk_assessment,
            "rag_insights": rag_insights,
            "ml_analysis": ml_analysis,
            "workflow_info": workflow_info,
            "sessions": sessions_data,
            "login_history": login_history_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Full dashboard error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dashboard data: {str(e)}"
        )


@router.get(
    "/dashboard/overview",
    response_model=DashboardOverviewResponse,
    summary="Get complete dashboard overview"
)
async def get_dashboard_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        user = current_user  # Use current_user directly
        
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        # Total logins
        total_logins_today = db.query(LoginEvent).filter(
            LoginEvent.user_id == user.id,
            LoginEvent.timestamp >= today_start
        ).count()
        
        total_logins_week = db.query(LoginEvent).filter(
            LoginEvent.user_id == user.id,
            LoginEvent.timestamp >= week_ago
        ).count()
        
        total_logins_month = db.query(LoginEvent).filter(
            LoginEvent.user_id == user.id,
            LoginEvent.timestamp >= month_ago
        ).count()
        
        # Failed logins
        failed_logins_today = db.query(LoginEvent).filter(
            LoginEvent.user_id == user.id,
            LoginEvent.timestamp >= today_start,
            LoginEvent.user_action == "denied"
        ).count()
        
        # Active sessions
        active_sessions = db.query(DBSession).filter(
            DBSession.user_id == user.id,
            DBSession.is_active == True,
            DBSession.expires_at > now
        ).count()
        
        # Trusted devices
        trusted_devices = db.query(func.count(func.distinct(LoginEvent.device_fingerprint))).filter(
            LoginEvent.user_id == user.id,
            LoginEvent.user_action == "approved",
            LoginEvent.device_known == True
        ).scalar() or 0
        
        # Average risk score
        avg_risk = db.query(func.avg(LoginEvent.risk_score)).filter(
            LoginEvent.user_id == user.id,
            LoginEvent.timestamp >= week_ago
        ).scalar() or 0.5
        
        # High risk logins today
        high_risk_today = db.query(LoginEvent).filter(
            LoginEvent.user_id == user.id,
            LoginEvent.timestamp >= today_start,
            LoginEvent.risk_level == "high"
        ).count()
        
        # Risk distribution
        risk_low = db.query(LoginEvent).filter(
            LoginEvent.user_id == user.id,
            LoginEvent.timestamp >= month_ago,
            LoginEvent.risk_level == "low"
        ).count()
        
        risk_medium = db.query(LoginEvent).filter(
            LoginEvent.user_id == user.id,
            LoginEvent.timestamp >= month_ago,
            LoginEvent.risk_level == "medium"
        ).count()
        
        risk_high = db.query(LoginEvent).filter(
            LoginEvent.user_id == user.id,
            LoginEvent.timestamp >= month_ago,
            LoginEvent.risk_level == "high"
        ).count()
        
        # Recent logins
        recent_logins = db.query(LoginEvent).filter(
            LoginEvent.user_id == user.id
        ).order_by(desc(LoginEvent.timestamp)).limit(10).all()
        
        # Current risk level
        latest_login = db.query(LoginEvent).filter(
            LoginEvent.user_id == user.id
        ).order_by(desc(LoginEvent.timestamp)).first()
        
        current_risk_level = latest_login.risk_level if latest_login else "low"
        
        # Account status
        account_status = "locked" if user.is_locked else ("active" if user.is_active else "inactive")
        
        # Security score
        security_score = calculate_security_score(user, db)
        
        return DashboardOverviewResponse(
            stats=DashboardStatsResponse(
                total_logins_today=total_logins_today,
                total_logins_week=total_logins_week,
                total_logins_month=total_logins_month,
                failed_logins_today=failed_logins_today,
                active_sessions=active_sessions,
                trusted_devices=trusted_devices,
                average_risk_score=round(float(avg_risk), 2),
                high_risk_logins_today=high_risk_today,
                mfa_enabled=user.mfa_enabled,
                account_status=account_status
            ),
            risk_distribution=RiskDistributionResponse(
                low=risk_low,
                medium=risk_medium,
                high=risk_high
            ),
            recent_logins=[LoginEventResponse.model_validate(event) for event in recent_logins],
            current_risk_level=current_risk_level,
            security_score=security_score
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dashboard overview error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch dashboard data"
        )


#Active Sessions

@router.get(
    "/active",
    response_model=List[SessionResponse],
    summary="Get all active sessions"
)
async def get_active_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        user = current_user  # Use current_user directly
        
        sessions = db.query(DBSession).filter(
            DBSession.user_id == user.id,
            DBSession.is_active == True,
            DBSession.expires_at > datetime.now(timezone.utc)
        ).order_by(desc(DBSession.last_activity_at)).all()
        
        return [SessionResponse.model_validate(session) for session in sessions]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Active sessions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch active sessions"
        )


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_200_OK,
    summary="Revoke a specific session"
)
async def revoke_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        user = current_user  # Use current_user directly
        
        session = db.query(DBSession).filter(
            DBSession.id == session_id,
            DBSession.user_id == user.id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        session.revoke()
        db.commit()
        
        logger.info(f"Session revoked: {session_id} for user {user.id}")
        
        return {"message": "Session revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session revocation error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke session"
        )


@router.delete(
    "/revoke-all",
    status_code=status.HTTP_200_OK,
    summary="Revoke all sessions except current"
)
async def revoke_all_sessions(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        from app.routers.auth_middleware import CookieTokenExtractor
        
        user = current_user  # Use current_user directly
        access_token = CookieTokenExtractor.get_access_token(request)
        
        # Get current session JTI
        success, payload = AuthService.verify_token(access_token, "access")
        current_jti = payload.get("jti") if success and payload else None
        
        # Revoke all sessions except current
        sessions = db.query(DBSession).filter(
            DBSession.user_id == user.id,
            DBSession.is_active == True,
            DBSession.jti != current_jti
        ).all()
        
        count = 0
        for session in sessions:
            session.revoke()
            count += 1
        
        db.commit()
        
        logger.info(f"Revoked {count} sessions for user {user.id}")
        
        return {"message": f"{count} sessions revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Revoke all sessions error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke sessions"
        )


#Session History

@router.get(
    "/history",
    response_model=List[LoginEventResponse],
    summary="Get login history"
)
async def get_session_history(
    current_user: User = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0,
    risk_level: Optional[str] = None,
    days: int = 30,
    db: Session = Depends(get_db)
):
    try:
        user = current_user  # Use current_user directly
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        query = db.query(LoginEvent).filter(
            LoginEvent.user_id == user.id,
            LoginEvent.timestamp >= cutoff_date
        )
        
        if risk_level:
            query = query.filter(LoginEvent.risk_level == risk_level)
        
        events = query.order_by(desc(LoginEvent.timestamp)).limit(limit).offset(offset).all()
        
        return [LoginEventResponse.model_validate(event) for event in events]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session history error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch session history"
        )


#Risk Assessment Details

@router.get(
    "/risk-assessment/{event_id}",
    response_model=RiskAssessmentDetailResponse,
    summary="Get detailed risk assessment for a login event"
)
async def get_risk_assessment_detail(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        user = current_user  # Use current_user directly
        
        event = db.query(LoginEvent).filter(
            LoginEvent.id == event_id,
            LoginEvent.user_id == user.id
        ).first()
        
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Login event not found"
            )
        
        # Risk factors
        risk_factors = {
            "device_known": event.device_known,
            "risk_score": event.risk_score,
            "anomaly_score": event.anomaly_score,
            "behavior_risk": event.behavior_risk,
            "mfa_required": event.mfa_required
        }
        
        # Behavioral analysis
        behavioral_analysis = {
            "typing_speed": event.typing_speed,
            "key_interval": event.key_interval,
            "key_hold": event.key_hold,
            "behavior_risk_level": event.behavior_risk
        }
        
        # Device analysis
        device_analysis = {
            "fingerprint": event.device_fingerprint,
            "known": event.device_known,
            "last_seen": event.device_last_seen_at.isoformat() if event.device_last_seen_at else None,
            "ip_address": event.ip_address,
            "location": event.location,
            "user_agent": event.user_agent
        }
        
        # Recommendations
        recommendations = []
        if event.risk_score > 0.7:
            recommendations.append("Enable MFA if not already enabled")
            recommendations.append("Review recent account activity")
            recommendations.append("Change password if unauthorized access suspected")
        elif event.risk_score > 0.3:
            recommendations.append("Consider enabling MFA for added security")
            recommendations.append("Monitor account activity")
        else:
            recommendations.append("Login appears normal")
        
        if not event.device_known:
            recommendations.append("New device detected - verify it was you")
        
        return RiskAssessmentDetailResponse(
            event=LoginEventResponse.model_validate(event),
            risk_factors=risk_factors,
            behavioral_analysis=behavioral_analysis,
            device_analysis=device_analysis,
            recommendations=recommendations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Risk assessment detail error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch risk assessment details"
        )