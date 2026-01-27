import unittest
from fastapi.testclient import TestClient

class TestAlertsSendEndpoint(unittest.TestCase):

    def setUp(self):
        from app import app
        self.client = TestClient(app)

        # fresh DB each run (אחרי import app כדי למחוק גם כל seed)
        from db import Base, engine
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def _insert_snapshot(self, customer_id=1):
        from db import SessionLocal
        from models import CustomerRiskSnapshot

        db = SessionLocal()

        # ביטחון: אם משהו כבר הכניס שורה עם אותו customer_id – מוחקים
        db.query(CustomerRiskSnapshot).filter(
            CustomerRiskSnapshot.customer_id == customer_id
        ).delete()
        db.commit()

        snap = CustomerRiskSnapshot(
            customer_id=customer_id,
            customer_name="Beta Corp",
            unpaid_count=2,
            total_open_debt=2150.0,
            has_overdue=True,
            risk_score=80.0,
            risk_level="High",
            reasons="Has at least one overdue invoice (+50)"
        )
        db.add(snap)
        db.commit()
        db.close()

    def test_send_alert_success(self):
        self._insert_snapshot(customer_id=1)

        payload = {"customer_id": 1, "message": "Dear Beta Corp, your invoice is overdue."}
        response = self.client.post("/alerts/send", json=payload)
        self.assertEqual(response.status_code, 200)

        body = response.json()
        self.assertEqual(body["status"], "sent")
        self.assertIsInstance(body["alert_id"], int)

        # DB assert: alert saved
        from db import SessionLocal
        from models import Alert

        db = SessionLocal()
        alert = db.query(Alert).filter(Alert.id == body["alert_id"]).first()
        db.close()

        self.assertIsNotNone(alert)
        self.assertEqual(alert.customer_id, 1)
        self.assertEqual(alert.status, "sent")

    def test_send_alert_missing_customer_id(self):
        payload = {"message": "hi"}
        response = self.client.post("/alerts/send", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "customer_id is required")

    def test_send_alert_customer_not_in_snapshot(self):
        payload = {"customer_id": 999, "message": "hello"}
        response = self.client.post("/alerts/send", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertTrue(isinstance(response.json().get("detail"), str))

if __name__ == "__main__":
    unittest.main()

