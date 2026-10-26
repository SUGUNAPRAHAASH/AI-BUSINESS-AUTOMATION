import pytest
from app.features.email_triage import triage_email

EMAIL_CASES = [
    # 1. Appointment rescheduling
    ("msg_1", "p@ex.com", "Reschedule my Friday cleaning", "Please move my Friday cleaning to next Tuesday", "appointment", False),
    # 2. Sales lead inquiry
    ("msg_2", "l@ex.com", "Invisalign quote and pricing", "I am interested in getting Invisalign next month", "sales", False),
    # 3. Billing question
    ("msg_3", "b@ex.com", "Question regarding invoice INV-202", "Can you explain the charge on my latest receipt?", "billing", False),
    # 4. Spam email
    ("msg_4", "s@ex.com", "Claim your free casino lottery winnings", "Click here to claim $1,000,000 lottery cash prize", "spam", False),
    # 5. Dissatisfaction / complaint (needs_human=True)
    ("msg_5", "a@ex.com", "Horrible experience - calling lawyer", "I am extremely unhappy with the procedure and will sue for malpractice", "support", True),
    # 6. Refund demand (needs_human=True)
    ("msg_6", "r@ex.com", "Demand full refund", "You overcharged my credit card, refund my money immediately", "billing", True),
    # 7. Acute clinical symptoms (needs_human=True)
    ("msg_7", "m@ex.com", "Emergency - severe pain and swelling", "I had an extraction and now have severe pain, fever, and a swollen face", "support", True),
    # 8. Routine general support
    ("msg_8", "g@ex.com", "Parking validation question", "Where do I validate my underground parking ticket?", "support", False),
    # 9. Appointment booking request
    ("msg_9", "c@ex.com", "Book an appointment for Saturday", "Can I book a cleaning on Saturday morning?", "appointment", False),
    # 10. Spam crypto pitch
    ("msg_10", "sp@ex.com", "Crypto investment doubling scheme", "Buy bitcoin today and double your crypto", "spam", False),
]


@pytest.mark.parametrize("msg_id,from_addr,subject,body,expected_cat,expected_human", EMAIL_CASES)
def test_email_triage_rules(msg_id, from_addr, subject, body, expected_cat, expected_human):
    res = triage_email(msg_id, from_addr, subject, body)
    assert res["category"] == expected_cat
    if expected_human:
        assert res["needs_human"] is True
        assert res["priority"] == "high"
