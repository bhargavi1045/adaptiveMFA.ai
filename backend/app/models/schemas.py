from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional, Literal
from datetime import datetime, timezone
from uuid import UUID


# User models
class UserResponse(BaseModel):
    """User data in responses"""
    id: UUID
    email: EmailStr
    is_active: bool
    is_verified: bool
    mfa_enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# Auth model
class RegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    password_confirm: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)
        
        if not (has_upper and has_lower and has_digit and has_special):
            raise ValueError(
                "Password must contain uppercase, lowercase, digit, and special character"
            )
        return v

    @field_validator("password_confirm")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        """Ensure passwords match"""
        if info.data.get("password") and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v


class RegisterResponse(BaseModel):
    """Registration response with MFA setup data"""
    message: str
    user: UserResponse
    qr_code_uri: str
    backup_codes: List[str]
    setup_token: str


class LoginRequest(BaseModel):
    """Login request"""
    email: str
    password: str
    ip_address: str
    user_agent: str = "unknown"
    device_fingerprint: str = "unknown"
    location: str | None = None
    typing_speed: float = 0.0
    key_interval: float = 0.0
    key_hold: float = 0.0

    location_latitude: Optional[float] = None
    location_longitude: Optional[float] = None
    location_city: Optional[str] = None
    location_region: Optional[str] = None
    location_country: Optional[str] = None


class LoginResponse(BaseModel):
    """Login response"""
    message: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    mfa_token: Optional[str] = None
    token_type: Literal["bearer"] = "bearer"
    user: UserResponse
    mfa_required: bool = False
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    instructions: Optional[str] = None
    device_known: Optional[bool] = None
    login_event_id:Optional[str]=None

    model_config = {"from_attributes": True}


class MFAVerifyRequest(BaseModel):
    """MFA verification request"""
    mfa_token: str
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")
    login_event_id : Optional[str]=None


class MFAVerifyResponse(BaseModel):
    """MFA verification response"""
    message: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: Literal["bearer"] = "bearer"
    user: Optional[UserResponse] = None


class ConfirmMFASetupRequest(BaseModel):
    """Confirm MFA setup request"""
    setup_token: str
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class ConfirmMFASetupResponse(BaseModel):
    """MFA setup confirmation response"""
    message: str
    user_id: UUID
    email: EmailStr


class RegenerateMFARequest(BaseModel):
    """Regenerate MFA setup token request"""
    email: EmailStr
    password: str = Field(..., min_length=1)


class RegenerateMFAResponse(BaseModel):
    """Regenerate MFA response"""
    message: str
    setup_token: str


class LogoutRequest(BaseModel):
    pass


class LogoutResponse(BaseModel):
    """Logout response"""
    message: str


# Error models

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


# Risk assessment models

class RiskAssessmentRequest(BaseModel):
    """Risk assessment request"""
    user_id: str
    ip_address: str
    location: str
    device_info: str
    device_fingerprint: Optional[str] = None
    user_agent: Optional[str] = None
    typing_speed: Optional[float] = None
    key_interval: Optional[float] = None
    key_hold: Optional[float] = None
    device_id: Optional[str] = None
    device_seen_before: Optional[bool] = False
    location_changed: Optional[bool] = False
    ip_reputation: Optional[float] = 0.5
    location_latitude: Optional[float] = None
    location_longitude: Optional[float] = None
    location_city: Optional[str] = None
    location_region: Optional[str] = None
    location_country: Optional[str] = None
    location_metric: Optional[float] = None


class RiskAssessmentResponse(BaseModel):
    """Risk assessment response from login"""
    risk_score: float = Field(..., ge=0.0, le=1.0)
    risk_level: Literal["low", "medium", "high"]
    explanation: str
    device_fingerprint: Optional[str] = None
    device_known: bool = False
    behavior_risk: Optional[str] = None
    mfa_methods_required: List[str] = []
    mfa_required: bool = False
    mfa_strength: Optional[str] = None
    similar_cases: List[dict] = []
    action_required: bool = False
    recommendation: Optional[str] = None
    anomaly_score: Optional[float] = None
    blocked: bool = False
    block_reason: Optional[str] = None


# Behavioural metrics modal

class BehavioralMetricsRequest(BaseModel):
    """Behavioral metrics for login"""
    typing_speed: float = Field(..., ge=0.0)
    key_interval: float = Field(..., ge=0.0)
    key_hold: float = Field(..., ge=0.0)


class BehavioralMetricsResponse(BaseModel):
    """Behavioral metrics response"""
    baseline_typing_speed: Optional[float] = None
    baseline_key_interval: Optional[float] = None
    baseline_key_hold: Optional[float] = None
    typing_speed_deviation: Optional[float] = None
    key_interval_deviation: Optional[float] = None
    key_hold_deviation: Optional[float] = None
    risk_level: Literal["low", "medium", "high"] = "medium"

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class ForgotPasswordResponse(BaseModel):
    message: str

class ResetPasswordResponse(BaseModel):
    message: str