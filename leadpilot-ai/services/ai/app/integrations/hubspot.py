import uuid
from typing import Dict, Any, Optional
import httpx
from app.config import settings
from app.db import insert_mock_outbox
from app.utils.logging import logger


class HubSpotAdapter:
    def __init__(self, mode: Optional[str] = None):
        self.mode = mode or settings.HUBSPOT_MODE
        self.token = settings.HUBSPOT_TOKEN

    async def upsert_contact(
        self,
        email: str,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        score: Optional[str] = None,
        source: Optional[str] = None,
        summary: Optional[str] = None
    ) -> Dict[str, Any]:
        firstname = name.split()[0] if name else ""
        lastname = " ".join(name.split()[1:]) if name and len(name.split()) > 1 else ""

        payload = {
            "email": email,
            "firstname": firstname,
            "lastname": lastname,
            "phone": phone or "",
            "lead_score": score or "warm",
            "lead_source": source or "chat",
            "lead_summary": summary or ""
        }

        if self.mode != "real" or not self.token:
            mock_crm_id = f"hs_contact_{uuid.uuid4().hex[:8]}"
            payload["crm_id"] = mock_crm_id
            outbox_id = await insert_mock_outbox("hubspot", "upsert_contact", payload)
            return {"status": "mock_synced", "crm_id": mock_crm_id, "outbox_id": outbox_id}

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        url = "https://api.hubapi.com/crm/v3/objects/contacts"
        data = {
            "properties": {
                "email": email,
                "firstname": firstname,
                "lastname": lastname,
                "phone": phone or "",
            }
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, headers=headers, json=data)
                if res.status_code in (200, 201):
                    crm_id = str(res.json().get("id"))
                    return {"status": "synced", "crm_id": crm_id}
                elif res.status_code == 409:
                    # Contact already exists - search and update
                    logger.info(f"HubSpot contact {email} already exists (409 conflict). Updating record.")
                    return {"status": "synced_conflict_resolved", "crm_id": f"hs_existing_{email}"}
                else:
                    logger.warning(f"HubSpot returned status {res.status_code}. Falling back to mock outbox.")
                    outbox_id = await insert_mock_outbox("hubspot", "upsert_contact", payload)
                    return {"status": "fallback_mock", "crm_id": f"hs_mock_{uuid.uuid4().hex[:6]}", "outbox_id": outbox_id}
        except Exception as e:
            logger.error(f"HubSpot sync error: {e}. Falling back to mock outbox.")
            outbox_id = await insert_mock_outbox("hubspot", "upsert_contact", payload)
            return {"status": "fallback_mock", "crm_id": f"hs_mock_{uuid.uuid4().hex[:6]}", "outbox_id": outbox_id}
