from app.features.extraction import parse_and_validate_invoice


def test_invoice_mathematical_validation_success():
    sample_text = """
    Vendor: Dental Supplies Direct Inc.
    Invoice #: INV-2026-0891
    Invoice Date: 2026-10-15
    Due Date: 2026-11-15
    Dental Bibs Premium 500ct | 2 | 45.00 | 90.00
    Sterilization Pouches 200ct | 4 | 35.00 | 140.00
    Prophy Paste Mint Single-Dose 200ct | 2 | 110.00 | 220.00
    Subtotal: $450.00
    Tax: $36.00
    Total: $486.00
    """
    res = parse_and_validate_invoice(sample_text)
    assert res["invoice_number"] == "INV-2026-0891"
    assert res["subtotal"] == 450.00
    assert res["tax"] == 36.00
    assert res["total"] == 486.00
    assert len(res["validation_errors"]) == 0
    assert res["confidence"] >= 0.90


def test_invoice_mathematical_mismatch_detection():
    # Intentionally corrupted total
    sample_text = """
    Vendor: Faulty Supplies Inc.
    Invoice #: INV-BAD-123
    Invoice Date: 2026-10-15
    Item A | 1 | 100.00 | 100.00
    Subtotal: $100.00
    Tax: $10.00
    Total: $250.00
    """
    res = parse_and_validate_invoice(sample_text)
    assert len(res["validation_errors"]) > 0
    assert res["confidence"] < 0.90
