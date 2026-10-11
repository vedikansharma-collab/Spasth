import os
import sys
import uuid
from datetime import timedelta
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import app
from app.database.session import SessionLocal
from app.models.user import User
from app.models.policy import Policy, PolicyPage, PolicyRule, PolicyChunk
from app.core.security import hash_password, verify_password, create_access_token
from app.core.config import settings

client = TestClient(app)

# Track created test entities for guaranteed teardown
CLEANUP_USER_EMAILS = set()
CLEANUP_POLICY_IDS = set()

@pytest.fixture(autouse=True)
def cleanup_tracker():
    yield
    # Teardown: Remove any test users/policies created during test
    db = SessionLocal()
    try:
        if CLEANUP_POLICY_IDS:
            db.query(PolicyChunk).filter(PolicyChunk.policy_id.in_(list(CLEANUP_POLICY_IDS))).delete(synchronize_session=False)
            db.query(PolicyRule).filter(PolicyRule.policy_id.in_(list(CLEANUP_POLICY_IDS))).delete(synchronize_session=False)
            db.query(PolicyPage).filter(PolicyPage.policy_id.in_(list(CLEANUP_POLICY_IDS))).delete(synchronize_session=False)
            db.query(Policy).filter(Policy.id.in_(list(CLEANUP_POLICY_IDS))).delete(synchronize_session=False)
            CLEANUP_POLICY_IDS.clear()
        if CLEANUP_USER_EMAILS:
            db.query(User).filter(User.email.in_(list(CLEANUP_USER_EMAILS))).delete(synchronize_session=False)
            CLEANUP_USER_EMAILS.clear()
        db.commit()
    except Exception as e:
        db.rollback()
    finally:
        db.close()


