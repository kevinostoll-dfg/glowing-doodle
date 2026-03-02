"""User model."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from shared.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    api_key = Column(String(255), nullable=False, index=True)
    role = Column(String(20), default="viewer")  # admin, manager, viewer
    created_at = Column(DateTime, default=datetime.utcnow)

    shop = relationship("Shop", back_populates="users")
