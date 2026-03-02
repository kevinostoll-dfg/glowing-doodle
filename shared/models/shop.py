"""Shop model."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from shared.database import Base


class Shop(Base):
    __tablename__ = "shops"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    shop_code = Column(String(50), unique=True, nullable=False, index=True)
    phone_number = Column(String(20))
    timezone = Column(String(50), default="America/New_York")
    business_hours = Column(JSONB, default=dict)
    address = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    users = relationship("User", back_populates="shop")
    calls = relationship("Call", back_populates="shop")
    phone_numbers = relationship("PhoneNumber", back_populates="shop")
    metrics = relationship("CallMetrics", back_populates="shop")