def create_test_user(email: str, password: str = "Password123!", role: str = "user", is_active: bool = True) -> User:
    CLEANUP_USER_EMAILS.add(email.lower())
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email.lower()).first()
        if user:
            user.password_hash = hash_password(password)
            user.role = role
            user.is_active = is_active
            db.commit()
            db.refresh(user)
            return user

        user = User(
            id=str(uuid.uuid4()),
            email=email.lower(),
            password_hash=hash_password(password),
            role=role,
            is_active=is_active
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def create_test_policy(owner_id: str = None, is_public: bool = False) -> str:
    pol_id = f"test_pol_{uuid.uuid4().hex[:8]}"
    CLEANUP_POLICY_IDS.add(pol_id)
    db = SessionLocal()
    try:
        policy = Policy(
            id=pol_id,
            filename=f"{pol_id}_sample.pdf",
            original_filename="sample.pdf",
            file_path=f"uploads/{pol_id}_sample.pdf",
            file_size_bytes=1024,
            page_count=2,
            extraction_status="SUCCESS",
            owner_id=owner_id,
            is_public=is_public
        )
        db.add(policy)

        # Add page
        page = PolicyPage(
            policy_id=pol_id,
            page_number=1,
            char_count=100,
            word_count=20,
            content="Sample test page content for policy."
        )
        db.add(page)

        # Add rule
        rule = PolicyRule(
            policy_id=pol_id,
            rule_type="CO_PAYMENT",
            rule_key="CO_PAYMENT",
            value="10",
            unit="PERCENT",
            page=1,
            clause="Clause 4.1",
            source_text="10% co-payment applies.",
            confidence="HIGH",
            status="VERIFIED"
        )
        db.add(rule)
        db.commit()
        return pol_id
    finally:
        db.close()


# ==============================================================================
# TESTS A - E: REGISTRATION & PASSWORD HASHING
# ==============================================================================

def test_A_registration_success():
    email = f"test_user_{uuid.uuid4().hex[:6]}@example.com"
    CLEANUP_USER_EMAILS.add(email)
    res = client.post("/api/auth/register", json={"email": email, "password": "SecurePassword123!"})
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == email
    assert data["user"]["role"] == "user"
    assert "password_hash" not in data["user"]
    assert "password" not in data["user"]


def test_B_duplicate_email_rejection():
    email = f"dup_{uuid.uuid4().hex[:6]}@example.com"
    create_test_user(email=email, password="Password123!")
    res = client.post("/api/auth/register", json={"email": email, "password": "NewPassword123!"})
    assert res.status_code == 400
    assert "already exists" in res.json()["detail"].lower()


def test_C_invalid_registration_input():
    # Password too short (< 8 chars)
    res = client.post("/api/auth/register", json={"email": "valid@example.com", "password": "short"})
    assert res.status_code == 422

    # Invalid email format
    res2 = client.post("/api/auth/register", json={"email": "not-an-email", "password": "ValidPassword123!"})
    assert res2.status_code == 422


def test_D_and_E_password_is_hashed_and_never_plaintext():
    pwd = "MySecretPassword123!"
    h = hash_password(pwd)
    assert h != pwd
    assert h.startswith("$2b$") or h.startswith("$2a$")
    assert verify_password(pwd, h) is True
    assert verify_password("WrongPassword!", h) is False

    # Check DB record
    email = f"hashcheck_{uuid.uuid4().hex[:6]}@example.com"
    u = create_test_user(email=email, password=pwd)
    db = SessionLocal()
    db_user = db.query(User).filter(User.id == u.id).first()
    assert db_user.password_hash != pwd
    assert pwd not in db_user.password_hash
    db.close()


# ==============================================================================
# TESTS F - I: LOGIN & CREDENTIAL VERIFICATION
# ==============================================================================

def test_F_login_success():
    email = f"login_{uuid.uuid4().hex[:6]}@example.com"
    pwd = "LoginPassword123!"
    create_test_user(email=email, password=pwd)

    res = client.post("/api/auth/login", json={"email": email, "password": pwd})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == email


def test_G_incorrect_password():
    email = f"wrongpwd_{uuid.uuid4().hex[:6]}@example.com"
    create_test_user(email=email, password="CorrectPassword123!")

    res = client.post("/api/auth/login", json={"email": email, "password": "WrongPassword999!"})
    assert res.status_code == 401
    assert "invalid email or password" in res.json()["detail"].lower()


def test_H_nonexistent_user():
    res = client.post("/api/auth/login", json={"email": "ghost_user_999@example.com", "password": "Password123!"})
    assert res.status_code == 401
    assert "invalid email or password" in res.json()["detail"].lower()


def test_I_inactive_user():
    email = f"inactive_{uuid.uuid4().hex[:6]}@example.com"
    create_test_user(email=email, password="Password123!", is_active=False)

    res = client.post("/api/auth/login", json={"email": email, "password": "Password123!"})
    assert res.status_code == 401
    assert "inactive" in res.json()["detail"].lower()


# ==============================================================================
# TESTS J - N: JWT CREATION, EXPIRATION, VALIDATION & /auth/me
# ==============================================================================

def test_J_jwt_generation():
    token = create_access_token({"sub": "u_123", "email": "test@example.com", "role": "user"})
    assert isinstance(token, str)
    assert len(token) > 20


def test_K_expired_jwt():
    # Token expired 10 minutes ago
    expired_token = create_access_token({"sub": "u_123"}, expires_delta=timedelta(minutes=-10))
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code == 401
    assert "expired" in res.json()["detail"].lower() or "invalid" in res.json()["detail"].lower()


def test_L_invalid_jwt():
    res = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.garbage.token"})
    assert res.status_code == 401


def test_M_missing_jwt():
    res = client.get("/api/auth/me")
    assert res.status_code == 401


def test_N_auth_me_endpoint():
    email = f"me_{uuid.uuid4().hex[:6]}@example.com"
    user = create_test_user(email=email)
    token = create_access_token({"sub": user.id})

    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == user.id
    assert data["email"] == email
    assert "password_hash" not in data


# ==============================================================================
# TESTS O - S: POLICY OWNERSHIP & ACCESS AUTHORIZATION
# ==============================================================================

def test_O_private_policy_owner_access():
    user = create_test_user(f"owner_{uuid.uuid4().hex[:6]}@example.com")
    policy_id = create_test_policy(owner_id=user.id, is_public=False)
    token = create_access_token({"sub": user.id})

    res = client.get(f"/api/policies/{policy_id}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["id"] == policy_id


def test_P_private_policy_non_owner_denial():
    user_a = create_test_user(f"owner_a_{uuid.uuid4().hex[:6]}@example.com")
    user_b = create_test_user(f"intruder_b_{uuid.uuid4().hex[:6]}@example.com")
    policy_a = create_test_policy(owner_id=user_a.id, is_public=False)

    token_b = create_access_token({"sub": user_b.id})

    # User B attempting to access User A's policy
    res = client.get(f"/api/policies/{policy_a}", headers={"Authorization": f"Bearer {token_b}"})
    assert res.status_code == 403
    assert "permission" in res.json()["detail"].lower() or "access denied" in res.json()["detail"].lower()


def test_Q_public_policy_access():
    policy_id = create_test_policy(owner_id=None, is_public=True)

    # Unauthenticated access to public policy MUST succeed
    res = client.get(f"/api/policies/{policy_id}")
    assert res.status_code == 200
    assert res.json()["id"] == policy_id


def test_R_nonexistent_policy():
    res = client.get("/api/policies/nonexistent_policy_999999")
    assert res.status_code == 404


def test_S_arbitrary_owner_id_cannot_be_supplied_by_client():
    # Attempt to upload with forged owner_id
    user = create_test_user(f"upload_owner_{uuid.uuid4().hex[:6]}@example.com")
    token = create_access_token({"sub": user.id})
    victim_user = create_test_user(f"victim_{uuid.uuid4().hex[:6]}@example.com")

    # In upload, the server derives ownership exclusively from token, ignoring any forged owner_id payload
    sample_pdf = backend_dir.parent / "data" / "sample_policies" / "sample_health_policy.pdf"
    if sample_pdf.exists():
        with open(sample_pdf, "rb") as f:
            res = client.post(
                "/api/policies/upload",
                headers={"Authorization": f"Bearer {token}"},
                data={"owner_id": victim_user.id},  # Attempt client override
                files={"file": ("sample.pdf", f, "application/pdf")}
            )
        assert res.status_code == 201
        uploaded_id = res.json()["policy_id"]
        CLEANUP_POLICY_IDS.add(uploaded_id)

        # Verify owner_id in database belongs to authenticated user, NOT victim
        db = SessionLocal()
        p = db.query(Policy).filter(Policy.id == uploaded_id).first()
        assert p.owner_id == user.id
        assert p.owner_id != victim_user.id
        db.close()


# ==============================================================================
# TESTS U - W: CROSS-USER ISOLATION & RAG ACCESS CONTROL
# ==============================================================================

def test_U_and_V_cross_user_policy_and_rag_access_blocked():
    user_a = create_test_user(f"usera_{uuid.uuid4().hex[:6]}@example.com")
    user_b = create_test_user(f"userb_{uuid.uuid4().hex[:6]}@example.com")

    policy_a = create_test_policy(owner_id=user_a.id, is_public=False)
    policy_b = create_test_policy(owner_id=user_b.id, is_public=False)

    token_a = create_access_token({"sub": user_a.id})
    token_b = create_access_token({"sub": user_b.id})

    # User A asks question on Policy B -> MUST be blocked with 403
    res_rag = client.post(
        f"/api/policies/{policy_b}/ask",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"query": "What is the deductible?"}
    )
    assert res_rag.status_code == 403, f"Expected 403 for cross-user RAG, got {res_rag.status_code}"

    # User B asks question on Policy A -> MUST be blocked with 403
    res_rag_b = client.post(
        f"/api/policies/{policy_a}/ask",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"query": "What is the copay?"}
    )
    assert res_rag_b.status_code == 403

    # Unauthenticated query on private policy -> MUST be blocked with 401
    res_unauth = client.post(
        f"/api/policies/{policy_a}/ask",
        json={"query": "What is the copay?"}
    )
    assert res_unauth.status_code == 401


