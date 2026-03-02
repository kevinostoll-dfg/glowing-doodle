"""PhoneNumber model."""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from shared.database import Base


class PhoneNumber(Base):
    __tablename__ = "phone_numbers"

    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    phone_number = Column(String(20), unique=True, nullable=False)
    number_type = Column(String(20), default="main")  # main, tracking, toll-free
    lead_source = Column(String(100))
    is_active = Column(Boolean, default=True)

    shop = relationship("Shop", back_populates="phone_numbers")
