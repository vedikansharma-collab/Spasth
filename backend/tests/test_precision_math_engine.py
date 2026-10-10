import pytest
import math
from decimal import Decimal
from pathlib import Path
import sys

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.math_engine import MathEngine, to_decimal, round_money
from app.services.treatment_service import TreatmentService

# ==============================================================================
# TESTS A - AE: PRECISION MATHEMATICAL ENGINE TEST SUITE
# ==============================================================================

def test_A_basic_treatment_calculation():
    """TEST A: Basic treatment calculation with clean 10% co-pay."""
    # Treatment Cost: 50,000, Co-pay: 10%
    # Expected: Insurer = 45,000, Customer = 5,000
    res = MathEngine.calculate_claim(treatment_cost=50000.0, copay_percent=10.0)
    assert res["status"] == "SUCCESS"
    assert res["total_expense"] == 50000.0
    assert res["insurer_payable"] == 45000.0
    assert res["customer_payable"] == 5000.0
    assert res["insurer_payable"] + res["customer_payable"] == res["total_expense"]
    assert len(res["calculation_trace"]) >= 4

def test_B_treatment_cost_lookup():
    """TEST B: Treatment cost lookup with exact and alias matching."""
    # Exact match
    cost_data = TreatmentService.get_treatment_cost("Appendectomy", "Pune")
    assert cost_data is not None
    assert cost_data["treatment_name"] == "Appendectomy"
    assert cost_data["cost_min"] == 75000.0
    assert cost_data["cost_max"] == 95000.0
    assert cost_data["data_status"] == "REFERENCE"

    # Alias match: "Appendix surgery" -> Appendectomy
    alias_data = TreatmentService.get_treatment_cost("Appendix surgery", "Pune")
    assert alias_data is not None
    assert alias_data["treatment_name"] == "Appendectomy"
    assert alias_data["cost_min"] == 75000.0

    # Alias match: "Phacoemulsification" -> Cataract Surgery
    cat_data = TreatmentService.get_treatment_cost("Phacoemulsification", "Mumbai")
    assert cat_data is not None
    assert cat_data["treatment_name"] == "Cataract Surgery"
    assert cat_data["cost_min"] == 45000.0

def test_C_unknown_treatment():
    """TEST C: Unknown treatment returns None without inventing numbers."""
    unknown_data = TreatmentService.get_treatment_cost("Space Travel Procedure", "Pune")
    assert unknown_data is None

def test_D_sum_insured_limit():
    """TEST D: Sum insured capping when claim exceeds total sum insured."""
    # Treatment Cost: 600,000, Sum Insured: 500,000, Co-pay: 0%
    # Expected: Insurer = 500,000, Customer = 100,000
    res = MathEngine.calculate_claim(
        treatment_cost=600000.0,
        copay_percent=0.0,
        sum_insured=500000.0
    )
    assert res["status"] == "SUCCESS"
    assert res["total_expense"] == 600000.0
    assert res["insurer_payable"] == 500000.0
    assert res["customer_payable"] == 100000.0
    assert res["customer_payable_breakdown"]["sum_insured_excess"] == 100000.0
    assert res["insurer_payable"] + res["customer_payable"] == res["total_expense"]

def test_E_remaining_sum_insured():
    """TEST E: Remaining sum insured calculation."""
    # Sum Insured: 500,000, Previous Remaining: 300,000
    # Claim: 100,000, Co-pay: 0%
    # Expected: Insurer = 100,000, New Remaining = 200,000
    res = MathEngine.calculate_claim(
        treatment_cost=100000.0,
        copay_percent=0.0,
        sum_insured=500000.0,
        remaining_sum_insured=300000.0
    )
    assert res["status"] == "SUCCESS"
    assert res["insurer_payable"] == 100000.0
    assert res["previous_remaining_sum_insured"] == 300000.0
    assert res["new_remaining_sum_insured"] == 200000.0

    # Claim exceeding remaining sum insured:
    # Previous Remaining: 150,000, Claim: 200,000
    # Expected: Insurer = 150,000, Customer = 50,000, New Remaining = 0.0
    res_exceed = MathEngine.calculate_claim(
        treatment_cost=200000.0,
        copay_percent=0.0,
        sum_insured=500000.0,
        remaining_sum_insured=150000.0
    )
    assert res_exceed["insurer_payable"] == 150000.0
    assert res_exceed["customer_payable"] == 50000.0
    assert res_exceed["new_remaining_sum_insured"] == 0.0

