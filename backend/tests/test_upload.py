import os
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print("Health check endpoint test PASSED!")

def test_pdf_upload_and_page_extraction():
    sample_pdf = backend_dir.parent / "data" / "sample_policies" / "sample_health_policy.pdf"
    assert sample_pdf.exists(), "Sample PDF does not exist!"

    with open(sample_pdf, "rb") as f:
        response = client.post(
            "/api/policies/upload",
            files={"file": ("sample_health_policy.pdf", f, "application/pdf")}
        )

    assert response.status_code == 201, f"Upload failed: {response.text}"
    data = response.json()
    assert "policy_id" in data
    assert data["page_count"] == 3
    assert data["extraction_status"] == "SUCCESS"
    policy_id = data["policy_id"]
    print(f"Policy uploaded successfully! ID: {policy_id}, Page count: {data['page_count']}")

    # Retrieve policy details
    detail_res = client.get(f"/api/policies/{policy_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert len(detail_data["pages"]) == 3

    # Check page numbers preservation
    for idx, page in enumerate(detail_data["pages"]):
        expected_page_num = idx + 1
        assert page["page_number"] == expected_page_num
        assert len(page["content"]) > 0
        print(f"Page {page['page_number']} preserved! Words: {page['word_count']}, Chars: {page['char_count']}")

    print("Page-wise extraction & page number preservation tests PASSED!")

if __name__ == "__main__":
    test_health_endpoint()
    test_pdf_upload_and_page_extraction()
