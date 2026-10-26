import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def create_invoice_pdf(filename: str, vendor: str, inv_number: str, date: str, items: list, subtotal: float, tax: float, total: float):
    output_dir = Path(__file__).resolve().parent.parent / "samples" / "invoices"
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / filename

    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, f"INVOICE — {vendor}")

    c.setFont("Helvetica", 10)
    c.drawString(50, 725, f"Invoice #: {inv_number}")
    c.drawString(50, 710, f"Invoice Date: {date}")
    c.drawString(50, 695, f"Due Date: 2026-11-15")
    c.drawString(50, 680, "Billed To: BrightSmile Dental, 742 Evergreen Medical Suites")

    c.line(50, 665, 550, 665)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, 650, "Item Description | Qty | Unit Price | Amount")
    c.line(50, 640, 550, 640)

    y = 620
    c.setFont("Helvetica", 10)
    for desc, qty, price, amt in items:
        line_str = f"{desc} | {qty} | ${price:.2f} | ${amt:.2f}"
        c.drawString(50, y, line_str)
        y -= 20

    c.line(50, y, 550, y)
    y -= 20
    c.drawString(350, y, f"Subtotal: ${subtotal:.2f}")
    y -= 15
    c.drawString(350, y, f"Tax: ${tax:.2f}")
    y -= 15
    c.setFont("Helvetica-Bold", 11)
    c.drawString(350, y, f"Total: ${total:.2f}")

    c.save()
    print(f"Generated invoice PDF: {pdf_path}")


def main():
    # 1. Standard Dental Supplies Invoice
    create_invoice_pdf(
        "invoice_01_supplies.pdf",
        "Dental Supplies Direct Inc.",
        "INV-2026-0891",
        "2026-10-15",
        [
            ("Dental Bibs Premium 500ct", 2, 45.00, 90.00),
            ("Sterilization Pouches 200ct", 4, 35.00, 140.00),
            ("Prophy Paste Mint Single-Dose 200ct", 2, 110.00, 220.00)
        ],
        subtotal=450.00,
        tax=36.00,
        total=486.00
    )

    # 2. Lab Restoration Invoice
    create_invoice_pdf(
        "invoice_02_lab_work.pdf",
        "Apex Aesthetic Dental Laboratories",
        "LAB-9921",
        "2026-10-20",
        [
            ("Custom Zirconia Crown Milling (Tooth #19)", 1, 380.00, 380.00),
            ("Porcelain Veneer Layering (Tooth #8)", 1, 420.00, 420.00)
        ],
        subtotal=800.00,
        tax=64.00,
        total=864.00
    )

    # 3. Surgical Consumables Invoice
    create_invoice_pdf(
        "invoice_03_surgical.pdf",
        "Precision Surgical Supply LLC",
        "SURG-4412",
        "2026-10-22",
        [
            ("Surgical Sutures 4-0 Silk 12pk", 3, 40.00, 120.00),
            ("Bone Graft Mineral Matrix 0.5cc", 2, 180.00, 360.00)
        ],
        subtotal=480.00,
        tax=38.40,
        total=518.40
    )


if __name__ == "__main__":
    main()
