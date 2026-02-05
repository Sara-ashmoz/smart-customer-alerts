import os
import pytest
from fastapi.testclient import TestClient


pytestmark = pytest.mark.integration


def _has_dolibarr_env() -> bool:
    return bool(os.getenv("DOLIBARR_BASE_URL")) and bool(os.getenv("DOLIBARR_API_KEY"))


def test_get_risk_customers_hits_real_dolibarr_and_persists_snapshot():
    if not _has_dolibarr_env():
        pytest.skip("Missing DOLIBARR_BASE_URL/DOLIBARR_API_KEY (integration test)")

    # Import app AFTER env exists
    from app import app
    client = TestClient(app)

    # Fresh DB
    from db import Base, engine, SessionLocal
    from models import CustomerRiskSnapshot

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # Call real endpoint (this calls Dolibarr and writes snapshots)
    resp = client.get("/risk/customers")
    assert resp.status_code == 200, resp.text

    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0, "Expected at least one customer from Dolibarr"

    first = data[0]
    assert "customer_id" in first
    assert "customer_name" in first
    assert "risk_score" in first
    assert "risk_level" in first

    # Verify snapshot persisted in DB for at least one customer
    db = SessionLocal()
    count = db.query(CustomerRiskSnapshot).count()
    db.close()

    assert count > 0, "Expected snapshots to be saved in DB"
