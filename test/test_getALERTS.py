import unittest
from fastapi.testclient import TestClient


class TestAlertsHistoryEndpoint(unittest.TestCase):

    def setUp(self):
        # fresh DB each run
        from db import Base, engine
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

        from app import app
        self.client = TestClient(app)

        # seed data: insert 2 alerts directly to DB
        from db import SessionLocal
        from models import Alert

        db = SessionLocal()

        a1 = Alert(
            customer_id=1,
            customer_name="Beta Corp",
            message="Dear Beta Corp, your invoice is overdue.",
            status="sent",
        )
        a2 = Alert(
            customer_id=2,
            customer_name="Delta Ltd",
            message="Friendly reminder: please review your account status.",
            status="sent",
        )

        db.add_all([a1, a2])
        db.commit()
        db.close()

    def test_get_alerts_success(self):
        """
        Test GET /alerts
        - returns list of alerts
        - validates response structure
        """
        response = self.client.get("/alerts")
        self.assertEqual(response.status_code, 200)

        body = response.json()
        self.assertIsInstance(body, list)
        self.assertEqual(len(body), 2)

        # validate keys exist + types
        for a in body:
            self.assertIn("id", a)
            self.assertIn("customer_id", a)
            self.assertIn("customer_name", a)
            self.assertIn("message", a)
            self.assertIn("status", a)
            self.assertIn("timestamp", a)

            self.assertIsInstance(a["id"], int)
            self.assertIsInstance(a["customer_id"], int)
            self.assertIsInstance(a["customer_name"], str)
            self.assertIsInstance(a["message"], str)
            self.assertIsInstance(a["status"], str)
            # timestamp usually comes back as str (isoformat) - depends on your code
            self.assertTrue(a["timestamp"] is None or isinstance(a["timestamp"], str))

        # specific check (find by customer_id)
        beta = next(x for x in body if x["customer_id"] == 1)
        self.assertEqual(beta["customer_name"], "Beta Corp")
        self.assertEqual(beta["status"], "sent")
        self.assertIn("overdue", beta["message"].lower())

        print("✓ GET /alerts passed all assertions")

    def test_get_alerts_empty(self):
        """
        Test GET /alerts when DB is empty -> should return []
        """
        # wipe alerts table only
        from db import SessionLocal
        from models import Alert

        db = SessionLocal()
        db.query(Alert).delete()
        db.commit()
        db.close()

        response = self.client.get("/alerts")
        self.assertEqual(response.status_code, 200)

        body = response.json()
        self.assertEqual(body, [])

        print("✓ GET /alerts empty passed all assertions")


if __name__ == "__main__":
    unittest.main()
