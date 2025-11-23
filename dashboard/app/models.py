from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from .db import Base
import datetime

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    source_ip = Column(String, index=True)
    service = Column(String)
    path = Column(String, nullable=True)
    payload = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    risk_score = Column(Float, default=0.0)
