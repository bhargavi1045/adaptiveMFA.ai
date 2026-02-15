from sqlalchemy import Column, String, DateTime, Boolean, Text, Float, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from uuid import uuid4
from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    
    # Core authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_verified = Column(Boolean, default=False, nullable=False, index=True)
    last_login_at = Column(DateTime, nullable=True)
    
    # TOTP-based MFA
    mfa_enabled = Column(Boolean, default=False, nullable=False, index=True)
    mfa_secret = Column(String(255), nullable=True) 
    backup_codes = Column(Text, nullable=True)  
    
    behavior_profile = Column(Text, nullable=True) 
    
    # Device trust 
    last_trusted_device_fingerprint = Column(String(255), nullable=True)
    trusted_devices_count = Column(Float, default=0, nullable=False)
    
    # Risk assessment flags
    is_locked = Column(Boolean, default=False, nullable=False, index=True)
    lock_reason = Column(String(255), nullable=True)
    failed_login_attempts = Column(Float, default=0, nullable=False)
    last_failed_login_at = Column(DateTime, nullable=True)
    
    # Timestamps 
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)  
    
    # Relationships
    login_events = relationship(
        "LoginEvent",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="LoginEvent.user_id"
    )
    sessions = relationship(
        "Session",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="Session.user_id"
    )

    # Indexes
    __table_args__ = (
        Index("idx_user_email_active", email, is_active),
        Index("idx_user_locked", is_locked, id),
    )

    def __repr__(self):
        return (
            f"<User(id={self.id}, email={self.email}, "
            f"mfa_enabled={self.mfa_enabled}, is_verified={self.is_verified})>"
        )
    
    def is_soft_deleted(self) -> bool:
        """Check if user is soft-deleted"""
        return self.deleted_at is not None
    
    def has_active_sessions(self) -> bool:
        """Check if user has active sessions"""
        return any(session.is_active for session in self.sessions)
    
    def unlock(self):
        """Unlock account after security review"""
        self.is_locked = False
        self.lock_reason = None
        self.failed_login_attempts = 0