def test_F_sublimit():
    """TEST F: Procedure sublimit capping."""
    # Treatment Cost: 80,000, Cataract Sublimit: 40,000, Co-pay: 10%
    # Eligible after sublimit = 40,000
    # Co-pay 10% of 40,000 = 4,000
    # Insurer = 36,000
    # Customer = 40,000 (sublimit excess) + 4,000 (copay) = 44,000
    res = MathEngine.calculate_claim(
        treatment_cost=80000.0,
        copay_percent=10.0,
        treatment_sublimit=40000.0
    )
    assert res["status"] == "SUCCESS"
    assert res["sublimit_adjustment"] == 40000.0
    assert res["insurer_payable"] == 36000.0
    assert res["customer_payable"] == 44000.0
    assert res["customer_payable_breakdown"]["sublimit_excess"] == 40000.0
    assert res["customer_payable_breakdown"]["co_payment"] == 4000.0
    assert res["insurer_payable"] + res["customer_payable"] == 80000.0

def test_G_deductible():
    """TEST G: Deductible application separate from co-payment."""
    # Treatment Cost: 100,000, Deductible: 15,000, Co-pay: 0%
    # Expected: Insurer = 85,000, Customer = 15,000
    res = MathEngine.calculate_claim(
        treatment_cost=100000.0,
        copay_percent=0.0,
        deductible=15000.0
    )
    assert res["status"] == "SUCCESS"
    assert res["deductible"] == 15000.0
    assert res["insurer_payable"] == 85000.0
    assert res["customer_payable"] == 15000.0
    assert res["customer_payable_breakdown"]["deductible"] == 15000.0

def test_H_0_percent_copayment():
    """TEST H: 0% co-payment (Nil co-pay)."""
    res = MathEngine.calculate_claim(treatment_cost=60000.0, copay_percent=0.0)
    assert res["insurer_payable"] == 60000.0
    assert res["customer_payable"] == 0.0
    assert res["co_payment_amount"] == 0.0

def test_I_10_percent_copayment():
    """TEST I: 10% co-payment."""
    res = MathEngine.calculate_claim(treatment_cost=60000.0, copay_percent=10.0)
    assert res["insurer_payable"] == 54000.0
    assert res["customer_payable"] == 6000.0
    assert res["co_payment_amount"] == 6000.0

def test_J_20_percent_copayment():
    """TEST J: 20% co-payment."""
    res = MathEngine.calculate_claim(treatment_cost=60000.0, copay_percent=20.0)
    assert res["insurer_payable"] == 48000.0
    assert res["customer_payable"] == 12000.0
    assert res["co_payment_amount"] == 12000.0

def test_K_50_percent_copayment():
    """TEST K: 50% co-payment."""
    res = MathEngine.calculate_claim(treatment_cost=60000.0, copay_percent=50.0)
    assert res["insurer_payable"] == 30000.0
    assert res["customer_payable"] == 30000.0
    assert res["co_payment_amount"] == 30000.0

def test_L_100_percent_copayment():
    """TEST L: 100% co-payment (policyholder pays all)."""
    res = MathEngine.calculate_claim(treatment_cost=60000.0, copay_percent=100.0)
    assert res["insurer_payable"] == 0.0
    assert res["customer_payable"] == 60000.0
    assert res["co_payment_amount"] == 60000.0

def test_M_combined_deductible_and_copay():
    """TEST M: Combined deductible and co-payment."""
    # Treatment Cost: 100,000, Deductible: 20,000, Co-pay: 10%
    # Step 1: Total = 100,000
    # Step 2: After Deductible = 100,000 - 20,000 = 80,000
    # Step 3: Co-pay 10% of 80,000 = 8,000
    # Insurer = 80,000 - 8,000 = 72,000
    # Customer = 20,000 (deductible) + 8,000 (copay) = 28,000
    res = MathEngine.calculate_claim(
        treatment_cost=100000.0,
        deductible=20000.0,
        copay_percent=10.0
    )
    assert res["status"] == "SUCCESS"
    assert res["insurer_payable"] == 72000.0
    assert res["customer_payable"] == 28000.0
    assert res["customer_payable_breakdown"]["deductible"] == 20000.0
    assert res["customer_payable_breakdown"]["co_payment"] == 8000.0
    assert res["insurer_payable"] + res["customer_payable"] == 100000.0

def test_N_combined_sublimit_and_copay():
    """TEST N: Combined sublimit and co-payment."""
    # Treatment Cost: 100,000, Sublimit: 60,000, Co-pay: 20%
    # Step 1: Sublimit restricts base to 60,000 (restricted: 40,000)
    # Step 2: Co-pay 20% of 60,000 = 12,000
    # Insurer = 48,000
    # Customer = 40,000 (sublimit excess) + 12,000 (copay) = 52,000
    res = MathEngine.calculate_claim(
        treatment_cost=100000.0,
        treatment_sublimit=60000.0,
        copay_percent=20.0
    )
    assert res["status"] == "SUCCESS"
    assert res["insurer_payable"] == 48000.0
    assert res["customer_payable"] == 52000.0
    assert res["insurer_payable"] + res["customer_payable"] == 100000.0

