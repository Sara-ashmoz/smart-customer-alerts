from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.sql import func
from db import Base

class CustomerRiskSnapshot(Base):
    __tablename__ = "customer_risk_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, index=True, nullable=False, unique=True)  # latest snapshot per customer
    customer_name = Column(String, nullable=False)

    unpaid_count = Column(Integer, nullable=False, default=0)
    total_open_debt = Column(Float, nullable=False, default=0.0)
    has_overdue = Column(Boolean, nullable=False, default=False)
    risk_score = Column(Float, nullable=False, default=0.0)
    risk_level = Column(String, nullable=False, default="Low")

    reasons = Column(Text, nullable=False, default="[]")  # store as JSON string



class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, index=True, nullable=False)
    customer_name = Column(String, nullable=False)
    message = Column(String, nullable=False)
    status = Column(String, default="sent", nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
