"""Call model."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from shared.database import Base


class Call(Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    twilio_call_sid = Column(String(64), unique=True, index=True)
    direction = Column(String(10), nullable=False)  # inbound, outbound
    status = Column(String(20), default="initiated")  # initiated, ringing, in-progress, completed, missed, voicemail
    from_number = Column(String(20))
    to_number = Column(String(20))
    caller_name = Column(String(255))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration_seconds = Column(Integer)
    recording_url = Column(Text)
    transcript = Column(Text)
    transcript_status = Column(String(20), default="pending")  # pending, processing, completed, failed
    ai_score = Column(Float)
    sentiment = Column(String(20))  # positive, neutral, negative
    caller_intent = Column(String(100))
    key_points = Column(JSONB, default=list)
    coaching_notes = Column(Text)
    analysis_status = Column(String(20), default="pending")  # pending, processing, completed, failed
    is_new_customer = Column(String(10))  # yes, no, unknown
    handled_by = Column(String(20))  # human, ai
    ai_agent_language = Column(String(10))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    shop = relationship("Shop", back_populates="calls")
    participants = relationship("CallParticipant", back_populates="call")

    __table_args__ = (
        Index("ix_calls_shop_id_start_time", "shop_id", "start_time"),
        Index("ix_calls_status", "status"),
        Index("ix_calls_direction", "direction"),
    )