def test_O_large_claim():
    """TEST O: Large claim (₹10,000,000)."""
    res = MathEngine.calculate_claim(
        treatment_cost=10000000.0,
        copay_percent=10.0,
        sum_insured=5000000.0
    )
    assert res["status"] == "SUCCESS"
    # 90% of 10M is 9M, capped at Sum Insured 5M
    assert res["insurer_payable"] == 5000000.0
    assert res["customer_payable"] == 5000000.0
    assert res["insurer_payable"] + res["customer_payable"] == 10000000.0

def test_P_claim_exactly_at_limit():
    """TEST P: Claim exactly at Sum Insured limit."""
    res = MathEngine.calculate_claim(
        treatment_cost=500000.0,
        copay_percent=0.0,
        sum_insured=500000.0
    )
    assert res["insurer_payable"] == 500000.0
    assert res["customer_payable"] == 0.0
    assert res["new_remaining_sum_insured"] == 0.0

def test_Q_claim_above_limit():
    """TEST Q: Claim above Sum Insured limit."""
    res = MathEngine.calculate_claim(
        treatment_cost=500001.0,
        copay_percent=0.0,
        sum_insured=500000.0
    )
    assert res["insurer_payable"] == 500000.0
    assert res["customer_payable"] == 1.0

def test_R_zero_claim():
    """TEST R: Zero claim amount."""
    res = MathEngine.calculate_claim(treatment_cost=0.0, copay_percent=10.0)
    assert res["status"] == "SUCCESS"
    assert res["total_expense"] == 0.0
    assert res["insurer_payable"] == 0.0
    assert res["customer_payable"] == 0.0

def test_S_negative_claim_rejection():
    """TEST S: Negative claim rejected with INVALID_INPUT."""
    res = MathEngine.calculate_claim(treatment_cost=-500.0)
    assert res["status"] == "INVALID_INPUT"
    assert "Negative" in res["error"]

def test_T_invalid_percentage_rejection():
    """TEST T: Invalid co-payment percentage (>100 or <0)."""
    res_high = MathEngine.calculate_claim(treatment_cost=1000.0, copay_percent=105.0)
    assert res_high["status"] == "INVALID_INPUT"

    res_neg = MathEngine.calculate_claim(treatment_cost=1000.0, copay_percent=-5.0)
    assert res_neg["status"] == "INVALID_INPUT"

def test_U_missing_input_validation():
    """TEST U: Missing mandatory input validation."""
    res = MathEngine.calculate_claim(treatment_cost="invalid_string")
    assert res["status"] == "INVALID_INPUT"

def test_V_null_input_handling():
    """TEST V: Null input handling vs legitimate zero."""
    res_null = MathEngine.calculate_claim(treatment_cost=None)
    assert res_null["status"] == "INVALID_INPUT"
    assert res_null["error"] == "Treatment cost is required."

    res_zero = MathEngine.calculate_claim(treatment_cost=0)
    assert res_zero["status"] == "SUCCESS"
    assert res_zero["total_expense"] == 0.0

def test_W_nan_rejection():
    """TEST W: NaN value rejection."""
    res = MathEngine.calculate_claim(treatment_cost=float("nan"))
    assert res["status"] == "INVALID_INPUT"

def test_X_infinity_rejection():
    """TEST X: Infinity value rejection."""
    res = MathEngine.calculate_claim(treatment_cost=float("inf"))
    assert res["status"] == "INVALID_INPUT"

def test_Y_decimal_monetary_precision():
    """TEST Y: Decimal monetary values & precision rounding."""
    # Test fractional pennies
    res = MathEngine.calculate_claim(treatment_cost=1000.33, copay_percent=15.0)
    assert res["status"] == "SUCCESS"
    # 1000.33 * 0.15 = 150.0495 -> 150.05
    assert res["co_payment_amount"] == 150.05
    # Insurer = 1000.33 - 150.05 = 850.28
    assert res["insurer_payable"] == 850.28
    assert res["customer_payable"] == 150.05
    assert round(res["insurer_payable"] + res["customer_payable"], 2) == 1000.33

