from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
import json

from app.database.connection import get_db
from app.models.user import User
from app.services.auth_service import AuthService
from app.utils.logger import logger

router = APIRouter(prefix="/api/user", tags=["User Settings"])


#Request/Reponse Models

class UserSettingsResponse(BaseModel):
    """User settings response"""
    id: UUID
    email: EmailStr
    is_active: bool
    is_verified: bool
    mfa_enabled: bool
    created_at: datetime
    last_login_at: Optional[datetime]
    failed_login_attempts: int
    is_locked: bool
    
    # Behavioral profile
    has_behavior_profile: bool
    behavior_samples: int
    
    # Trust
    trusted_devices_count: int
    
    model_config = {"from_attributes": True}


class UpdatePasswordRequest(BaseModel):
    """Change password request"""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)
    new_password_confirm: str = Field(..., min_length=8, max_length=128)


class DisableMFARequest(BaseModel):
    """Disable MFA request"""
    password: str = Field(..., min_length=1)
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class TrustedDevice(BaseModel):
    """Trusted device info"""
    device_fingerprint: str
    last_seen: datetime
    login_count: int
    locations: List[str]

class DeleteAccountRequest(BaseModel):
    password: str = Field(..., min_length=1)


#Helper function

def get_current_user_from_token(authorization: str, db: Session) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
    
    token = authorization.split(" ", 1)[1]
    user = AuthService.get_current_user(token, db)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return user


#Setting endpoints

@router.get(
    "/settings",
    response_model=UserSettingsResponse,
    summary="Get user settings"
)
async def get_user_settings(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    
    try:
        user = get_current_user_from_token(authorization, db)
        
        # Parse behavior profile
        has_behavior_profile = bool(user.behavior_profile)
        behavior_samples = 0
        if user.behavior_profile:
            try:
                profile = json.loads(user.behavior_profile)
                behavior_samples = profile.get("samples", 0)
            except:
                pass
        
        response = UserSettingsResponse(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            is_verified=user.is_verified,
            mfa_enabled=user.mfa_enabled,
            created_at=user.created_at,
            last_login_at=user.last_login_at,
            failed_login_attempts=int(user.failed_login_attempts),
            is_locked=user.is_locked,
            has_behavior_profile=has_behavior_profile,
            behavior_samples=behavior_samples,
            trusted_devices_count=int(user.trusted_devices_count)
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get settings error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user settings"
        )


@router.put(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change password"
)
async def change_password(
    request: UpdatePasswordRequest,
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    try:
        user = get_current_user_from_token(authorization, db)
        
        # Verify current password
        if not AuthService.verify_password(request.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )
        
        # Verify new passwords match
        if request.new_password != request.new_password_confirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New passwords do not match"
            )
        
        # Verify new password is different
        if request.current_password == request.new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from current password"
            )
        
        # Update password
        user.password_hash = AuthService.hash_password(request.new_password)
        db.commit()
        
        logger.info(f"Password changed for user {user.email}")
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Change password error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.post(
    "/disable-mfa",
    status_code=status.HTTP_200_OK,
    summary="Disable MFA"
)
async def disable_mfa(
    request: DisableMFARequest,
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    try:
        user = get_current_user_from_token(authorization, db)
        
        if not user.mfa_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA is not enabled"
            )
        
        # Verify password
        if not AuthService.verify_password(request.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password"
            )
        
        # Verify MFA code
        if not AuthService.verify_mfa_code(user.mfa_secret, request.code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid MFA code"
            )
        
        # Disable MFA
        user.mfa_enabled = False
        db.commit()
        
        logger.info(f"MFA disabled for user {user.email}")
        
        return {"message": "MFA disabled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Disable MFA error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable MFA"
        )


@router.get(
    "/trusted-devices",
    response_model=List[TrustedDevice],
    summary="Get trusted devices"
)
async def get_trusted_devices(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    try:
        user = get_current_user_from_token(authorization, db)
        
        from app.models.login_event import LoginEvent
        from sqlalchemy import func, desc
        
        # Get all approved logins grouped by device fingerprint
        devices = db.query(
            LoginEvent.device_fingerprint,
            func.max(LoginEvent.timestamp).label('last_seen'),
            func.count(LoginEvent.id).label('login_count'),
            func.array_agg(func.distinct(LoginEvent.location)).label('locations')
        ).filter(
            LoginEvent.user_id == user.id,
            LoginEvent.user_action == "approved",
            LoginEvent.device_known == True,
            LoginEvent.device_fingerprint.isnot(None)
        ).group_by(
            LoginEvent.device_fingerprint
        ).order_by(desc('last_seen')).all()
        
        trusted_devices = []
        for device in devices:
            # Filter out None locations
            locations = [loc for loc in (device.locations or []) if loc]
            
            trusted_devices.append(TrustedDevice(
                device_fingerprint=device.device_fingerprint,
                last_seen=device.last_seen,
                login_count=device.login_count,
                locations=locations if locations else ["Unknown"]
            ))
        
        return trusted_devices
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get trusted devices error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch trusted devices"
        )


@router.delete(
    "/trusted-devices/{device_fingerprint}",
    status_code=status.HTTP_200_OK,
    summary="Remove trusted device"
)
async def remove_trusted_device(
    device_fingerprint: str,
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """Remove a device from trusted devices list"""
    try:
        user = get_current_user_from_token(authorization, db)
        
        from app.models.login_event import LoginEvent
        
        # Update all login events for this device to mark as not known
        updated = db.query(LoginEvent).filter(
            LoginEvent.user_id == user.id,
            LoginEvent.device_fingerprint == device_fingerprint
        ).update({"device_known": False})
        
        db.commit()
        
        logger.info(f"Device {device_fingerprint} removed from trusted devices for user {user.email}")
        
        return {"message": f"Device removed from trusted devices (affected {updated} login records)"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Remove trusted device error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove trusted device"
        )


@router.delete(
    "/account",
    status_code=status.HTTP_200_OK,
    summary="Delete account"
)
async def delete_account(
    payload: DeleteAccountRequest,
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """Soft delete user account (requires password confirmation)"""
    try:
        user = get_current_user_from_token(authorization, db)
        
        # Verify password
        if not AuthService.verify_password(payload.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password"
            )
        
        # Soft delete
        user.deleted_at = datetime.now(datetime.timezone.utc)
        user.is_active = False
        
        # Revoke all sessions
        from app.models.session import Session as DBSession
        db.query(DBSession).filter(
            DBSession.user_id == user.id,
            DBSession.is_active == True
        ).update({"is_active": False})
        
        db.commit()
        
        logger.info(f"Account deleted for user {user.email}")
        
        return {"message": "Account deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete account error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account"
        )