import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

class TestRiskCustomersEndpoint(unittest.TestCase):

    def setUp(self):
        # ensure fresh SQLAlchemy tables for each test run
        from db import Base, engine
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

        from app import app
        self.client = TestClient(app)

    @patch("app.DolibarrClient")
    def test_get_risk_customers_success(self, mock_dolibarr_client):
        fake_client_instance = MagicMock()
        mock_dolibarr_client.return_value = fake_client_instance

        fake_customers = [
            {"id": 1, "name": "Beta Corp"},
            {"id": 2, "name": "Delta Ltd"},
        ]
        fake_client_instance.get_customers.return_value = fake_customers

        beta_invoices = [
            {"id": 101, "socid": 1, "total_ttc": 1650, "paid": 0, "date_lim_reglement": "2023-01-01"},
            {"id": 102, "socid": 1, "total_ttc": 500,  "paid": 0, "date_lim_reglement": "2024-01-01"},
        ]
        delta_invoices = [
            {"id": 201, "socid": 2, "total_ttc": 200, "paid": 0, "date_lim_reglement": "2099-01-01"},
        ]

        fake_client_instance.get_invoices_by_customer.side_effect = lambda cid: (
            beta_invoices if cid == 1 else delta_invoices if cid == 2 else []
        )

        response = self.client.get("/risk/customers")
        self.assertEqual(response.status_code, 200)

        body = response.json()
        self.assertIsInstance(body, list)
        self.assertEqual(len(body), 2)

        beta = next(c for c in body if c["customer_id"] == 1)
        delta = next(c for c in body if c["customer_id"] == 2)

        self.assertTrue(beta["has_overdue"])
        self.assertEqual(beta["unpaid_count"], 2)
        self.assertEqual(beta["total_open_debt"], 2150.0)
        self.assertEqual(beta["risk_level"], "High")
        self.assertGreaterEqual(beta["risk_score"], 50)

        self.assertFalse(delta["has_overdue"])
        self.assertEqual(delta["unpaid_count"], 1)
        self.assertEqual(delta["total_open_debt"], 200.0)

        from db import SessionLocal
        from models import CustomerRiskSnapshot

        db = SessionLocal()
        snapshots = db.query(CustomerRiskSnapshot).all()
        db.close()

        self.assertEqual(len(snapshots), 2)

        beta_snapshot = next(s for s in snapshots if s.customer_id == 1)
        self.assertEqual(beta_snapshot.customer_name, "Beta Corp")
        self.assertEqual(beta_snapshot.risk_level, "High")
        self.assertTrue(beta_snapshot.has_overdue)

        print("✓ GET /risk/customers passed all assertions")


    @patch("app.DolibarrClient")
    def test_get_risk_customers_dolibarr_failure(self, mock_dolibarr_client):
        """
        Error case:
        DolibarrClient throws exception → API should return 500
        """

        fake_client_instance = MagicMock()
        fake_client_instance.get_customers.side_effect = Exception("Dolibarr down")
        mock_dolibarr_client.return_value = fake_client_instance

        response = self.client.get("/risk/customers")

        self.assertEqual(response.status_code, 500)

        body = response.json()
        self.assertIn("detail", body)
        self.assertIn("Dolibarr down", body["detail"])

        print("✓ GET /risk/customers handles Dolibarr failure correctly")


if __name__ == "__main__":
    unittest.main()
