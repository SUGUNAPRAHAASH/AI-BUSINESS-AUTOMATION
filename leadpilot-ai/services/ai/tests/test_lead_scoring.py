import pytest
from app.features.lead_scoring import score_lead_deterministic

CASES = [
    # 1. Hot: Invisalign with contact and timeline
    ("I'm interested in Invisalign, my name is Priya Nair, priya@example.com, start next month, budget 4000", "hot"),
    # 2. Hot: Dental implants urgent booking
    ("I need to book dental implants ASAP, call me at 555-123-4567, ready to start this month", "hot"),
    # 3. Hot: Teeth whitening booking tomorrow
    ("Can I schedule teeth whitening tomorrow? My email is mark@test.com", "hot"),
    # 4. Hot: Emergency tooth extraction appointment request
    ("I have severe tooth pain and want to book an appointment today, phone 555-987-6543", "hot"),
    # 5. Hot: Crowns with phone number and near timeline
    ("Looking for 2 ceramic crowns within 30 days, reach me at david@clinic.org", "hot"),

    # 6. Warm: Specific interest but no timeline or contact
    ("How does Invisalign compare to braces?", "warm"),
    # 7. Warm: Interest with budget but no contact details
    ("Interested in full porcelain veneers with a budget of 5000", "warm"),
    # 8. Warm: Contact info provided but general inquiry
    ("Hello, my email is sarah@sample.com, do you accept Guardian insurance?", "warm"),
    # 9. Warm: Distant timeline
    ("I might get dental implants next year, reach me at test@example.com", "warm"),

    # 10. Cold: General browsing
    ("What are your clinic opening hours on Wednesday?", "cold"),
    # 11. Cold: Price question with no details
    ("How much is a basic checkup?", "cold"),
    # 12. Cold: Off-topic / smalltalk
    ("Do you offer free parking near the subway?", "cold"),
]


@pytest.mark.parametrize("text,expected_score", CASES)
def test_lead_scoring_rubric(text, expected_score):
    result = score_lead_deterministic(text)
    assert result["score"] == expected_score, f"Expected {expected_score} but got {result['score']} for text: {text}"
    assert len(result["score_reason"]) <= 200
    assert len(result["summary"]) <= 300
    assert result["next_best_action"] != ""
