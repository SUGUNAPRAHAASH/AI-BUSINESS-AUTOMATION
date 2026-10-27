import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from app.db import execute, fetch_all, fetch_one
from app.security import verify_api_key
from app.integrations.gmail import EmailAdapter
from app.integrations.telegram import TelegramAdapter
from app.integrations.slack import SlackAdapter
from app.integrations.airtable import AirtableAdapter
from app.utils.logging import logger

router = APIRouter(prefix="/v1/schedule", tags=["Clinical Scheduling & Roster"])


# --- Pydantic Schemas ---

class DoctorScheduleItem(BaseModel):
    day_of_week: int
    day_name: str
    start_time: str
    end_time: str
    lunch_start: Optional[str] = None
    lunch_end: Optional[str] = None
    slot_duration_mins: int = 30
    is_working: int = 1


class DoctorUpdateRosterRequest(BaseModel):
    schedules: List[DoctorScheduleItem]


class BookAppointmentRequest(BaseModel):
    doctor_id: Optional[str] = None
    appointment_date: str  # YYYY-MM-DD
    start_time: str        # HH:MM
    duration_mins: int = 30
    patient_name: str
    patient_email: str
    patient_phone: Optional[str] = None
    service_type: str = "Basic Consultation (30 mins)"
    notes: Optional[str] = None


# --- Helper Time Functions ---

def parse_time_to_minutes(t_str: str) -> int:
    parts = t_str.strip().split(":")
    return int(parts[0]) * 60 + int(parts[1])


def format_minutes_to_time(mins: int) -> str:
    h = mins // 60
    m = mins % 60
    return f"{h:02d}:{m:02d}"


# --- Endpoints ---

@router.get("/doctors", dependencies=[Depends(verify_api_key)])
async def list_doctors():
    """List all clinic doctors with their active specialties, cabins, and schedules."""
    docs = await fetch_all("SELECT * FROM doctors ORDER BY name ASC")
    results = []
    for d in docs:
        schedules = await fetch_all(
            "SELECT * FROM doctor_schedules WHERE doctor_id = ? ORDER BY day_of_week ASC",
            (d["id"],)
        )
        results.append({
            "id": d["id"],
            "name": d["name"],
            "title": d["title"],
            "specialty": d["specialty"],
            "cabin": d["cabin"],
            "color": d["color"],
            "is_active": bool(d["is_active"]),
            "schedules": schedules
        })
    return {"doctors": results, "total": len(results)}


@router.put("/doctors/{doctor_id}/roster", dependencies=[Depends(verify_api_key)])
async def update_doctor_roster(doctor_id: str, req: DoctorUpdateRosterRequest):
    """Admin endpoint: Adjust working hours, lunch buffers, and slot durations for any doctor."""
    doc = await fetch_one("SELECT * FROM doctors WHERE id = ?", (doctor_id,))
    if not doc:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": f"Doctor {doctor_id} not found"})

    for s in req.schedules:
        sid = f"sched-{doctor_id.replace('doc-', '')}-{s.day_of_week}"
        await execute(
            "INSERT OR REPLACE INTO doctor_schedules (id, doctor_id, day_of_week, day_name, start_time, end_time, lunch_start, lunch_end, slot_duration_mins, is_working) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (sid, doctor_id, s.day_of_week, s.day_name, s.start_time, s.end_time, s.lunch_start, s.lunch_end, s.slot_duration_mins, s.is_working)
        )
    return {"status": "success", "message": f"Roster updated for {doc['name']}"}


