from app.models.user import User 
from app.models.login_event import LoginEvent, LoginOutcome
from app.models.session import Session

from app.models.schemas import (
    UserResponse,
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    MFAVerifyRequest,
    MFAVerifyResponse,
    ConfirmMFASetupRequest,
    ConfirmMFASetupResponse,
    RegenerateMFARequest,
    RegenerateMFAResponse,
    LogoutRequest,
    LogoutResponse,
    ErrorResponse,
    RiskAssessmentRequest,
    RiskAssessmentResponse,
    BehavioralMetricsRequest,
    BehavioralMetricsResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse
)
from sqlalchemy.orm import declarative_base
Base = declarative_base()

__all__ = [
    "User",  
    "LoginEvent",
    "LoginOutcome",
    "Session",
    "UserResponse",
    "RegisterRequest",
    "RegisterResponse",
    "LoginRequest",
    "LoginResponse",
    "MFAVerifyRequest",
    "MFAVerifyResponse",
    "ConfirmMFASetupRequest",
    "ConfirmMFASetupResponse",
    "RegenerateMFARequest",
    "RegenerateMFAResponse",
    "LogoutRequest",
    "LogoutResponse",
    "ErrorResponse",
    "RiskAssessmentRequest",
    "RiskAssessmentResponse",
    "BehavioralMetricsRequest",
    "BehavioralMetricsResponse",
    "ForgotPasswordRequest",
    "ForgotPasswordResponse",
    "ResetPasswordRequest",
    "ResetPasswordResponse"

]

__all__=["Base","User","Session"]