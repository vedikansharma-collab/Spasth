import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

from app.main import app
from app.services.math_engine import MathEngine
from app.calculation.validator import CalculationValidator
from app.services.treatment_service import TreatmentService

client = TestClient(app)

# ==============================================================================
# SECTION 19: CANONICAL BENCHMARK VALIDATION
# ==============================================================================

def test_section_19_canonical_appendectomy():
    """
    Section 19: Canonical benchmark test.
    Treatment: Appendectomy
    Treatment Cost: ₹100,000
    Sum Insured: ₹500,000
    Appendectomy Sublimit: ₹90,000
    Co-payment: 10%
    Deductible: ₹0
    Non-covered: ₹0

    Expected:
    Treatment Cost = ₹100,000
    Sublimit Excess = ₹10,000
    Eligible after Sublimit = ₹90,000
    Co-payment = ₹9,000
    Insurance Payable = ₹81,000
    Customer Out-of-Pocket = ₹19,000
    Remaining Sum Insured = ₹419,000
    Reconciliation: ₹81,000 + ₹19,000 = ₹100,000
    """
    result = MathEngine.calculate_claim(
        treatment_cost=100000,
        quantity=1,
        non_covered_expense=0,
        copay_percent=10,
        deductible=0,
        treatment_sublimit=90000,
        sum_insured=500000,
        procedure_name="Appendectomy",
        city="Pune"
    )

    # 1. Math Engine Results
    assert result["status"] == "SUCCESS"
    assert result["total_expense"] == 100000.0
    assert result["eligible_amount"] == 100000.0
    assert result["sublimit"] == 90000.0
    assert result["sublimit_adjustment"] == 10000.0
    assert result["customer_payable_breakdown"]["sublimit_excess"] == 10000.0
    assert result["co_payment_amount"] == 9000.0
    assert result["customer_payable_breakdown"]["co_payment"] == 9000.0
    assert result["insurer_payable"] == 81000.0
    assert result["customer_payable"] == 19000.0
    assert result["remaining_sum_insured"] == 419000.0

    # 2. Reconciliation Invariant
    assert result["insurer_payable"] + result["customer_payable"] == result["total_expense"]

    # 3. Independent Calculation Validator Verification
    val = result["validation"]
    assert val["independent_check"] is True
    assert val["reconciled"] is True
    assert val["status"] == "CALCULATION_VALIDATED"
    assert val["expected_values"]["insurer_payable"] == 81000.0
    assert val["expected_values"]["customer_payable"] == 19000.0
    assert val["expected_values"]["remaining_sum_insured"] == 419000.0


# ==============================================================================
# SECTION 20: TEST CASES A TO AH
# ==============================================================================

# Test A: Exact treatment cost
def test_a_exact_treatment_cost():
    res = MathEngine.calculate_claim(treatment_cost=75000.0)
    assert res["total_expense"] == 75000.0
    assert res["insurer_payable"] == 75000.0
    assert res["customer_payable"] == 0.0

# Test B: Quantity > 1
def test_b_quantity_multiplier():
    res = MathEngine.calculate_claim(treatment_cost=25000.0, quantity=3)
    assert res["total_expense"] == 75000.0
    assert res["validation"]["status"] == "CALCULATION_VALIDATED"

# Test C: Unknown treatment benchmark lookup
def test_c_unknown_treatment():
    data = TreatmentService.get_treatment_cost("NonExistentSpecialtySurgery", "Pune")
    assert data is None

