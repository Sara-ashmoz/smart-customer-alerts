from sqlalchemy.orm import Session
from models import Alert, CustomerRiskSnapshot

#SAVE / UPSERT
def create_alert_from_snapshot(
    db: Session,
    customer_id: int,
    message: str,
) -> Alert:
    snap = db.query(CustomerRiskSnapshot)\
             .filter(CustomerRiskSnapshot.customer_id == customer_id)\
             .first()

    if not snap:
        raise ValueError("No risk snapshot found for this customer. Refresh risk first.")

    alert = Alert(
        customer_id=customer_id,
        customer_name=snap.customer_name,
        message=message,
        status="sent",
    )

    db.add(alert)
    db.commit()
    return alert

#GET
def get_alerts(db: Session, limit: int = 200):
    return db.query(Alert)\
             .order_by(Alert.timestamp.desc())\
             .limit(limit)\
             .all()

def get_alert_by_id(db: Session, alert_id: int) -> Alert | None:
    return db.query(Alert).filter(Alert.id == alert_id).first()

# UPDATE
def update_alert(
    db: Session,
    alert_id: int,
    *,
    message: str | None = None,
    status: str | None = None,
) -> Alert:
    alert = get_alert_by_id(db, alert_id)
    if not alert:
        raise ValueError("Alert not found")

    if message is not None:
        alert.message = message

    if status is not None:
        alert.status = status

    db.commit()
    return alert

# DELETE
def delete_alert(db: Session, alert_id: int) -> bool:
    alert = get_alert_by_id(db, alert_id)
    if not alert:
        return False

    db.delete(alert)
    db.commit()
    return True

