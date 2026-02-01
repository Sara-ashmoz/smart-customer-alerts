from typing import List
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
import models
from db import Base, engine, get_db
from dolibarr_client import DolibarrClient
from risk_service import RiskService
from schemas import CustomerRiskOut
from crud import alerts_crud, risk_crud
from fastapi.middleware.cors import CORSMiddleware
from settings import settings
from fastapi import BackgroundTasks
from email_service import send_email_smtp


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Customer Alerts API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# GET /risk/customers
@app.get("/risk/customers", response_model=List[CustomerRiskOut])
def get_risk_customers(db: Session = Depends(get_db)):
    try:
        client = DolibarrClient()
        service = RiskService(client)

        results = service.get_customers_risk()   

        for r in results:
            risk_crud.upsert_customer_risk_snapshot(db, {
                "customer_id": r["customer_id"],
                "customer_name": r["customer_name"],
                "unpaid_count": r["unpaid_count"],
                "total_open_debt": r["total_open_debt"],
                "has_overdue": r["has_overdue"],
                "risk_score": r["risk_score"],
                "risk_level": r["risk_level"],
                "reasons": r["reasons"],  # list
            })

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/alerts/send")
def send_alert(
    payload: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    # 1) validate input
    try:
        customer_id = int(payload["customer_id"])
        message = str(payload.get("message") or "Automatic risk alert")
    except Exception:
        raise HTTPException(status_code=400, detail="customer_id is required")

    # 2) create alert in DB (this pulls customer_name from the snapshot internally)
    raw_message = (
    payload.get("message")
    or payload.get("preview")
    or payload.get("email_body")
)

    message = raw_message.strip() if isinstance(raw_message, str) and raw_message.strip() else "Automatic risk alert"

    try:
        alert = alerts_crud.create_alert_from_snapshot(
            db=db,
            customer_id=customer_id,
            message = message,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 3) email content (UI-friendly)
    customer_name = alert.customer_name
    subject = f"🚨 Risk Alert – {customer_name}"
    body = f"""Smart Customer Alerts

Customer: {customer_name}

Message:
{alert.message}
"""

    # 4) send email asynchronously
    background_tasks.add_task(
        send_email_smtp,
        settings.email_host,
        settings.email_port,
        settings.email_user,
        settings.email_pass,
        settings.email_to,          # always your email
        subject,
        body,
        settings.email_from_name,
    )

    # 5) response
    return {
        "status": "sent",
        "alert_id": alert.id,
        "customer_name": customer_name,
        "email_sent_to": settings.email_to,
    }


# GET /alerts
@app.get("/alerts")
def alerts_history(db: Session = Depends(get_db)):
    rows = alerts_crud.get_alerts(db)

    return [
        {
            "id": a.id,
            "customer_id": a.customer_id,
            "customer_name": a.customer_name,
            "message": a.message,
            "status": a.status,
            "timestamp": a.timestamp,
        }
        for a in rows
    ]
    

@app.get("/health")
def health():
    return {"status": "ok"}
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
