"""
API + Integration (Dolibarr ERP) + DB Test Plan – Smart Customer Alerts

1) Scope (What we test)
-----------------------
We validate three things in the backend:

A) API Endpoints (FastAPI)
- GET  /risk/customers
- POST /alerts/send
- GET  /alerts

B) ERP Integration (Dolibarr)
- The application can pull real customers/invoices from Dolibarr
- The endpoint /risk/customers can run end-to-end against Dolibarr and persist results

C) Database (SQLite / SQLAlchemy)
- Snapshots are persisted and updated correctly (upsert)
- Alerts are created from snapshots and stored
- Alerts history is retrieved correctly


2) Test Types + Where They Run
------------------------------
A) API Tests (FastAPI + DB, stable)
- Run locally (CI-ready)
- Use TestClient to call endpoints
- Use mocks for external dependencies when needed

B) Integration Tests (ERP + DB)  [NOT RUN IN CI]
- Marked with: pytestmark = pytest.mark.integration
- Run locally only
- Use real Dolibarr credentials (env vars)
- Verify real data flow + DB persistence

Reason: integration tests depend on external ERP availability + secrets, so they are excluded from CI.


3) Environment / Setup
----------------------
- SQLite database reset per test (drop_all/create_all)
- FastAPI TestClient (no uvicorn)
- Dolibarr integration requires:
  * DOLIBARR_BASE_URL
  * DOLIBARR_API_KEY
- Email sending is patched/mocked in tests to avoid real sends.


4) Success Criteria
-------------------
API + DB + Integration testing is considered successful when:

- All tests pass consistently (no flaky failures).
- API endpoints return expected status codes and JSON structure.
- /risk/customers persists CustomerRiskSnapshot rows into DB.
- Upsert updates existing snapshot row (no duplicates).
- /alerts/send creates an Alert record only when snapshot exists.
- /alerts returns correct list schema and empty list when DB is empty.
- Real Dolibarr integration test (when env vars exist):
  * /risk/customers returns non-empty list
  * DB snapshot count > 0
- Code coverage is above 90% (Test Coverage >= 90%) and is visible in Codecov.


5) Test Cases Covered
---------------------
DB + CRUD (local)
- Upsert snapshot updates existing row (no duplicates)
- Create alert from snapshot pulls customer_name and saves Alert

API Endpoints (local)
- GET /risk/customers (mock Dolibarr) -> 200 + snapshots saved
- GET /risk/customers (Dolibarr failure) -> 500
- POST /alerts/send success -> 200 + email mocked + alert saved
- POST /alerts/send missing customer_id -> 400
- POST /alerts/send customer not in snapshot -> 400
- GET /alerts returns list + correct schema
- GET /alerts empty -> []

Integration (local only, pytest.mark.integration)
- GET /risk/customers hits real Dolibarr and persists snapshots
  (skipped automatically if env vars are missing)


6) Reporting
------------
- pytest -v (local): runs the tests with detailed output in the terminal.
- Allure (local): generates a visual test report for results, steps, and failures.
- Codecov (CI): uploads coverage.xml and shows coverage percentage in GitHub pull requests.
"""
