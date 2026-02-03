import pytest

pytestmark = pytest.mark.integration


def test_risk_snapshot_upsert_updates_existing_row():
    from db import Base, engine, SessionLocal
    from crud import risk_crud
    from models import CustomerRiskSnapshot

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    # Insert 1st time
    risk_crud.upsert_customer_risk_snapshot(db, {
        "customer_id": 1,
        "customer_name": "Beta Corp",
        "unpaid_count": 2,
        "total_open_debt": 2000.0,
        "has_overdue": True,
        "risk_score": 80.0,
        "risk_level": "High",
        "reasons": ["Has at least one overdue invoice (+50)"],
    })

    # Upsert again with changed values
    risk_crud.upsert_customer_risk_snapshot(db, {
        "customer_id": 1,
        "customer_name": "Beta Corp",
        "unpaid_count": 5,
        "total_open_debt": 5000.0,
        "has_overdue": True,
        "risk_score": 95.0,
        "risk_level": "High",
        "reasons": ["Updated reasons"],
    })

    rows = db.query(CustomerRiskSnapshot).filter(CustomerRiskSnapshot.customer_id == 1).all()
    assert len(rows) == 1, "Upsert should not create duplicates"

    snap = rows[0]
    assert snap.unpaid_count == 5
    assert float(snap.total_open_debt) == 5000.0
    assert float(snap.risk_score) == 95.0
    db.close()


def test_create_alert_from_snapshot_pulls_customer_name_and_saves_alert():
    from db import Base, engine, SessionLocal
    from crud import alerts_crud, risk_crud
    from models import Alert

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    # Ensure snapshot exists
    risk_crud.upsert_customer_risk_snapshot(db, {
        "customer_id": 1,
        "customer_name": "Beta Corp",
        "unpaid_count": 2,
        "total_open_debt": 2150.0,
        "has_overdue": True,
        "risk_score": 80.0,
        "risk_level": "High",
        "reasons": ["Has at least one overdue invoice (+50)"],
    })

    alert = alerts_crud.create_alert_from_snapshot(
        db=db,
        customer_id=1,
        message="Dear Beta Corp, your invoice is overdue.",
    )

    assert alert.id is not None
    assert alert.customer_id == 1
    assert alert.customer_name == "Beta Corp"
    assert alert.status == "sent"

    # Verify persisted
    saved = db.query(Alert).filter(Alert.id == alert.id).first()
    assert saved is not None
    assert saved.message == "Dear Beta Corp, your invoice is overdue."
    db.close()
