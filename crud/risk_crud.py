from sqlalchemy.orm import Session
from models import CustomerRiskSnapshot

#SAVE / UPSERT
def upsert_customer_risk_snapshot(db: Session, data: dict) -> CustomerRiskSnapshot:
    """
    data keys:
    customer_id, customer_name, unpaid_count, total_open_debt,
    has_overdue, risk_score, risk_level, reasons (list[str] or str)
    """

    existing = db.query(CustomerRiskSnapshot)\
                 .filter(CustomerRiskSnapshot.customer_id == data["customer_id"])\
                 .first()

    # נהפוך reasons לרצף טקסט פשוט
    reasons_text = data.get("reasons", [])
    if isinstance(reasons_text, list):
        reasons_text = "; ".join(reasons_text)

    if existing:
        existing.customer_name = data["customer_name"]
        existing.unpaid_count = data["unpaid_count"]
        existing.total_open_debt = float(data["total_open_debt"])
        existing.has_overdue = bool(data["has_overdue"])
        existing.risk_score = float(data["risk_score"])
        existing.risk_level = data["risk_level"]
        existing.reasons = reasons_text

        db.commit()
        db.refresh(existing)
        return existing

    snap = CustomerRiskSnapshot(
        customer_id=data["customer_id"],
        customer_name=data["customer_name"],
        unpaid_count=data["unpaid_count"],
        total_open_debt=float(data["total_open_debt"]),
        has_overdue=bool(data["has_overdue"]),
        risk_score=float(data["risk_score"]),
        risk_level=data["risk_level"],
        reasons=reasons_text,
    )

    db.add(snap)
    db.commit()
    return snap

#GET
def get_customer_risk(db: Session, customer_id: int) -> CustomerRiskSnapshot | None:
    return db.query(CustomerRiskSnapshot).filter(CustomerRiskSnapshot.customer_id == customer_id).first()

def list_customer_risks(db: Session):
    return db.query(CustomerRiskSnapshot).order_by(CustomerRiskSnapshot.risk_score.desc()).all()


# DELETE
def delete_customer_risk(db: Session, customer_id: int) -> bool:
    obj = get_customer_risk(db, customer_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True