@router.get("/slots", dependencies=[Depends(verify_api_key)])
async def get_daily_slots(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    doctor_id: Optional[str] = Query(None, description="Optional doctor filter")
):
    """
    Generate real-time consultation slots for the given date.
    Respects doctor working hours, lunch pauses, and marks booked slots to guarantee zero overlaps.
    """
    try:
        dt = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail={"code": "INVALID_DATE", "message": "Date must be YYYY-MM-DD format"})

    day_of_week = dt.weekday()  # 0=Monday ... 6=Sunday

    doc_query = "SELECT * FROM doctors WHERE is_active = 1"
    params = []
    if doctor_id and isinstance(doctor_id, str):
        doc_query += " AND id = ?"
        params.append(doctor_id)
    doctors = await fetch_all(doc_query, tuple(params))

    # Fetch all booked appointments on this date
    existing_appointments = await fetch_all(
        "SELECT * FROM appointments WHERE appointment_date = ? AND status != 'cancelled'",
        (date,)
    )

    all_doctor_slots = []
    time_slot_map: Dict[str, Dict[str, Any]] = {}

    for doc in doctors:
        did = doc["id"]
        sched = await fetch_one(
            "SELECT * FROM doctor_schedules WHERE doctor_id = ? AND day_of_week = ?",
            (did, day_of_week)
        )
        if not sched or not sched["is_working"]:
            all_doctor_slots.append({
                "doctor_id": did,
                "doctor_name": doc["name"],
                "specialty": doc["specialty"],
                "cabin": doc["cabin"],
                "color": doc["color"],
                "is_working_today": False,
                "slots": []
            })
            continue

        start_min = parse_time_to_minutes(sched["start_time"])
        end_min = parse_time_to_minutes(sched["end_time"])
        slot_len = sched["slot_duration_mins"] or 30

        lunch_s = parse_time_to_minutes(sched["lunch_start"]) if sched["lunch_start"] else None
        lunch_e = parse_time_to_minutes(sched["lunch_end"]) if sched["lunch_end"] else None

        doc_appointments = [a for a in existing_appointments if a["doctor_id"] == did]

        generated_slots = []
        cur_min = start_min
        while cur_min + slot_len <= end_min:
            # Skip if inside lunch break
            if lunch_s and lunch_e and (cur_min >= lunch_s and cur_min < lunch_e):
                cur_min += slot_len
                continue

            slot_start_str = format_minutes_to_time(cur_min)
            slot_end_str = format_minutes_to_time(cur_min + slot_len)

            # Check overlap with existing appointments
            overlapping = None
            for app in doc_appointments:
                app_s = parse_time_to_minutes(app["start_time"])
                app_e = parse_time_to_minutes(app["end_time"])
                if max(cur_min, app_s) < min(cur_min + slot_len, app_e):
                    overlapping = app
                    break

            slot_data = {
                "start_time": slot_start_str,
                "end_time": slot_end_str,
                "duration_mins": slot_len,
                "is_booked": bool(overlapping),
                "booked_info": {
                    "patient_name": overlapping["patient_name"],
                    "service": overlapping["service_type"],
                    "appointment_id": overlapping["id"]
                } if overlapping else None
            }
            generated_slots.append(slot_data)

            # Aggregate across clinic
            if slot_start_str not in time_slot_map:
                time_slot_map[slot_start_str] = {
                    "time": slot_start_str,
                    "available_doctors": [],
                    "booked_doctors": []
                }
            if not overlapping:
                time_slot_map[slot_start_str]["available_doctors"].append({
                    "id": did,
                    "name": doc["name"],
                    "specialty": doc["specialty"]
                })
            else:
                time_slot_map[slot_start_str]["booked_doctors"].append({
                    "id": did,
                    "name": doc["name"],
                    "patient": overlapping["patient_name"]
                })

            cur_min += slot_len

        all_doctor_slots.append({
            "doctor_id": did,
            "doctor_name": doc["name"],
            "specialty": doc["specialty"],
            "cabin": doc["cabin"],
            "color": doc["color"],
            "is_working_today": True,
            "working_hours": f"{sched['start_time']} - {sched['end_time']}",
            "slot_duration": slot_len,
            "slots": generated_slots
        })

    # Sort time slot aggregate
    clinic_timeline = sorted(time_slot_map.values(), key=lambda x: parse_time_to_minutes(x["time"]))

    return {
        "date": date,
        "day_name": dt.strftime("%A"),
        "doctors": all_doctor_slots,
        "timeline": clinic_timeline
    }


