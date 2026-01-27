# API Test Plan – Smart Customer Alerts Application

## 1. What to Test

The purpose of this test plan is to validate the Smart Customer Alerts backend API endpoints.

The following aspects will be tested:

- All public API endpoints exposed by the FastAPI application.
- Successful request handling (HTTP 200 responses).
- Correct response structure and JSON format.
- Proper interaction between the API layer and the SQLite database.
- Correct execution of the risk calculation business logic.
- Correct creation and storage of alert records.
- Correct retrieval of alert history.
- Error handling for invalid request payloads.
- Consistent risk level classification (Low / Medium / High).

Each API endpoint will have at least one corresponding integration test to ensure full API coverage.

---

## 2. Test Design Strategy

The chosen testing strategy is a combination of **API Unit Testing, Integration Testing, DB Integration Testing, and End-to-End (manual) testing**, as required by the project guidelines.

### Rationale:

- **API Unit tests** validate the internal business logic in isolation:
  - Risk score calculation
  - Risk level mapping (Low / Medium / High)
  - Reasons generation

- **DB integration tests** validate correct persistence and retrieval of alert records using a real SQLite database.

- **API integration tests** validate endpoint behavior using FastAPI’s `TestClient` without running a real server (Uvicorn).

- External services (Dolibarr ERP API) are **mocked** using `unittest.mock` to avoid dependency on external systems.

This approach ensures the API logic is tested in a realistic but controlled environment.

---

## 3. Test Environment

The tests will be executed in the following environments:

- **Local development environment**
  - TERMINAL – pytest
  - SQLite database initialized per test run

- **CI environment (GitHub Actions)**
  - Automated execution on each pull request
  - Unit + Integration tests executed automatically
  - Test results and coverage reported automatically

---

## 4. Success Criteria

The test execution will be considered successful when:

- All API endpoints are covered by integration tests (100% API endpoint coverage).
- All tests pass without errors.
- API responses return expected HTTP status codes.
- Response payloads match the expected structure.
- Risk score calculation follows the defined business rules:
  - Overdue invoice adds +50
  - Open debt above threshold adds +30
  - More than N unpaid invoices adds +20
- Risk levels are classified correctly:
  - 0–39 → Low
  - 40–69 → Medium
  - 70+ → High
- DB operations work correctly:
  - Alerts are stored successfully
  - Alerts history returns correct records
- Code coverage for the API layer is as close as possible to 100% and not less than 90%.
- Continuous Integration (CI) checks pass successfully.

---

## 5. Reporting

Test results and quality metrics will be reported using the following tools:

- **pytest** – for test execution and assertions.
- **pytest-cov** – for generating code coverage reports.
- **HTML coverage report** – generated locally for detailed inspection.
- **Codecov** – integrated with GitHub to display coverage metrics in pull requests.
- **GitHub Actions** – used to automatically run tests and enforce quality gates.

All reports will be accessible directly from the GitHub repository and CI pipeline.

---

# Test Types Included

## A) API Unit Testing (Logic Only)

Unit tests cover:

- Risk score calculation function.
- Risk level mapping (Low / Medium / High).
- Reasons generation formatting.
- Edge cases:
  - No invoices.
  - Zero debt.
  - Unpaid count exactly at threshold.
  - Overdue true / false combinations.

ERP responses are mocked as input objects. No HTTP calls are performed.

---

## B) DB Integration Testing (Alerts DB)

DB tests cover:

- Inserting an alert record when calling the alert logic.
- Retrieving alerts history from the database.
- Database reset / cleanup between tests (fresh DB per test).
- Data integrity:
  - Timestamp exists.
  - Status saved correctly.
  - Correct customer_id and customer_name.

Uses a real SQLite database initialized for each test.

---

## C) API Integration Testing (FastAPI + DB)

Integration tests cover all endpoints:

1) **GET /risk/customers**

- Returns a list of customers with required fields:
  - customer_id
  - customer_name
  - risk_score
  - risk_level
  - reasons
  - unpaid_count
  - total_open_debt
  - has_overdue

- Correct risk score and risk level based on mocked Dolibarr data.

---

2) **POST /alerts/send**

- Valid request creates a DB record and returns status "sent".
- Invalid request (missing customer_id or invalid template) returns proper error status.
- Only existing customers can receive alerts.

---

3) **GET /alerts**

- Returns all sent alerts.
- Returns records in correct schema:
  - id
  - customer_id
  - customer_name
  - message
  - status
  - timestamp

---

## D) End-to-End (Manual) Testing

Manual E2E tests validate the complete workflow:

1) Run Dolibarr locally (Docker) and create:
- 2–3 customers.
- Invoices (some overdue, some unpaid, different debt values).

2) Run Smart Customer Alerts backend (FastAPI).

3) Open the frontend dashboard.

4) Verify:

- Clicking "Refresh Risk" loads customers and risk levels.
- High / Medium / Low displayed correctly.
- Reasons match the scenario.
- Clicking "Send Alert" returns status "sent".
- Alerts appear in "History" after sending.
- Refresh does not break the state.

Manual E2E testing is documented as a checklist and can be demonstrated live.

---

## 6. Test Cases Table (High-Level)

| Test Case ID | Test Name                         | Endpoint            | Input                             | Expected Result                          |
|--------------|----------------------------------|---------------------|-----------------------------------|------------------------------------------|
| TC-01        | Get risk customers               | GET /risk/customers| None                              | 200 OK + list of customers               |
| TC-02        | Send alert – valid request       | POST /alerts/send  | customer_id, message_template     | 200 OK + status = "sent"                 |
| TC-03        | Send alert – invalid customer    | POST /alerts/send  | invalid customer_id               | 400 / 404 error                          |
| TC-04        | Get alerts history               | GET /alerts        | None                              | 200 OK + list of alerts                  |
| TC-05        | Risk logic – overdue invoice     | Unit Test           | overdue = true                    | risk_score >= 50                         |
| TC-06        | Risk logic – high debt           | Unit Test           | total_open_debt > threshold       | risk_score increased                     |
| TC-07        | DB insert alert                  | DB Test             | valid alert payload               | record saved in DB                       |
| TC-08        | DB fetch alerts                  | DB Test             | None                              | correct records returned                 |

---

End of Test Plan
"""