import httpx
from typing import List, Dict
from fastapi import HTTPException
from settings import settings


class DolibarrClient:
    def __init__(self):
        if not settings.dolibarr_base_url or not settings.dolibarr_api_key:
            raise RuntimeError("Missing DOLIBARR_BASE_URL or DOLIBARR_API_KEY in .env")

        self.base_url = settings.dolibarr_base_url.rstrip("/")
        self.headers = {"DOLAPIKEY": settings.dolibarr_api_key}
        self.timeout = settings.dolibarr_timeout

    def _get(self, path: str, params: dict | None = None) -> List[Dict]:
        url = f"{self.base_url}{path}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                r = client.get(url, headers=self.headers, params=params)
                r.raise_for_status()
                return r.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Dolibarr connection error: {e}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=502, detail=f"Dolibarr API error: {e.response.text}")

    def get_customers(self) -> List[Dict]:
        return self._get("/api/index.php/thirdparties", params={"limit": 200})

    def get_invoices_by_customer(self, customer_id: int) -> List[Dict]:
        return self._get(
            "/api/index.php/invoices",
            params={"thirdparty_ids": customer_id, "limit": 200},
        )
