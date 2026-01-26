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
    

# POST /alerts/send
@app.post("/alerts/send")
def send_alert(payload: dict, db: Session = Depends(get_db)):
    try:
        customer_id = int(payload["customer_id"])
        message = str(payload.get("message") or "Automatic risk alert")
    except Exception:
        raise HTTPException(status_code=400, detail="customer_id is required")

    try:
        alert = alerts_crud.create_alert_from_snapshot(
            db=db,
            customer_id=customer_id,
            message=message
        )
        return {"status": "sent", "alert_id": alert.id}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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
