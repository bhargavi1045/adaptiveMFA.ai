from sqlalchemy import Column, DateTime, Boolean, ForeignKey, String, Index, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from uuid import uuid4
from app.database.base import Base
import enum

class SessionStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    INVALIDATED = "invalidated"

class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    jti = Column(String(64), unique=True, nullable=False, index=True)
    token_type = Column(
        String(20),
        default="access",
        nullable=False,
        index=True
    )

    is_active = Column(Boolean, default=True, nullable=False, index=True)
    status = Column(
        Enum(SessionStatus, name="session_status_enum"),
        default=SessionStatus.ACTIVE,
        nullable=False,
        index=True
    )

    device_fingerprint = Column(String(255), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    last_activity_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    user = relationship("User", back_populates="sessions", foreign_keys=[user_id])

    __table_args__ = (
        Index("idx_user_active_sessions", user_id, is_active),
        Index("idx_expired_sessions", expires_at),
        Index("idx_jti_active", jti, is_active),
    )

    def __repr__(self):
        return (
            f"<Session(id={self.id}, user_id={self.user_id}, "
            f"token_type={self.token_type}, is_active={self.is_active})>"
        )

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    def is_valid(self) -> bool:
        return (
            self.is_active and 
            not self.is_expired() and 
            self.status == SessionStatus.ACTIVE
        )

    def revoke(self):
        self.is_active = False
        self.status = SessionStatus.REVOKED
        self.revoked_at = datetime.now(timezone.utc)

    def invalidate(self):
        self.is_active = False
        self.status = SessionStatus.INVALIDATED
        self.revoked_at = datetime.now(timezone.utc)

    def refresh_activity(self):
        self.last_activity_at = datetime.now(timezone.utc)