@router.post("/appointments", dependencies=[Depends(verify_api_key)])
async def book_appointment(req: BookAppointmentRequest):
    """
    Atomically schedule a patient appointment without overlaps.
    Automatically sends dual emails:
    1) Dedicated Hospital Alert to prahaashnms18@gmail.com
    2) Patient Confirmation to the patient's entered email.
    """
    try:
        dt = datetime.strptime(req.appointment_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail={"code": "INVALID_DATE", "message": "Invalid date format. Use YYYY-MM-DD"})

    day_of_week = dt.weekday()
    req_start_min = parse_time_to_minutes(req.start_time)
    req_end_min = req_start_min + req.duration_mins
    req_end_str = format_minutes_to_time(req_end_min)

    target_doctor_id = req.doctor_id
    assigned_doctor = None

    # If doctor specified, verify existence and availability
    if target_doctor_id:
        doc = await fetch_one("SELECT * FROM doctors WHERE id = ? AND is_active = 1", (target_doctor_id,))
        if not doc:
            raise HTTPException(status_code=404, detail={"code": "DOCTOR_NOT_FOUND", "message": f"Doctor {target_doctor_id} not found or inactive"})
        assigned_doctor = doc
    else:
        # Auto-assign: Find any working doctor available at this time
        doctors = await fetch_all("SELECT * FROM doctors WHERE is_active = 1")
        for d in doctors:
            sched = await fetch_one("SELECT * FROM doctor_schedules WHERE doctor_id = ? AND day_of_week = ? AND is_working = 1", (d["id"], day_of_week))
            if sched:
                s_min = parse_time_to_minutes(sched["start_time"])
                e_min = parse_time_to_minutes(sched["end_time"])
                if req_start_min >= s_min and req_end_min <= e_min:
                    # Check existing overlap
                    overlap = await fetch_one(
                        "SELECT id FROM appointments WHERE doctor_id = ? AND appointment_date = ? AND status != 'cancelled' AND "
                        "NOT (end_time <= ? OR start_time >= ?)",
                        (d["id"], req.appointment_date, req.start_time, req_end_str)
                    )
                    if not overlap:
                        assigned_doctor = d
                        target_doctor_id = d["id"]
                        break

    if not assigned_doctor:
        raise HTTPException(status_code=404, detail={"code": "NO_DOCTOR_AVAILABLE", "message": "No doctors on duty for the requested date and time."})

    # Check conflict for assigned doctor
    sched = await fetch_one(
        "SELECT * FROM doctor_schedules WHERE doctor_id = ? AND day_of_week = ? AND is_working = 1",
        (target_doctor_id, day_of_week)
    )
    if not sched:
        raise HTTPException(status_code=400, detail={
            "code": "DOCTOR_NOT_WORKING",
            "message": f"{assigned_doctor['name']} does not have office hours on {dt.strftime('%A')}."
        })

    # Strict overlap prevention
    overlap = await fetch_one(
        "SELECT id, patient_name, start_time, end_time FROM appointments "
        "WHERE doctor_id = ? AND appointment_date = ? AND status != 'cancelled' AND "
        "NOT (end_time <= ? OR start_time >= ?)",
        (target_doctor_id, req.appointment_date, req.start_time, req_end_str)
    )
    if overlap:
        # Find alternative available doctors at this same time
        all_docs = await fetch_all("SELECT * FROM doctors WHERE is_active = 1 AND id != ?", (target_doctor_id,))
        alt_docs = []
        for ad in all_docs:
            asched = await fetch_one("SELECT * FROM doctor_schedules WHERE doctor_id = ? AND day_of_week = ? AND is_working = 1", (ad["id"], day_of_week))
            if asched:
                a_overlap = await fetch_one(
                    "SELECT id FROM appointments WHERE doctor_id = ? AND appointment_date = ? AND status != 'cancelled' AND "
                    "NOT (end_time <= ? OR start_time >= ?)",
                    (ad["id"], req.appointment_date, req.start_time, req_end_str)
                )
                if not a_overlap:
                    alt_docs.append({"id": ad["id"], "name": ad["name"], "specialty": ad["specialty"]})

        raise HTTPException(
            status_code=409,
            detail={
                "code": "SLOT_CONFLICT",
                "message": f"Time slot conflict: {assigned_doctor['name']} is already reserved at {req.start_time} on {dt.strftime('%A, %b %d')}.",
                "booked_slot": f"{req.start_time} - {req_end_str}",
                "alternative_doctors_available_at_same_time": alt_docs,
                "suggestion": f"Dr. {assigned_doctor['name'].split()[-1]} is booked. You can choose another doctor above or book the next open slot."
            }
        )

    # All clear - Insert appointment
    app_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    await execute(
        "INSERT INTO appointments (id, tenant_id, doctor_id, doctor_name, patient_name, patient_email, patient_phone, appointment_date, start_time, end_time, duration_mins, service_type, status, notes, created_at) "
        "VALUES (?, 'a0000000-0000-0000-0000-000000000001', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'confirmed', ?, ?)",
        (app_id, target_doctor_id, assigned_doctor["name"], req.patient_name, req.patient_email, req.patient_phone, req.appointment_date, req.start_time, req_end_str, req.duration_mins, req.service_type, req.notes, now_iso)
    )

    # 1. Dispatch Hospital Side Intimation Email to prahaashnms18@gmail.com
    emailer = EmailAdapter()
    await emailer.send_hospital_intake_alert({
        "name": req.patient_name,
        "email": req.patient_email,
        "phone": req.patient_phone,
        "doctor_name": assigned_doctor["name"],
        "date_time": f"{dt.strftime('%A, %b %d, %Y')} at {req.start_time} - {req_end_str}",
        "service": req.service_type,
        "notes": req.notes or f"Booked via practice calendar for {req.duration_mins} min consultation."
    })

    # 2. Dispatch Patient Confirmation Email to the patient's entered email
    await emailer.send_patient_confirmation(
        to_addr=req.patient_email,
        data={
            "name": req.patient_name,
            "doctor_name": assigned_doctor["name"],
            "date_time": f"{dt.strftime('%A, %b %d, %Y')} at {req.start_time} - {req_end_str}",
            "service": req.service_type,
            "phone": req.patient_phone or "On File"
        }
    )

    # 3. Notify Staff via Telegram & Slack
    try:
        telegram = TelegramAdapter()
        await telegram.send_message(
            f"📅 *NEW APPOINTMENT RESERVED!*\n\n"
            f"👤 *Patient:* {req.patient_name}\n"
            f"🩺 *Doctor:* {assigned_doctor['name']}\n"
            f"⏰ *Time:* {dt.strftime('%A, %b %d')} at {req.start_time} ({req.duration_mins} mins)\n"
            f"📧 *Email:* {req.patient_email}\n"
            f"📞 *Phone:* {req.patient_phone or 'N/A'}\n"
            f"🦷 *Service:* {req.service_type}"
        )
        slack = SlackAdapter()
        await slack.send_message(
            text=f"📅 Confirmed Appointment: {req.patient_name} with {assigned_doctor['name']} on {dt.strftime('%A, %b %d')} at {req.start_time}"
        )
    except Exception as e:
        logger.warning(f"Team messenger dispatch warning: {e}")

    # 4. Upsert Airtable record
    try:
        airtable = AirtableAdapter()
        await airtable.create_record({
            "Name": f"{req.patient_name} ({assigned_doctor['name']})",
            "Notes": f"Appointment: {req.appointment_date} {req.start_time} ({req.duration_mins}m) | Email: {req.patient_email} | Phone: {req.patient_phone or 'N/A'} | {req.service_type}"
        })
    except Exception as e:
        logger.warning(f"Airtable sync warning: {e}")

    return {
        "status": "confirmed",
        "appointment_id": app_id,
        "doctor_name": assigned_doctor["name"],
        "doctor_specialty": assigned_doctor["specialty"],
        "cabin": assigned_doctor["cabin"],
        "patient_name": req.patient_name,
        "patient_email": req.patient_email,
        "appointment_date": req.appointment_date,
        "time_slot": f"{req.start_time} - {req_end_str}",
        "duration_mins": req.duration_mins,
        "service_type": req.service_type,
        "message": f"Appointment successfully scheduled with {assigned_doctor['name']}. Confirmation emails delivered to patient and hospital administration."
    }