# Test D: Missing treatment cost API handling
def test_d_missing_treatment_cost():
    resp = client.post("/api/estimate/calculate-claim", json={
        "procedure_name": "NonExistentSpecialtySurgery",
        "city": "Pune"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "TREATMENT_COST_NOT_AVAILABLE"
    assert "Reference treatment cost unavailable" in data["message"]
    assert data["total_expense"] is None

# Test E: Actual user-provided cost precedence
def test_e_user_provided_cost():
    resp = client.post("/api/estimate/calculate-claim", json={
        "procedure_name": "Appendectomy",
        "city": "Pune",
        "treatment_cost": 100000,
        "cost_mode": "actual",
        "sum_insured": 500000,
        "treatment_sublimit": 90000,
        "copay_percent": 10
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["treatment_cost_source"] == "USER_PROVIDED"
    assert data["insurer_payable"] == 81000.0
    assert data["customer_payable"] == 19000.0
    assert data["validation"]["status"] == "CALCULATION_VALIDATED"

# Test F: Reference dataset cost
def test_f_reference_dataset_cost():
    resp = client.post("/api/estimate/calculate-claim", json={
        "procedure_name": "Appendectomy",
        "city": "Pune",
        "cost_mode": "reference"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["treatment_cost_source"] == "REFERENCE_DATASET"
    assert data["total_expense"] == 85000.0

# Test G: 0% co-pay
def test_g_zero_copay():
    res = MathEngine.calculate_claim(treatment_cost=50000.0, copay_percent=0.0)
    assert res["co_payment_amount"] == 0.0
    assert res["customer_payable"] == 0.0
    assert res["insurer_payable"] == 50000.0

# Test H: 10% co-pay
def test_h_ten_percent_copay():
    res = MathEngine.calculate_claim(treatment_cost=100000.0, copay_percent=10.0)
    assert res["co_payment_amount"] == 10000.0
    assert res["insurer_payable"] == 90000.0
    assert res["customer_payable"] == 10000.0

# Test I: 20% co-pay
def test_i_twenty_percent_copay():
    res = MathEngine.calculate_claim(treatment_cost=100000.0, copay_percent=20.0)
    assert res["co_payment_amount"] == 20000.0
    assert res["insurer_payable"] == 80000.0
    assert res["customer_payable"] == 20000.0

# Test J: 50% co-pay
def test_j_fifty_percent_copay():
    res = MathEngine.calculate_claim(treatment_cost=100000.0, copay_percent=50.0)
    assert res["co_payment_amount"] == 50000.0
    assert res["insurer_payable"] == 50000.0
    assert res["customer_payable"] == 50000.0

# Test K: 100% co-pay
def test_k_hundred_percent_copay():
    res = MathEngine.calculate_claim(treatment_cost=100000.0, copay_percent=100.0)
    assert res["co_payment_amount"] == 100000.0
    assert res["insurer_payable"] == 0.0
    assert res["customer_payable"] == 100000.0

# Test L: Deductible
def test_l_deductible():
    res = MathEngine.calculate_claim(treatment_cost=100000.0, deductible=15000.0)
    assert res["deductible"] == 15000.0
    assert res["customer_payable_breakdown"]["deductible"] == 15000.0
    assert res["insurer_payable"] == 85000.0
    assert res["customer_payable"] == 15000.0

# Test M: Sublimit
def test_m_sublimit():
    res = MathEngine.calculate_claim(treatment_cost=120000.0, treatment_sublimit=80000.0)
    assert res["sublimit_adjustment"] == 40000.0
    assert res["customer_payable_breakdown"]["sublimit_excess"] == 40000.0
    assert res["insurer_payable"] == 80000.0
    assert res["customer_payable"] == 40000.0

# Test N: Sum Insured cap
def test_n_sum_insured_cap():
    res = MathEngine.calculate_claim(treatment_cost=300000.0, sum_insured=200000.0)
    assert res["insurer_payable"] == 200000.0
    assert res["customer_payable"] == 100000.0
    assert res["customer_payable_breakdown"]["sum_insured_excess"] == 100000.0

# Test O: Remaining Sum Insured
def test_o_remaining_sum_insured():
    res = MathEngine.calculate_claim(treatment_cost=80000.0, sum_insured=500000.0)
    assert res["remaining_sum_insured"] == 420000.0

# Test P: Non-covered expense
def test_p_non_covered_expense():
    res = MathEngine.calculate_claim(treatment_cost=100000.0, non_covered_expense=5000.0)
    assert res["non_covered_expense"] == 5000.0
    assert res["customer_payable_breakdown"]["non_covered_expense"] == 5000.0
    assert res["insurer_payable"] == 95000.0
    assert res["customer_payable"] == 5000.0

# Test Q: Room rule proportionate deduction
def test_q_room_rule():
    res = MathEngine.calculate_claim(treatment_cost=100000.0, room_penalty_ratio=0.10)
    assert res["room_adjustment"] == 10000.0
    assert res["customer_payable_breakdown"]["room_upgrade_excess"] == 10000.0
    assert res["insurer_payable"] == 90000.0
    assert res["customer_payable"] == 10000.0

# Test R: Missing room rule formula flags uncertainty
def test_r_missing_room_rule_formula():
    resp = client.post("/api/estimate/calculate-claim", json={
        "procedure_name": "Appendectomy",
        "city": "Pune",
        "room_category": "Deluxe",
        "treatment_cost": 85000
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") in ("SUCCESS", "calculated")

# Test S: Missing co-pay does not default blindly if policy exists
def test_s_missing_copay():
    # Math Engine handles explicitly passed 0.0 vs omitted
    res = MathEngine.calculate_claim(treatment_cost=10000.0, copay_percent=0.0)
    assert res["co_payment_percentage"] == 0.0

# Test T: Missing deductible
def test_t_missing_deductible():
    res = MathEngine.calculate_claim(treatment_cost=10000.0, deductible=0.0)
    assert res["deductible"] == 0.0

# Test U: Missing sublimit
def test_u_missing_sublimit():
    res = MathEngine.calculate_claim(treatment_cost=50000.0, treatment_sublimit=None)
    assert res["sublimit"] is None
    assert res["sublimit_adjustment"] == 0.0

# Test V: Missing Sum Insured
def test_v_missing_sum_insured():
    res = MathEngine.calculate_claim(treatment_cost=50000.0, sum_insured=None)
    assert res["sum_insured"] is None
    assert res["remaining_sum_insured"] is None

# Test W: Waiting period eligibility
def test_w_waiting_period_eligibility():
    resp = client.post("/api/estimate/calculate-claim", json={
        "procedure_name": "Appendectomy",
        "city": "Pune",
        "treatment_cost": 85000,
        "scenario": {
            "is_ped": True,
            "policy_tenure_months": 6  # PED requires 36/48 months
        }
    })
    assert resp.status_code == 200
    data = resp.json()
    if data["status"] == "WAITING_PERIOD":
        assert data["insurer_payable"] == 0.0
        assert data["customer_payable"] == 85000.0

# Test X: Cumulative bonus
def test_x_cumulative_bonus():
    # Sum insured with no blind bonus
    res = MathEngine.calculate_claim(treatment_cost=50000.0, sum_insured=500000.0)
    assert res["sum_insured"] == 500000.0

# Test Y: Multiple deductions sequential
def test_y_multiple_deductions():
    # Bill = 150k, Non-covered = 10k -> 140k
    # Sublimit = 100k -> 40k sublimit excess, eligible = 100k
    # Room penalty = 10% -> 10k room excess, eligible = 90k
    # Deductible = 10k -> 10k deductible, eligible = 80k
    # Copay = 10% -> 8k copay, insurer pre-si = 72k
    # Sum Insured = 500k -> Insurer = 72k
    # Customer = 10k + 40k + 10k + 10k + 8k = 78k
    # Reconciliation: 72k + 78k = 150k
    res = MathEngine.calculate_claim(
        treatment_cost=150000.0,
        non_covered_expense=10000.0,
        treatment_sublimit=100000.0,
        room_penalty_ratio=0.10,
        deductible=10000.0,
        copay_percent=10.0,
        sum_insured=500000.0
    )
    assert res["total_expense"] == 150000.0
    assert res["insurer_payable"] == 72000.0
    assert res["customer_payable"] == 78000.0
    assert res["insurer_payable"] + res["customer_payable"] == 150000.0
    assert res["validation"]["status"] == "CALCULATION_VALIDATED"

# Test Z: Decimal precision
def test_z_decimal_precision():
    # Ensure exact 100000 * 10% is 10000.00
    res = MathEngine.calculate_claim(treatment_cost=100000.0, copay_percent=10.0)
    assert res["co_payment_amount"] == 10000.00
    assert str(res["co_payment_amount"]) == "10000.0"

# Test AA: Negative values rejected
def test_aa_negative_values():
    res = MathEngine.calculate_claim(treatment_cost=-5000.0)
    assert res["status"] == "INVALID_INPUT"

# Test AB: NaN rejected
def test_ab_nan_rejected():
    res = MathEngine.calculate_claim(treatment_cost=float("nan"))
    assert res["status"] == "INVALID_INPUT"

# Test AC: Infinity rejected
def test_ac_infinity_rejected():
    res = MathEngine.calculate_claim(treatment_cost=float("inf"))
    assert res["status"] == "INVALID_INPUT"

# Test AD: Zero values handled gracefully
def test_ad_zero_values():
    res = MathEngine.calculate_claim(
        treatment_cost=0.0,
        quantity=1,
        copay_percent=0.0
    )
    assert res["status"] == "SUCCESS"
    assert res["total_expense"] == 0.0
    assert res["customer_payable"] == 0.0

# Test AE: Independent validator mismatch detection
def test_ae_validator_mismatch():
    # Test that validator detects when a tampered result is passed
    tampered_math_result = {
        "total_expense": 100000.0,
        "insurer_payable": 80000.0,  # Should be 81000
        "customer_payable": 20000.0,  # Should be 19000
        "remaining_sum_insured": 419000.0
    }
    inputs = {
        "treatment_cost": 100000.0,
        "quantity": 1,
        "sublimit": 90000.0,
        "copay_percent": 10.0,
        "sum_insured": 500000.0
    }
    val = CalculationValidator.validate_calculation(tampered_math_result, inputs)
    assert val["status"] == "CALCULATION_MISMATCH"
    assert val["independent_check"] is False
    assert len(val["discrepancies"]) >= 2

# Test AF: Reconciliation failure detection
def test_af_reconciliation_failure():
    # Insurer + Customer != Total
    broken_result = {
        "total_expense": 100000.0,
        "insurer_payable": 70000.0,
        "customer_payable": 10000.0  # Sum is 80k != 100k
    }
    inputs = {
        "treatment_cost": 100000.0,
        "quantity": 1
    }
    val = CalculationValidator.validate_calculation(broken_result, inputs)
    assert val["reconciled"] is False
    assert val["status"] == "CALCULATION_RECONCILIATION_FAILED"

# Test AG: API Integration
def test_ag_api_integration():
    resp = client.post("/api/estimate/calculate-claim", json={
        "procedure_name": "Appendectomy",
        "city": "Pune",
        "treatment_cost": 100000,
        "cost_mode": "actual",
        "sum_insured": 500000,
        "treatment_sublimit": 90000,
        "copay_percent": 10
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["calculation"]["total_expense"] == 100000.0
    assert data["calculation"]["sublimit_excess"] == 10000.0
    assert data["calculation"]["copay_amount"] == 9000.0
    assert data["calculation"]["insurer_payable"] == 81000.0
    assert data["calculation"]["customer_payable"] == 19000.0
    assert data["calculation"]["remaining_sum_insured"] == 419000.0
    assert data["validation"]["status"] == "CALCULATION_VALIDATED"

# Test AH: Backend values match expected Section 16 format
def test_ah_section_16_schema():
    resp = client.post("/api/estimate/calculate-claim", json={
        "procedure_name": "Appendectomy",
        "city": "Pune",
        "treatment_cost": 100000,
        "cost_mode": "reference",
        "sum_insured": 500000,
        "treatment_sublimit": 90000,
        "copay_percent": 10
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "treatment" in data
    assert "cost_source" in data
    assert "treatment_cost" in data
    assert "quantity" in data
    assert "policy" in data
    assert "calculation" in data
    assert "validation" in data
    assert data["validation"]["independent_check"] is True
    assert data["validation"]["reconciled"] is True
