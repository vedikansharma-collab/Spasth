import sys
from pathlib import Path
import fitz
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import app

client = TestClient(app)

def test_upload_bill_pdf_and_math_model_calculation():
    """
    Integration test:
    1. Upload a bill PDF -> extract total amount, procedure, non-covered items
    2. Feed extracted parameters into the mathematical model (/api/estimate/calculate-claim)
    3. Verify deterministic financial breakdown (deductible, copay, customer payable, insurer payable)
    """
    # 1. Generate an in-memory test hospital bill PDF
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), """
    SAHYADRI SUPER SPECIALITY HOSPITAL
    Bill No: SSH-2026-9901
    Date: 11-Oct-2026
    Patient Name: Rahul Sharma
    Procedure: Appendectomy
    City: Pune
    Room Category: Standard

    Hospital Room Charges: Rs. 15,000
    Operation Theatre & Surgery: Rs. 50,000
    Medicines & Pharmacy: Rs. 15,000
    PPE, Sanitizer & Consumables: Rs. 2,000
    Administrative & File Fee: Rs. 1,000

    Total Bill Amount: Rs. 83,000
    Net Payable: Rs. 83,000
    """)
    pdf_bytes = doc.tobytes()
    doc.close()

    # 2. Upload to /api/estimate/upload-bill
    upload_res = client.post(
        "/api/estimate/upload-bill",
        files={"file": ("test_hospital_bill.pdf", pdf_bytes, "application/pdf")}
    )
    assert upload_res.status_code == 200, f"Upload failed: {upload_res.text}"
    bill_data = upload_res.json()

    assert bill_data["status"] == "SUCCESS"
    assert bill_data["total_amount"] == 83000.0
    assert bill_data["non_covered_amount"] == 3000.0  # 2000 consumables + 1000 admin fee
    assert bill_data["detected_procedure"] == "Appendectomy"
    assert "SAHYADRI" in bill_data["hospital_name"]
    assert bill_data["bill_number"] == "SSH-2026-9901"

    # 3. Compute Out-of-Pocket Estimate with Math Model
    # Example policy: Sum Insured = 500,000, Co-pay = 10%, Deductible = 0
    math_payload = {
        "procedure_name": bill_data["detected_procedure"],
        "treatment_cost": bill_data["total_amount"],
        "quantity": 1,
        "non_covered_expense": bill_data["non_covered_amount"],
        "sum_insured": 500000.0,
        "copay_percent": 10.0,
        "deductible": 0.0,
        "cost_mode": "actual",
        "use_actual_cost": True
    }

    claim_res = client.post("/api/estimate/calculate-claim", json=math_payload)
    assert claim_res.status_code == 200, f"Math calculation failed: {claim_res.text}"
    calc_data = claim_res.json()

    assert calc_data["status"] == "SUCCESS"
    assert calc_data["total_expense"] == 83000.0
    # Total = 83,000, Non-covered = 3,000 -> Eligible = 80,000
    assert calc_data["eligible_amount"] == 80000.0
    # Co-pay 10% on 80,000 = 8,000
    assert calc_data["customer_payable_breakdown"]["co_payment"] == 8000.0
    assert calc_data["customer_payable_breakdown"]["non_covered_expense"] == 3000.0
    # Insurer payable = 80,000 - 8,000 = 72,000
    assert calc_data["insurer_payable"] == 72000.0
    # Customer payable = 3,000 (non-covered) + 8,000 (copay) = 11,000
    assert calc_data["customer_payable"] == 11000.0
    assert round(calc_data["insurer_payable"] + calc_data["customer_payable"], 2) == 83000.0
    assert calc_data["treatment_cost_source"] == "USER_PROVIDED"
    assert len(calc_data["calculation_trace"]) > 0


def test_upload_bill_validation_errors():
    """Verify non-PDF and empty files are rejected."""
    # Non-PDF rejection
    res1 = client.post(
        "/api/estimate/upload-bill",
        files={"file": ("bill.txt", b"Total: 50000", "text/plain")}
    )
    assert res1.status_code == 400
    assert "Only PDF" in res1.json()["detail"]

    # Empty PDF rejection
    res2 = client.post(
        "/api/estimate/upload-bill",
        files={"file": ("empty.pdf", b"", "application/pdf")}
    )
    assert res2.status_code == 400
    assert "empty" in res2.json()["detail"].lower()
