from datetime import datetime, timezone
from uuid import uuid4
import enum
from sqlalchemy import Column, String, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError
from app.database.connection import SessionLocal
from app.database.base import Base

class LoginOutcome(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    MFA_REQUIRED = "mfa_required"

class LoginEvent(Base):
    __tablename__ = "login_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    device_fingerprint = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    location = Column(String, nullable=True)
    risk_score = Column(Float, default=0.5)
    risk_level = Column(String, default="medium")
    anomaly_score = Column(Float, default=0.5)
    behavior_risk = Column(String, default="medium")
    device_known = Column(Boolean, default=False)
    device_last_seen_at = Column(DateTime(timezone=True), nullable=True)
    typing_speed = Column(Float, nullable=True)
    key_interval = Column(Float, nullable=True)
    key_hold = Column(Float, nullable=True)
    is_anomalous = Column(Boolean, default=False)
    mfa_required = Column(Boolean, default=False)
    user_action = Column(String, default=LoginOutcome.PENDING.value)
    risk_explanation = Column(String, nullable=True)
    location_city = Column(String, nullable=True)
    location_region = Column(String, nullable=True)
    location_country = Column(String, nullable=True)
    location_latitude = Column(Float, nullable=True)
    location_longitude = Column(Float, nullable=True)
    location_metric = Column(Float, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="login_events")

def create_login_event(**kwargs) -> LoginEvent:
    session = SessionLocal()
    try:
        login_event = LoginEvent(id=uuid4(), **kwargs)
        session.add(login_event)
        session.commit()
        session.refresh(login_event)
        return login_event
    except SQLAlchemyError as e:
        session.rollback()
        raise e
    finally:
        session.close()