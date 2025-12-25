from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func

from shared.database.connection import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    user_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    location = Column(String(100), nullable=True)
    website = Column(String(200), nullable=True)
    github_url = Column(String(200), nullable=True)
    linkedin_url = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id = Column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    user_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    theme = Column(String(20), default="light")
    language = Column(String(10), default="en")
    timezone = Column(String(50), default="UTC")
    email_notifications = Column(Boolean, default=True)
    privacy_level = Column(String(20), default="private")
    two_factor_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
