import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import app
from app.database.db import init_db

client = TestClient(app)

def setup_module(module):
    init_db()

CANONICAL_POLICY_ID = "945c5b0b-c71e-4e0b-abf0-ed0211b93052"

# ==============================================================================
# PHASE 9 & 12: COMPREHENSIVE ENDPOINT INTEGRATION TESTS
# ==============================================================================

def test_api_case_1_no_deductions():
    """CASE 1: Treatment cost = ₹100,000, No deductions, SI = ₹500,000"""
    payload = {
        "procedure_name": "General Consultation",
        "treatment_cost": 100000.0,
        "quantity": 1,
        "sum_insured": 500000.0,
        "copay_percent": 0.0,
        "deductible": 0.0,
        "treatment_sublimit": None,
        "non_covered_expense": 0.0
    }
    response = client.post("/api/estimate/calculate-claim", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["total_expense"] == 100000.0
    assert data["eligible_amount"] == 100000.0
    assert data["insurer_payable"] == 100000.0
    assert data["customer_payable"] == 0.0
    assert round(data["insurer_payable"] + data["customer_payable"], 2) == 100000.0
    assert data["remaining_sum_insured"] == 400000.0
    assert len(data["calculation_trace"]) > 0


def test_api_case_2_copay_10_percent():
    """CASE 2: Treatment cost = ₹100,000, Co-pay = 10%, SI = ₹500,000"""
    payload = {
        "procedure_name": "General Procedure",
        "treatment_cost": 100000.0,
        "quantity": 1,
        "sum_insured": 500000.0,
        "copay_percent": 10.0,
        "deductible": 0.0,
        "non_covered_expense": 0.0
    }
    response = client.post("/api/estimate/calculate-claim", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["total_expense"] == 100000.0
    assert data["insurer_payable"] == 90000.0
    assert data["customer_payable"] == 10000.0
    assert data["customer_payable_breakdown"]["co_payment"] == 10000.0
    assert round(data["insurer_payable"] + data["customer_payable"], 2) == 100000.0


def test_api_case_3_sublimit_and_copay():
    """CASE 3: Treatment cost = ₹100,000, Sublimit = ₹80,000, Co-pay = 10%, SI = ₹500,000"""
    payload = {
        "procedure_name": "Sublimit Procedure",
        "treatment_cost": 100000.0,
        "quantity": 1,
        "sum_insured": 500000.0,
        "treatment_sublimit": 80000.0,
        "copay_percent": 10.0
    }
    response = client.post("/api/estimate/calculate-claim", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["total_expense"] == 100000.0
    # Sublimit excess = 20,000 -> eligible = 80,000
    # Co-pay 10% on 80,000 = 8,000
    # Insurer = 72,000, Customer = 20,000 + 8,000 = 28,000
    assert data["customer_payable_breakdown"]["sublimit_excess"] == 20000.0
    assert data["customer_payable_breakdown"]["co_payment"] == 8000.0
    assert data["insurer_payable"] == 72000.0
    assert data["customer_payable"] == 28000.0
    assert round(data["insurer_payable"] + data["customer_payable"], 2) == 100000.0


def test_api_case_4_deductible_and_copay():
    """CASE 4: Treatment cost = ₹100,000, Deductible = ₹10,000, Co-pay = 10%, SI = ₹500,000"""
    payload = {
        "procedure_name": "Deductible Procedure",
        "treatment_cost": 100000.0,
        "quantity": 1,
        "sum_insured": 500000.0,
        "deductible": 10000.0,
        "copay_percent": 10.0
    }
    response = client.post("/api/estimate/calculate-claim", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    # Deductible = 10,000 -> base for copay = 90,000
    # Co-pay 10% = 9,000
    # Insurer = 81,000, Customer = 19,000
    assert data["customer_payable_breakdown"]["deductible"] == 10000.0
    assert data["customer_payable_breakdown"]["co_payment"] == 9000.0
    assert data["insurer_payable"] == 81000.0
    assert data["customer_payable"] == 19000.0
    assert round(data["insurer_payable"] + data["customer_payable"], 2) == 100000.0


def test_api_case_5_sublimit_deductible_and_copay():
    """CASE 5: Treatment cost = ₹100,000, Sublimit = ₹80,000, Deductible = ₹10,000, Co-pay = 10%, SI = ₹500,000"""
    payload = {
        "procedure_name": "Complex Procedure",
        "treatment_cost": 100000.0,
        "quantity": 1,
        "sum_insured": 500000.0,
        "treatment_sublimit": 80000.0,
        "deductible": 10000.0,
        "copay_percent": 10.0
    }
    response = client.post("/api/estimate/calculate-claim", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    # Sublimit excess: 20,000 -> eligible: 80,000
    # Deductible: 10,000 -> eligible: 70,000
    # Copay 10%: 7,000
    # Insurer: 63,000, Customer: 20k + 10k + 7k = 37,000
    assert data["customer_payable_breakdown"]["sublimit_excess"] == 20000.0
    assert data["customer_payable_breakdown"]["deductible"] == 10000.0
    assert data["customer_payable_breakdown"]["co_payment"] == 7000.0
    assert data["insurer_payable"] == 63000.0
    assert data["customer_payable"] == 37000.0
    assert round(data["insurer_payable"] + data["customer_payable"], 2) == 100000.0


def test_api_case_6_cost_exceeds_si():
    """CASE 6: Treatment cost exceeds Sum Insured."""
    payload = {
        "procedure_name": "Major Surgery",
        "treatment_cost": 600000.0,
        "sum_insured": 500000.0
    }
    response = client.post("/api/estimate/calculate-claim", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["insurer_payable"] == 500000.0
    assert data["customer_payable"] == 100000.0
    assert data["customer_payable_breakdown"]["sum_insured_excess"] == 100000.0
    assert data["remaining_sum_insured"] == 0.0


def test_api_case_7_remaining_si_depleted():
    """CASE 7: Remaining Sum Insured is less than the claim."""
    payload = {
        "procedure_name": "Follow-up Care",
        "treatment_cost": 100000.0,
        "sum_insured": 500000.0,
        "remaining_sum_insured": 40000.0
    }
    response = client.post("/api/estimate/calculate-claim", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["insurer_payable"] == 40000.0
    assert data["customer_payable"] == 60000.0
    assert data["customer_payable_breakdown"]["sum_insured_excess"] == 60000.0
    assert data["remaining_sum_insured"] == 0.0


def test_api_case_8_policy_overrides_frontend_copay():
    """CASE 8: Policy has 0% co-pay, but frontend sends 10% co-pay -> Policy MUST override."""
    payload = {
        "policy_id": CANONICAL_POLICY_ID,
        "procedure_name": "Appendectomy",
        "treatment_cost": 100000.0,
        "copay_percent": 10.0  # Frontend untrusted parameter
    }
    response = client.post("/api/estimate/calculate-claim", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    # Canonical policy has 0% co-pay, Sum Insured ₹10,00,000
    # Customer should pay 0% co-pay
    assert data["customer_payable_breakdown"]["co_payment"] == 0.0
    assert data["insurer_payable"] == 100000.0
    assert data["customer_payable"] == 0.0


def test_api_case_9_non_covered_expense():
    """CASE 9: Non-covered expense exists."""
    payload = {
        "procedure_name": "Routine Surgery",
        "treatment_cost": 100000.0,
        "non_covered_expense": 15000.0,
        "copay_percent": 10.0,
        "sum_insured": 500000.0
    }
    response = client.post("/api/estimate/calculate-claim", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    # Non-covered = 15,000 -> eligible = 85,000
    # Copay 10% on 85,000 = 8,500
    # Insurer = 76,500
    # Customer = 15,000 + 8,500 = 23,500
    assert data["eligible_amount"] == 85000.0
    assert data["customer_payable_breakdown"]["non_covered_expense"] == 15000.0
    assert data["customer_payable_breakdown"]["co_payment"] == 8500.0
    assert data["insurer_payable"] == 76500.0
    assert data["customer_payable"] == 23500.0
    assert round(data["insurer_payable"] + data["customer_payable"], 2) == 100000.0


def test_api_case_10_room_rule_exists():
    """CASE 10: Room rule exists with proportionate deduction."""
    payload = {
        "procedure_name": "Inpatient Surgery",
        "treatment_cost": 100000.0,
        "room_penalty_ratio": 0.20,
        "sum_insured": 500000.0
    }
    response = client.post("/api/estimate/calculate-claim", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    # Room penalty = 20% on 100,000 = 20,000
    # Insurer = 80,000, Customer = 20,000
    assert data["customer_payable_breakdown"]["room_upgrade_excess"] == 20000.0
    assert data["insurer_payable"] == 80000.0
    assert data["customer_payable"] == 20000.0


def test_api_canonical_policy_cataract_sublimit():
    """Verify authoritative Cataract sublimit enforcement from canonical policy."""
    payload = {
        "policy_id": CANONICAL_POLICY_ID,
        "procedure_name": "Cataract Surgery",
        "treatment_cost": 100000.0
    }
    response = client.post("/api/estimate/calculate-claim", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    # Canonical policy has ₹40,000 sublimit for Cataract
    assert data["customer_payable_breakdown"]["sublimit_excess"] == 60000.0
    assert data["insurer_payable"] == 40000.0
    assert data["customer_payable"] == 60000.0


def test_api_benchmark_cost_resolution():
    """Verify automatic benchmark resolution when treatment_cost is omitted."""
    payload = {
        "procedure_name": "Appendectomy",
        "city": "Pune",
        "room_category": "Standard"
    }
    response = client.post("/api/estimate/calculate-claim", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    # Appendectomy in Pune benchmark range is 75000 - 95000 -> default midpoint 85000
    assert data["total_expense"] == 85000.0
    assert data["insurer_payable"] == 85000.0


def test_api_unrecognized_treatment_not_available():
    """Verify unknown treatment without explicit cost returns TREATMENT_COST_NOT_AVAILABLE."""
    payload = {
        "procedure_name": "Interstellar Quantum Replacement",
        "city": "Pune"
    }
    response = client.post("/api/estimate/calculate-claim", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "TREATMENT_COST_NOT_AVAILABLE"
    assert data["insurer_payable"] == 0.0
    assert data["customer_payable"] == 0.0


def test_api_invalid_negative_cost():
    """Verify negative cost returns INVALID_INPUT."""
    payload = {
        "procedure_name": "Appendectomy",
        "treatment_cost": -5000.0
    }
    response = client.post("/api/estimate/calculate-claim", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "INVALID_INPUT"


def test_api_invalid_zero_quantity():
    """Verify zero quantity returns INVALID_INPUT."""
    payload = {
        "procedure_name": "Appendectomy",
        "treatment_cost": 50000.0,
        "quantity": 0
    }
    response = client.post("/api/estimate/calculate-claim", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "INVALID_INPUT"


def test_dual_routing_support():
    """Verify both /api/estimate/calculate-claim and /api/calculate-claim work identically."""
    payload = {
        "procedure_name": "Appendectomy",
        "treatment_cost": 50000.0,
        "sum_insured": 500000.0
    }
    resp1 = client.post("/api/estimate/calculate-claim", json=payload)
    resp2 = client.post("/api/calculate-claim", json=payload)
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json()["total_expense"] == resp2.json()["total_expense"]
    assert resp1.json()["insurer_payable"] == resp2.json()["insurer_payable"]


def test_treatment_cost_source_classification():
    """Verify reference dataset vs user-provided cost source tagging."""
    # 1. Reference cost lookup
    ref_payload = {
        "procedure_name": "Appendectomy",
        "city": "Pune",
        "cost_mode": "reference"
    }
    resp_ref = client.post("/api/estimate/calculate-claim", json=ref_payload)
    assert resp_ref.status_code == 200
    data_ref = resp_ref.json()
    assert data_ref["treatment_cost_source"] == "REFERENCE_DATASET"
    assert "SPASTH treatment dataset" in data_ref["treatment_cost_source_label"]
    assert data_ref["total_expense"] == 85000.0

    # 2. User-provided actual bill
    actual_payload = {
        "procedure_name": "Appendectomy",
        "city": "Pune",
        "treatment_cost": 92000.0,
        "cost_mode": "actual"
    }
    resp_actual = client.post("/api/estimate/calculate-claim", json=actual_payload)
    assert resp_actual.status_code == 200
    data_actual = resp_actual.json()
    assert data_actual["treatment_cost_source"] == "USER_PROVIDED"
    assert data_actual["total_expense"] == 92000.0


def test_structured_calculation_contract_field():
    """Verify Section 9 structured calculation and trace fields."""
    payload = {
        "policy_id": CANONICAL_POLICY_ID,
        "procedure_name": "Cataract Surgery",
        "treatment_cost": 100000.0
    }
    resp = client.post("/api/estimate/calculate-claim", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "calculation" in data
    calc = data["calculation"]
    assert calc["eligible_amount"] == 100000.0
    assert calc["sublimit_excess"] == 60000.0
    assert calc["insurer_payable"] == 40000.0
    assert calc["customer_payable"] == 60000.0
    assert "trace" in data
    assert len(data["trace"]) > 0


def test_get_treatments_metadata_includes_benchmarks():
    """Verify GET /api/treatments returns canonical procedures, cities, and benchmarks."""
    resp = client.get("/api/treatments")
    assert resp.status_code == 200
    data = resp.json()
    assert "Appendectomy" in data["procedures"]
    assert "Pune" in data["cities"]
    assert data["benchmarks"] is not None
    assert len(data["benchmarks"]) >= 15

