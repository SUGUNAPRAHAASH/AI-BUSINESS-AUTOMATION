import uuid
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from app.models import InvoiceExtractionResponse
from app.features.extraction import extract_text_from_pdf_or_bytes, parse_and_validate_invoice
from app.db import execute, fetch_all, insert_mock_outbox
from app.security import verify_api_key

router = APIRouter(prefix="/v1/documents", tags=["Document Extraction"])


@router.post("/extract", response_model=InvoiceExtractionResponse, dependencies=[Depends(verify_api_key)])
async def extract_document_endpoint(
    file: UploadFile = File(...)
):
    """
    Extract structured data from invoices and forms.
    Validates mathematical consistency: sum(items) == subtotal, subtotal + tax == total.
    """
    content_bytes = await file.read()
    raw_text = extract_text_from_pdf_or_bytes(content_bytes)
    data = parse_and_validate_invoice(raw_text)

    doc_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    await execute(
        "INSERT INTO extracted_documents (id, tenant_id, filename, doc_type, data, confidence, validation_errors, created_at) "
        "VALUES (?, 'a0000000-0000-0000-0000-000000000001', ?, 'invoice', ?, ?, ?, ?)",
        (doc_id, file.filename, json.dumps(data), data["confidence"], json.dumps(data["validation_errors"]), now_iso)
    )

    # Append to Google Sheets mock outbox
    await insert_mock_outbox("sheets", "append_invoice_row", {
        "invoice_number": data["invoice_number"],
        "vendor": data["vendor_name"],
        "total": data["total"],
        "confidence": data["confidence"]
    })

    data["id"] = doc_id
    return InvoiceExtractionResponse(**data)


@router.get("", dependencies=[Depends(verify_api_key)])
async def list_extracted_documents():
    """List recent extracted documents for the dashboard."""
    rows = await fetch_all("SELECT * FROM extracted_documents ORDER BY created_at DESC LIMIT 50")
    results = []
    for r in rows:
        parsed_data = json.loads(r["data"]) if isinstance(r["data"], str) else r["data"]
        val_errors = json.loads(r["validation_errors"]) if isinstance(r["validation_errors"], str) else r["validation_errors"]
        results.append({
            "id": r["id"],
            "filename": r["filename"],
            "doc_type": r["doc_type"],
            "data": parsed_data,
            "confidence": r["confidence"],
            "validation_errors": val_errors,
            "created_at": r["created_at"]
        })
    return {"documents": results, "total": len(results)}
