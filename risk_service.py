from typing import List, Dict
from datetime import date, datetime
from dolibarr_client import DolibarrClient
from settings import settings


class RiskService:
    def __init__(self, client: DolibarrClient):
        self.client = client

    def _parse_date(self, d) -> date | None:
        if not d:
            return None

        # אם זה כבר date / datetime
        if isinstance(d, date) and not isinstance(d, datetime):
            return d
        if isinstance(d, datetime):
            return d.date()

        # אם זה Unix timestamp (מספר)
        if isinstance(d, (int, float)):
            try:
                return datetime.fromtimestamp(d).date()
            except Exception:
                return None

        # אם זה מחרוזת
        if isinstance(d, str):
            s = d.split("T")[0]
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S"):
                try:
                    return datetime.strptime(s, fmt).date()
                except Exception:
                    pass
            return None

        return None

    def _calc_risk(self, invoices: List[Dict]) -> Dict:
        today = date.today()

        unpaid_count = 0
        total_open_debt = 0.0
        has_overdue = False

        for inv in invoices:
            amount = float(inv.get("total_ttc") or inv.get("total") or inv.get("amount") or 0)

            paid_flag = inv.get("paid")  # בדוליבאר: 1 = שולם, 0 = לא שולם
            is_paid = (paid_flag == 1)

            if not is_paid:
                unpaid_count += 1
                total_open_debt += amount

                # זה השדה של "Payment due on" בדוליבאר
                due_raw = inv.get("date_lim_reglement") or inv.get("due_date") or inv.get("datedue")
                due_date = self._parse_date(due_raw)

                if due_date and due_date < today:
                    has_overdue = True

        score = 0
        reasons = []

        if has_overdue:
            score += 50
            reasons.append("Has at least one overdue invoice (+50)")

        if total_open_debt > settings.debt_threshold:
            score += 30
            reasons.append(f"Total open debt {total_open_debt:.2f} > {settings.debt_threshold} (+30)")

        if unpaid_count >= settings.unpaid_n:
            score += 20
            reasons.append(f"Unpaid invoices {unpaid_count} >= {settings.unpaid_n} (+20)")

        if score == 0:
            level = "Safe"
        elif score <= 39:
            level = "Low"
        elif score <= 69:
            level = "Medium"
        else:
            level = "High"


        return {
            "unpaid_count": unpaid_count,
            "total_open_debt": round(total_open_debt, 2),
            "has_overdue": has_overdue,
            "risk_score": float(score),
            "risk_level": level,
            "reasons": reasons,
        }
    
    def get_customers_risk(self) -> List[Dict]:
        customers = self.client.get_customers()
        results = []

        for c in customers:
            cid = int(c.get("id"))
            name = c.get("name") or c.get("nom") or f"customer_{cid}"

            invoices = self.client.get_invoices_by_customer(cid)
            risk = self._calc_risk(invoices)

            results.append(
                {
                    "customer_id": cid,
                    "customer_name": name,
                    **risk,
                }
            )

        results.sort(key=lambda x: x["risk_score"], reverse=True)
        return results

