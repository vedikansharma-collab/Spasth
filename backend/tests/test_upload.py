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

    # 1. Register temporary test user
    test_email = "upload_test_user@example.com"
    test_pwd = "UploadPassword123!"
    reg_res = client.post("/api/auth/register", json={"email": test_email, "password": test_pwd})
    if reg_res.status_code == 201:
        token = reg_res.json()["access_token"]
        user_id = reg_res.json()["user"]["id"]
    else:
        login_res = client.post("/api/auth/login", json={"email": test_email, "password": test_pwd})
        token = login_res.json()["access_token"]
        user_id = login_res.json()["user"]["id"]

    auth_headers = {"Authorization": f"Bearer {token}"}

    # 2. Verify unauthenticated upload is rejected
    with open(sample_pdf, "rb") as f:
        unauth_upload = client.post(
            "/api/policies/upload",
            files={"file": ("sample_health_policy.pdf", f, "application/pdf")}
        )
    assert unauth_upload.status_code == 401, f"Expected 401 for unauth upload, got: {unauth_upload.status_code}"

    policy_id = None
    try:
        with open(sample_pdf, "rb") as f:
            response = client.post(
                "/api/policies/upload",
                headers=auth_headers,
                files={"file": ("sample_health_policy.pdf", f, "application/pdf")}
            )

        assert response.status_code == 201, f"Upload failed: {response.text}"
        data = response.json()
        assert "policy_id" in data
        assert data["page_count"] == 3
        assert data["extraction_status"] == "SUCCESS"
        policy_id = data["policy_id"]
        print(f"Policy uploaded successfully! ID: {policy_id}, Page count: {data['page_count']}")

        # 3. Retrieve policy details unauthenticated -> must fail with 401
        unauth_detail = client.get(f"/api/policies/{policy_id}")
        assert unauth_detail.status_code == 401

        # 4. Retrieve policy details with authenticated owner -> must succeed with 200
        detail_res = client.get(f"/api/policies/{policy_id}", headers=auth_headers)
        assert detail_res.status_code == 200
        detail_data = detail_res.json()
        assert len(detail_data["pages"]) == 3
        assert detail_data.get("owner_id") == user_id

        # Check page numbers preservation
        for idx, page in enumerate(detail_data["pages"]):
            expected_page_num = idx + 1
            assert page["page_number"] == expected_page_num
            assert len(page["content"]) > 0

        print("Page-wise extraction & authenticated ownership tests PASSED!")
    finally:
        from app.database.session import SessionLocal
        from app.models.policy import Policy, PolicyPage, PolicyRule, PolicyChunk
        from app.models.user import User

        cleanup_db = SessionLocal()
        try:
            if policy_id:
                cleanup_db.query(PolicyChunk).filter(PolicyChunk.policy_id == policy_id).delete()
                cleanup_db.query(PolicyRule).filter(PolicyRule.policy_id == policy_id).delete()
                cleanup_db.query(PolicyPage).filter(PolicyPage.policy_id == policy_id).delete()
                cleanup_db.query(Policy).filter(Policy.id == policy_id).delete()
            cleanup_db.query(User).filter(User.email == test_email).delete()
            cleanup_db.commit()
        except Exception as e:
            cleanup_db.rollback()
            print(f"Warning: Cleanup failed: {e}")
        finally:
            cleanup_db.close()

        if policy_id:
            for f in (backend_dir / "uploads").glob(f"{policy_id}_*"):
                try:
                    f.unlink()
                except Exception:
                    pass

if __name__ == "__main__":
    test_health_endpoint()
    test_pdf_upload_and_page_extraction()
