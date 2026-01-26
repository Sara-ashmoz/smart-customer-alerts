from pydantic import BaseModel
from typing import List, Literal

RiskLevel = Literal["Low", "Medium", "High"]

class CustomerRiskOut(BaseModel):
    customer_id: int
    customer_name: str
    unpaid_count: int
    total_open_debt: float
    has_overdue: bool
    risk_score: float
    risk_level: RiskLevel
    reasons: List[str]