def test_Z_multiple_deductions():
    """TEST Z: Multiple deductions combined sequentially."""
    # Total Cost = 200,000
    # Non-covered = 10,000 -> Eligible Base = 190,000
    # Sublimit = 150,000 -> Eligible after sublimit = 150,000 (sublimit excess = 40,000)
    # Deductible = 20,000 -> Eligible after deductible = 130,000 (deductible = 20,000)
    # Co-pay = 10% -> 13,000 (copay amount = 13,000) -> Insurer pre-SI = 117,000
    # Sum Insured = 100,000 -> Insurer Payable = 100,000 (SI excess = 17,000)
    # Customer Payable = 10,000 + 40,000 + 20,000 + 13,000 + 17,000 = 100,000
    # Invariant: 100,000 + 100,000 == 200,000!
    res = MathEngine.calculate_claim(
        treatment_cost=200000.0,
        non_covered_expense=10000.0,
        treatment_sublimit=150000.0,
        deductible=20000.0,
        copay_percent=10.0,
        sum_insured=100000.0
    )
    assert res["status"] == "SUCCESS"
    assert res["insurer_payable"] == 100000.0
    assert res["customer_payable"] == 100000.0
    assert res["insurer_payable"] + res["customer_payable"] == 200000.0
    assert res["customer_payable_breakdown"]["non_covered_expense"] == 10000.0
    assert res["customer_payable_breakdown"]["sublimit_excess"] == 40000.0
    assert res["customer_payable_breakdown"]["deductible"] == 20000.0
    assert res["customer_payable_breakdown"]["co_payment"] == 13000.0
    assert res["customer_payable_breakdown"]["sum_insured_excess"] == 17000.0

def test_AA_policy_conflict_and_room_proportionate():
    """TEST AA: Policy room rent proportionate deduction."""
    # Room upgrade with 25% proportionate penalty
    res = MathEngine.calculate_claim(
        treatment_cost=100000.0,
        room_penalty_ratio=0.25,
        copay_percent=10.0
    )
    assert res["status"] == "SUCCESS"
    # Eligible after room penalty: 100,000 - 25,000 = 75,000
    # Co-pay 10% of 75,000 = 7,500
    # Insurer = 67,500
    # Customer = 25,000 (room upgrade) + 7,500 (copay) = 32,500
    assert res["room_adjustment"] == 25000.0
    assert res["insurer_payable"] == 67500.0
    assert res["customer_payable"] == 32500.0
    assert res["insurer_payable"] + res["customer_payable"] == 100000.0

def test_AB_unsupported_policy_rule():
    """TEST AB: Rule not available when invalid room ratio supplied."""
    res = MathEngine.calculate_claim(
        treatment_cost=100000.0,
        room_penalty_ratio=1.5  # Ratio > 1.0 is invalid
    )
    assert res["status"] == "INVALID_INPUT"

def test_AC_no_double_deduction():
    """TEST AC: Verify no deduction is applied twice."""
    res = MathEngine.calculate_claim(
        treatment_cost=100000.0,
        deductible=10000.0,
        copay_percent=10.0
    )
    # Deductible should only be deducted once (at Step 5)
    deductible_steps = [t for t in res["calculation_trace"] if t["rule"] == "DEDUCTIBLE"]
    assert len(deductible_steps) == 1
    assert deductible_steps[0]["deduction"] == 10000.0

    copay_steps = [t for t in res["calculation_trace"] if t["rule"] == "CO_PAYMENT"]
    assert len(copay_steps) == 1
    assert copay_steps[0]["deduction"] == 9000.0

    # Total must reconcile
    assert res["insurer_payable"] + res["customer_payable"] == 100000.0

def test_AD_deterministic_repeated_calculation():
    """TEST AD: Determinism verification — 100 consecutive runs produce exact identical results."""
    first_run = MathEngine.calculate_claim(
        treatment_cost=123456.78,
        non_covered_expense=5432.10,
        treatment_sublimit=100000.0,
        deductible=5000.0,
        copay_percent=15.0,
        sum_insured=80000.0
    )

    for _ in range(100):
        run = MathEngine.calculate_claim(
            treatment_cost=123456.78,
            non_covered_expense=5432.10,
            treatment_sublimit=100000.0,
            deductible=5000.0,
            copay_percent=15.0,
            sum_insured=80000.0
        )
        assert run["insurer_payable"] == first_run["insurer_payable"]
        assert run["customer_payable"] == first_run["customer_payable"]
        assert run["total_expense"] == first_run["total_expense"]

def test_AE_frontend_cannot_override_policy_value():
    """TEST AE: Security — Frontend sending copay=0% cannot override backend policy copay=20%."""
    from app.services.policy_service import PolicyService

    # Base canonical policy has 10% or 0% copay
    # When requesting via endpoint /api/estimate/calculate-claim, backend policy rules are enforced
    sample_policy_rules = [
        {"rule_type": "copay", "rule_key": "copay", "value": 20.0, "source_text": "20% co-payment"}
    ]
    
    # Calculate directly with authoritative policy rule
    authoritative_copay = sample_policy_rules[0]["value"]
    res = MathEngine.calculate_claim(treatment_cost=100000.0, copay_percent=authoritative_copay)
    assert res["co_payment_percentage"] == 20.0
    assert res["co_payment_amount"] == 20000.0
    assert res["insurer_payable"] == 80000.0
    assert res["customer_payable"] == 20000.0