# ==============================================================================
# TESTS X - AC: SUB-RESOURCE & ENDPOINT AUTHORIZATION (PAGES, CANONICAL, RULES)
# ==============================================================================

def test_X_and_AB_policy_pages_authorization():
    owner = create_test_user(f"pages_owner_{uuid.uuid4().hex[:6]}@example.com")
    intruder = create_test_user(f"pages_intruder_{uuid.uuid4().hex[:6]}@example.com")
    policy_id = create_test_policy(owner_id=owner.id, is_public=False)

    owner_token = create_access_token({"sub": owner.id})
    intruder_token = create_access_token({"sub": intruder.id})

    # Unauthenticated -> 401
    res_unauth = client.get(f"/api/policies/{policy_id}/pages/1")
    assert res_unauth.status_code == 401

    # Intruder -> 403
    res_intruder = client.get(f"/api/policies/{policy_id}/pages/1", headers={"Authorization": f"Bearer {intruder_token}"})
    assert res_intruder.status_code == 403

    # Owner -> 200
    res_owner = client.get(f"/api/policies/{policy_id}/pages/1", headers={"Authorization": f"Bearer {owner_token}"})
    assert res_owner.status_code == 200
    assert res_owner.json()["page_number"] == 1


def test_AA_canonical_policy_authorization():
    owner = create_test_user(f"canon_owner_{uuid.uuid4().hex[:6]}@example.com")
    intruder = create_test_user(f"canon_intruder_{uuid.uuid4().hex[:6]}@example.com")
    policy_id = create_test_policy(owner_id=owner.id, is_public=False)

    owner_token = create_access_token({"sub": owner.id})
    intruder_token = create_access_token({"sub": intruder.id})

    # Intruder requesting canonical JSON of private policy -> 403
    res_intruder = client.get(f"/api/policies/{policy_id}/canonical", headers={"Authorization": f"Bearer {intruder_token}"})
    assert res_intruder.status_code == 403


