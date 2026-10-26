from app.security import mask_pii


def test_mask_credit_card():
    text = "My card number is 4111 2222 3333 4444 and my cvv is 123"
    masked = mask_pii(text)
    assert "4111 2222 3333 4444" not in masked
    assert "[MASKED_CARD:" in masked
    assert "4444" in masked  # last 4 digits visible


def test_mask_ssn():
    text = "Patient SSN is 123-45-6789 for dental insurance records"
    masked = mask_pii(text)
    assert "123-45-6789" not in masked
    assert "[MASKED_SSN]" in masked


def test_clean_text_unaltered():
    text = "I would like to inquire about teeth whitening fees"
    masked = mask_pii(text)
    assert masked == text
