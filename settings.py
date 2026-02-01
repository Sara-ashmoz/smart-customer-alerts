from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    dolibarr_base_url: str = os.getenv("DOLIBARR_BASE_URL", "").rstrip("/")
    dolibarr_api_key: str = os.getenv("DOLIBARR_API_KEY", "")
    dolibarr_timeout: int = int(os.getenv("DOLIBARR_TIMEOUT", "20"))

    debt_threshold: float = float(os.getenv("DEBT_THRESHOLD", "1000"))
    unpaid_n: int = int(os.getenv("UNPAID_N", "3"))

    #EMAIL SETTINGS
    email_host: str = os.getenv("EMAIL_HOST")
    email_port: int = int(os.getenv("EMAIL_PORT", "587"))
    email_user: str = os.getenv("EMAIL_USER")
    email_pass: str = os.getenv("EMAIL_PASS")
    email_to: str = os.getenv("EMAIL_TO")
    email_from_name: str = os.getenv("EMAIL_FROM_NAME", "Smart Customer Alerts")

settings = Settings()
