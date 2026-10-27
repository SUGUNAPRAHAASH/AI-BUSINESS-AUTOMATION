import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db import init_db, fetch_one, fetch_all, execute

API_KEY_HEADER = {"X-API-Key": "lp_secret_key_demo_2026"}


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()


@pytest.mark.asyncio
async def test_clinical_severity_triage():
    """Verify clinical symptom triage routes to the appropriate specialist and slots."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Urgent / Pain
        res1 = await client.get("/v1/schedule/triage?symptoms=severe%20toothache%20and%20swelling&date=2026-10-31", headers=API_KEY_HEADER)
        assert res1.status_code == 200
        d1 = res1.json()
        assert d1["severity"] == "urgent"
        assert "doc-sarah" in d1["recommended_doctor_ids"]

        # 2. Orthodontics
        res2 = await client.get("/v1/schedule/triage?symptoms=I%20want%20Invisalign%20aligners&date=2026-10-31", headers=API_KEY_HEADER)
        assert res2.status_code == 200
        d2 = res2.json()
        assert d2["severity"] == "orthodontic"
        assert "doc-alex" in d2["recommended_doctor_ids"]

        # 3. Cosmetic
        res3 = await client.get("/v1/schedule/triage?symptoms=Professional%20teeth%20whitening&date=2026-10-31", headers=API_KEY_HEADER)
        assert res3.status_code == 200
        d3 = res3.json()
        assert d3["severity"] == "cosmetic"
        assert "doc-priya" in d3["recommended_doctor_ids"]

        # 4. Conflict check on Dr. Sarah at 11:00 AM (Emma Thompson)
        doc_sarah = next(d for d in d1["all_doctors"] if d["doctor_id"] == "doc-sarah")
        slot_1100 = next(s for s in doc_sarah["slots"] if s["start_time"] == "11:00")
        assert slot_1100["is_booked"] is True
        assert "Emma Thompson" in slot_1100["booked_info"]["patient_name"]

        # Dr. Sarah at 11:30 AM is open
        slot_1130 = next(s for s in doc_sarah["slots"] if s["start_time"] == "11:30")
        assert slot_1130["is_booked"] is False


@pytest.mark.asyncio
async def test_appointment_booking_and_location_storage():
    """Verify appointment booking stores patient_location and prevents double-booking."""
    await execute("DELETE FROM appointments WHERE patient_email = 'czeta@example.com'")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Book Dr. Alex at 11:00 AM on Saturday
        booking_payload = {
            "doctor_id": "doc-alex",
            "patient_name": "Catherine Zeta",
            "patient_email": "czeta@example.com",
            "patient_phone": "+1-555-019-9944",
            "patient_location": "Midtown Manhattan",
            "appointment_date": "2026-10-31",
            "start_time": "11:00",
            "duration_mins": 30,
            "service_type": "Orthodontic Aligners Scan",
            "notes": "Patient intake test"
        }
        res = await client.post("/v1/schedule/appointments", json=booking_payload, headers=API_KEY_HEADER)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "confirmed"

        # Verify DB row has patient_location
        app_id = data["appointment_id"]
        row = await fetch_one("SELECT * FROM appointments WHERE id = ?", (app_id,))
        assert row is not None
        assert row["patient_location"] == "Midtown Manhattan"
        assert row["doctor_name"] == "Dr. Alex Rivera, DMD"

        # Attempt to book exact same slot with Dr. Alex -> must be rejected with 409 SLOT_CONFLICT
        res_conflict = await client.post("/v1/schedule/appointments", json=booking_payload, headers=API_KEY_HEADER)
        assert res_conflict.status_code == 409
        err = res_conflict.json()["error"]
        assert err["code"] == "SLOT_CONFLICT"
        assert "already reserved" in err["message"]


@pytest.mark.asyncio
async def test_chat_lead_capture_no_fake_saturday_assignment():
    """Verify chat intake does not auto-book Saturday 11 AM blindly and stores location."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        msg = "Hi, my name is Arthur Dent, email arthur@example.com, phone 555-901-2233, location Brooklyn. What are your teeth cleaning prices?"
        res = await client.post("/v1/chat", json={"message": msg, "channel": "web"}, headers=API_KEY_HEADER)
        assert res.status_code == 200
        data = res.json()

        assert data["lead_captured"] is not None
        assert data["lead_captured"]["name"] == "Arthur Dent"
        assert data["lead_captured"]["location"] == "Brooklyn"

        # Verify DB leads record
        lead = await fetch_one("SELECT * FROM leads WHERE lower(email) = 'arthur@example.com'")
        assert lead is not None
        assert lead["patient_location"] == "Brooklyn"

        # Verify NO fake appointment was created for Arthur Dent at 11:00 AM on Saturday
        fake_app = await fetch_one("SELECT * FROM appointments WHERE lower(patient_email) = 'arthur@example.com'")
        assert fake_app is None