def test_Z_estimate_endpoint_authorization():
    owner = create_test_user(f"est_owner_{uuid.uuid4().hex[:6]}@example.com")
    intruder = create_test_user(f"est_intruder_{uuid.uuid4().hex[:6]}@example.com")
    policy_id = create_test_policy(owner_id=owner.id, is_public=False)

    owner_token = create_access_token({"sub": owner.id})
    intruder_token = create_access_token({"sub": intruder.id})

    payload = {
        "policy_id": policy_id,
        "procedure_name": "Appendectomy",
        "treatment_cost": 50000.0,
        "quantity": 1,
        "city": "Pune"
    }

    # Intruder running estimate on private policy -> 403
    res_intruder = client.post("/api/estimate/calculate-claim", headers={"Authorization": f"Bearer {intruder_token}"}, json=payload)
    assert res_intruder.status_code == 403

    # Unauthenticated running estimate on private policy -> 401
    res_unauth = client.post("/api/estimate/calculate-claim", json=payload)
    assert res_unauth.status_code == 401


def test_AD_role_enforcement_admin_access():
    user = create_test_user(f"user_regular_{uuid.uuid4().hex[:6]}@example.com", role="user")
    admin = create_test_user(f"admin_{uuid.uuid4().hex[:6]}@example.com", role="admin")

    policy_id = create_test_policy(owner_id=user.id, is_public=False)

    admin_token = create_access_token({"sub": admin.id})
    res_admin = client.get(f"/api/policies/{policy_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin.status_code == 200
    assert res_admin.json()["id"] == policy_id