@router.get("/appointments", dependencies=[Depends(verify_api_key)])
async def list_appointments(
    date: Optional[str] = Query(None),
    doctor_id: Optional[str] = Query(None)
):
    """List scheduled appointments with optional date or doctor filter."""
    query = "SELECT * FROM appointments WHERE status != 'cancelled'"
    params = []
    if date and isinstance(date, str):
        query += " AND appointment_date = ?"
        params.append(date)
    if doctor_id and isinstance(doctor_id, str):
        query += " AND doctor_id = ?"
        params.append(doctor_id)
    query += " ORDER BY appointment_date ASC, start_time ASC"

    rows = await fetch_all(query, tuple(params))
    return {"appointments": rows, "total": len(rows)}


@router.delete("/appointments/{appointment_id}", dependencies=[Depends(verify_api_key)])
async def cancel_appointment(appointment_id: str):
    """Cancel an appointment and free the slot immediately."""
    app = await fetch_one("SELECT * FROM appointments WHERE id = ?", (appointment_id,))
    if not app:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Appointment not found"})

    await execute("UPDATE appointments SET status = 'cancelled' WHERE id = ?", (appointment_id,))
    return {"status": "cancelled", "message": f"Appointment {appointment_id} for {app['patient_name']} has been cancelled and the slot is now open."}
