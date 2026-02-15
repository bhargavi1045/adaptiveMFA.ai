from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models import RiskAssessmentResponse
from app.models.user import User
from app.models.login_event import LoginEvent
from app.services.auth_service import AuthService
from app.services.risk_service import RiskAssessmentService
from app.utils.logger import logger
from typing import Optional

router = APIRouter(prefix="/risk", tags=["Risk Assessment"])

# Service instance
risk_service = RiskAssessmentService()


def get_current_user(authorization: Optional[str], db: Session) -> User:
   
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authorization header"
        )
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
    
    user = AuthService.get_current_user(parts[1], db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return user


@router.get("/history")
async def get_risk_history(
    limit: int = 10,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    logger.info("Fetching risk history")
    
    try:
        user = get_current_user(authorization, db)
        
        # Get history
        history = db.query(LoginEvent).filter(
            LoginEvent.user_id == user.id
        ).order_by(LoginEvent.timestamp.desc()).limit(limit).all()
        
        return {
            "user_id": str(user.id),
            "total_logins": len(history),
            "history": [
                {
                    "id": str(login.id),
                    "ip_address": login.ip_address,
                    "location": login.location,
                    "timestamp": login.timestamp.isoformat(),
                    "risk_score": login.risk_score,
                    "is_anomalous": login.is_anomalous,
                    "user_action": login.user_action,
                }
                for login in history
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching history"
        )


@router.get("/stats")
async def get_risk_stats(db: Session = Depends(get_db)):
    
    logger.info("Fetching risk statistics")
    
    try:
        total_assessments = db.query(LoginEvent).count()
        anomalies_detected = db.query(LoginEvent).filter(
            LoginEvent.is_anomalous == True
        ).count()
        
        avg_risk_score = 0.0
        if total_assessments > 0:
            result = db.query(LoginEvent).with_entities(
                db.func.avg(LoginEvent.risk_score)
            ).scalar()
            avg_risk_score = float(result) if result else 0.0
        
        return {
            "total_assessments": total_assessments,
            "anomalies_detected": anomalies_detected,
            "average_risk_score": avg_risk_score,
            "anomaly_detection_rate": (anomalies_detected / total_assessments * 100) if total_assessments > 0 else 0,
        }
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching statistics"
        )


@router.post("/feedback")
async def submit_feedback(
    login_id: str,
    action: str,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
   
    logger.info(f"Feedback submitted for login: {login_id}")
    
    try:
        user = get_current_user(authorization, db)
        
        # Validate action
        if action not in ["approved", "blocked", "compromised"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid action"
            )
        
        # Get login event
        login_event = db.query(LoginEvent).filter(
            LoginEvent.id == login_id,
            LoginEvent.user_id == user.id
        ).first()
        
        if not login_event:
            raise HTTPException(status_code=404, detail="Login not found")
        
        # Update with user feedback
        login_event.user_action = action
        db.commit()
        
        logger.info(f"Feedback recorded: {login_id} -> {action}")
        
        return {
            "message": "Feedback recorded successfully",
            "login_id": login_id,
            "action": action
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error submitting feedback"
        )