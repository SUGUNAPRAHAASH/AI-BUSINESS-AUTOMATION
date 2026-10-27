import smtplib
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from app.config import settings
from app.db import insert_mock_outbox
from app.utils.logging import logger


HOSPITAL_ALERT_EMAIL = "prahaashnms18@gmail.com"


class EmailAdapter:
    def __init__(self, mode: Optional[str] = None):
        self.mode = mode or settings.GMAIL_MODE
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.smtp_user if hasattr(settings, "smtp_user") else settings.SMTP_USER
        self.smtp_password = settings.smtp_password if hasattr(settings, "smtp_password") else settings.SMTP_PASSWORD
        self.smtp_from = settings.SMTP_FROM
        self.resend_api_key = settings.RESEND_API_KEY
        self.hospital_email = HOSPITAL_ALERT_EMAIL

    async def send_email(
        self,
        to_addr: str,
        subject: str,
        body: str,
        is_html: bool = False
    ) -> Dict[str, Any]:
        payload = {
            "from": self.smtp_from,
            "to": to_addr,
            "subject": subject,
            "body": body
        }

        # 1. Try Resend API if API key provided
        if self.resend_api_key:
            try:
                headers = {
                    "Authorization": f"Bearer {self.resend_api_key}",
                    "Content-Type": "application/json"
                }
                resend_payload = {
                    "from": "BrightSmile Dental <onboarding@resend.dev>",
                    "to": [to_addr],
                    "subject": subject,
                    "html" if is_html else "text": body
                }
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post("https://api.resend.com/emails", headers=headers, json=resend_payload)
                    if resp.status_code in (200, 201):
                        logger.info(f"Live email delivered via Resend API to {to_addr}")
                        await insert_mock_outbox("gmail", "email_delivered", payload)
                        return {"status": "sent", "transport": "resend", "data": resp.json()}
                    elif resp.status_code == 403 and to_addr.lower() != self.hospital_email.lower():
                        logger.warning(f"Resend sandbox limitation: routing patient copy to hospital owner {self.hospital_email}")
                        prefix_subject = f"[PATIENT COPY -> {to_addr}] {subject}"
                        sandbox_notice = (
                            f'<div style="background:#fef3c7;border:1px solid #f59e0b;color:#92400e;padding:12px;border-radius:8px;margin-bottom:16px;font-size:12px;font-family:sans-serif;">'
                            f'<strong>Hospital Dispatch Note:</strong> In Resend Sandbox mode, a live copy of this patient confirmation '
                            f'was dispatched to your hospital administrator mailbox (<code>{self.hospital_email}</code>) on behalf of recipient <code>{to_addr}</code>.</div>'
                        )
                        resend_payload["to"] = [self.hospital_email]
                        resend_payload["subject"] = prefix_subject
                        if is_html:
                            resend_payload["html"] = sandbox_notice + body
                        else:
                            resend_payload["text"] = f"[Hospital Dispatch Note: Sent on behalf of {to_addr}]\n\n" + body

                        retry_resp = await client.post("https://api.resend.com/emails", headers=headers, json=resend_payload)
                        if retry_resp.status_code in (200, 201):
                            logger.info(f"Delivered sandbox patient copy to {self.hospital_email} (for {to_addr})")
                            await insert_mock_outbox("gmail", "email_dispatched_sandbox_copy", {"target_recipient": to_addr, "owner_delivered": self.hospital_email, "subject": prefix_subject})
                            return {"status": "sent_sandbox_owner", "transport": "resend", "data": retry_resp.json()}
                    else:
                        logger.warning(f"Resend API error ({resp.status_code}): {resp.text}")
            except Exception as e:
                logger.error(f"Resend dispatch error: {e}")

        # 2. Try SMTP if real mode or credentials configured
        if self.mode == "real" and self.smtp_user:
            try:
                msg = MIMEMultipart()
                msg['From'] = self.smtp_from
                msg['To'] = to_addr
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'html' if is_html else 'plain'))

                server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=8)
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
                server.quit()
                logger.info(f"Email sent via SMTP ({self.smtp_host}:{self.smtp_port}) to {to_addr}")
                await insert_mock_outbox("gmail", "email_sent_smtp", payload)
                return {"status": "sent", "transport": "smtp"}
            except Exception as e:
                logger.warning(f"SMTP send failed ({e}).")

        # 3. Persist to activity outbox
        outbox_id = await insert_mock_outbox("gmail", "email_dispatched", payload)
        return {"status": "dispatched", "outbox_id": outbox_id, "payload": payload}

    async def send_hospital_intake_alert(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send dedicated notification to hospital side (prahaashnms18@gmail.com)."""
        patient_name = data.get("name") or "New Patient"
        patient_email = data.get("email") or "Not provided"
        patient_phone = data.get("phone") or "Not provided"
        doctor_name = data.get("doctor_name") or "Dr. Sarah Mitchell, DDS"
        date_time = data.get("date_time") or data.get("timeline_text") or "Upcoming Consultation"
        service = data.get("service") or data.get("interest") or "Basic Consultation (30 mins)"
        notes = data.get("notes") or data.get("summary") or "Patient self-booked via AI assistant."
        score = (data.get("score") or "HOT").upper()

        subject = f"🏥 [HOSPITAL INTAKE ALERT] New Patient Consultation: {patient_name} ({date_time})"
        html_body = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 620px; margin: 0 auto; padding: 24px; border: 1px solid #cbd5e1; border-radius: 14px; background: #ffffff;">
            <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 2px solid #0d9488; padding-bottom: 14px;">
                <div>
                    <h2 style="color: #0f766e; margin: 0; font-size: 20px;">🏥 BrightSmile Practice Alert</h2>
                    <p style="color: #64748b; font-size: 13px; margin: 3px 0 0 0;">New Appointment & Triage Notification (Hospital Administration)</p>
                </div>
                <span style="background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; padding: 4px 10px; border-radius: 9999px; font-weight: 700; font-size: 11px;">
                    STATUS: {score} LEAD
                </span>
            </div>

            <div style="padding: 18px 0; color: #1e293b; line-height: 1.6;">
                <p style="font-size: 15px; margin-top: 0;">
                    A new patient consultation has been officially scheduled via the <strong>AI Practice Operations Hub</strong>.
                </p>

                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; margin: 16px 0;">
                    <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                        <tr>
                            <td style="padding: 6px 0; color: #64748b; width: 140px;"><strong>👤 Patient Name:</strong></td>
                            <td style="padding: 6px 0; color: #0f172a; font-weight: 600;">{patient_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 0; color: #64748b;"><strong>📧 Patient Email:</strong></td>
                            <td style="padding: 6px 0; color: #0d9488; font-weight: 600;">{patient_email}</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 0; color: #64748b;"><strong>📞 Patient Phone:</strong></td>
                            <td style="padding: 6px 0; color: #0f172a; font-weight: 600;">{patient_phone}</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 0; color: #64748b;"><strong>📅 Scheduled Slot:</strong></td>
                            <td style="padding: 6px 0; color: #0f172a; font-weight: 700; background: #e0f2fe; padding-left: 6px; border-radius: 4px;">{date_time} (30 mins)</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 0; color: #64748b;"><strong>🩺 Attending Doctor:</strong></td>
                            <td style="padding: 6px 0; color: #0f172a; font-weight: 600;">{doctor_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 0; color: #64748b;"><strong>🦷 Service / Category:</strong></td>
                            <td style="padding: 6px 0; color: #0f172a;">{service}</td>
                        </tr>
                    </table>
                </div>

                <div style="background: #f0fdf4; border-left: 4px solid #10b981; padding: 12px 16px; border-radius: 6px; margin-bottom: 16px;">
                    <p style="margin: 0; font-size: 13px; color: #065f46;">
                        <strong>Clinical Triage Note:</strong><br>{notes}
                    </p>
                </div>

                <p style="font-size: 13px; color: #64748b;">
                    Synced automatically with HubSpot CRM, Airtable Practice Records, and Staff Telegram channel.
                </p>
            </div>

            <div style="border-top: 1px solid #f1f5f9; padding-top: 14px; text-align: center; font-size: 12px; color: #94a3b8;">
                BrightSmile Practice Operations Engine • Autonomous Clinic Hub
            </div>
        </div>
        """
        return await self.send_email(
            to_addr=self.hospital_email,
            subject=subject,
            body=html_body,
            is_html=True
        )

    async def send_patient_confirmation(self, to_addr: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send reassuring confirmation to patient with doctor details and preparation notes."""
        patient_name = data.get("name") or "Valued Patient"
        doctor_name = data.get("doctor_name") or "Dr. Sarah Mitchell, DDS"
        date_time = data.get("date_time") or data.get("timeline_text") or "Upcoming Saturday at 11:00 AM"
        service = data.get("service") or data.get("interest") or "Basic Dental Consultation (30 mins)"
        phone = data.get("phone") or "on file"

        subject = f"🦷 Appointment Confirmed: {service} with {doctor_name}"
        html_body = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 28px; border: 1px solid #e2e8f0; border-radius: 16px; background: #ffffff;">
            <div style="text-align: center; padding-bottom: 20px; border-bottom: 2px solid #0d9488;">
                <h1 style="color: #0f766e; margin: 0; font-size: 24px; font-weight: 800; letter-spacing: -0.5px;">BrightSmile Health & Dental</h1>
                <p style="color: #64748b; font-size: 14px; margin: 6px 0 0 0;">Official Consultation Confirmation</p>
            </div>

            <div style="padding: 24px 0; color: #1e293b; line-height: 1.6;">
                <p style="font-size: 16px;">Dear <strong>{patient_name}</strong>,</p>
                <p style="font-size: 14px; color: #475569;">
                    We are pleased to confirm your upcoming appointment at <strong>BrightSmile Health & Dental Clinic</strong>.
                    Our clinical team is prepared to provide you with personalized, top-tier wellness care.
                </p>

                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; margin: 20px 0;">
                    <div style="font-size: 12px; font-weight: 700; text-transform: uppercase; color: #0d9488; letter-spacing: 0.5px; margin-bottom: 12px;">
                        Appointment Details
                    </div>
                    <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                        <tr>
                            <td style="padding: 8px 0; color: #64748b; width: 140px;"><strong>📅 Scheduled Time:</strong></td>
                            <td style="padding: 8px 0; color: #0f172a; font-weight: 700; font-size: 15px; color: #0f766e;">{date_time} (30 mins)</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #64748b;"><strong>🩺 Attending Doctor:</strong></td>
                            <td style="padding: 8px 0; color: #0f172a; font-weight: 600;">{doctor_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #64748b;"><strong>🦷 Consultation Type:</strong></td>
                            <td style="padding: 8px 0; color: #0f172a;">{service}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #64748b;"><strong>🏥 Clinic Location:</strong></td>
                            <td style="padding: 8px 0; color: #0f172a;">123 Healthcare Plaza, Suite 400</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #64748b;"><strong>📞 Patient Contact:</strong></td>
                            <td style="padding: 8px 0; color: #0f172a;">{phone}</td>
                        </tr>
                    </table>
                </div>

                <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 10px; padding: 14px 18px; margin-bottom: 20px;">
                    <h4 style="margin: 0 0 6px 0; color: #166534; font-size: 13px;">📋 Quick Preparation Guide:</h4>
                    <ul style="margin: 0; padding-left: 20px; font-size: 13px; color: #166534; line-height: 1.5;">
                        <li>Please arrive 10 minutes prior to your time for seamless registration.</li>
                        <li>Bring a valid photo ID and insurance information if applicable.</li>
                        <li>If you need to reschedule or cancel, kindly give at least 24 hours notice.</li>
                    </ul>
                </div>

                <p style="font-size: 13px; color: #64748b;">
                    Need assistance or directions? Call our front desk directly at <strong>(555) 019-2831</strong> or reply to this email.
                </p>

                <p style="margin-top: 24px; font-size: 14px;">
                    Warm regards,<br>
                    <strong>The BrightSmile Clinical & Care Team</strong>
                </p>
            </div>

            <div style="border-top: 1px solid #f1f5f9; padding-top: 14px; text-align: center; font-size: 11px; color: #94a3b8;">
                BrightSmile Dental Clinic • 123 Healthcare Plaza, Suite 400 • Dedicated Patient Care
            </div>
        </div>
        """
        return await self.send_email(
            to_addr=to_addr,
            subject=subject,
            body=html_body,
            is_html=True
        )
