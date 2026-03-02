"""CallParticipant model."""

from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from shared.database import Base


class CallParticipant(Base):
    __tablename__ = "call_participants"

    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(Integer, ForeignKey("calls.id"), nullable=False)
    speaker_label = Column(String(50))
    role = Column(String(20))  # advisor, customer
    utterances = Column(JSONB, default=list)
    total_talk_time_seconds = Column(Float, default=0.0)

    call = relationship("Call", back_populates="participants")
