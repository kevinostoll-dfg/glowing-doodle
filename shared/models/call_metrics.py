"""CallMetrics model for daily aggregated metrics."""

from sqlalchemy import Column, Date, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from shared.database import Base


class CallMetrics(Base):
    __tablename__ = "call_metrics"

    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    date = Column(Date, nullable=False)
    total_calls = Column(Integer, default=0)
    inbound_calls = Column(Integer, default=0)
    outbound_calls = Column(Integer, default=0)
    missed_calls = Column(Integer, default=0)
    ai_handled_calls = Column(Integer, default=0)
    avg_duration = Column(Float, default=0.0)
    avg_score = Column(Float)
    sentiment_distribution = Column(JSONB, default=dict)
    lead_source_breakdown = Column(JSONB, default=dict)

    shop = relationship("Shop", back_populates="metrics")
