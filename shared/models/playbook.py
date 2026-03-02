"""Playbook model for call scoring rubrics."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from shared.database import Base


class Playbook(Base):
    __tablename__ = "playbooks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    criteria = Column(JSONB, default=list)
    script_template = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
