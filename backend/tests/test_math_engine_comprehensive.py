import pytest
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.calculation.engine import FinancialCalculationEngine
from app.services.math_engine import MathEngine
from app.validation.policy_validator import PolicyValidator, ValidationError

# Grounded base policy rules for testing
BASE_VALID_RULES = [
    {
        "rule_type": "sum_insured",
        "value": 500000.0,
        "unit": "INR",
        "page": 1,
        "clause": "1.1",
        "source_text": "Base policy Sum Insured: INR 5,00,000"
    },
    {
        "rule_type": "copay",
        "value": 10.0,
        "unit": "percent",
        "page": 2,
        "clause": "2.1",
        "source_text": "Mandatory 10% co-payment on all claims"
    }
]

def test_1_treatment_cost_below_sublimit():
    """TEST 1: Treatment cost below sub-limit."""
    rules = [
        *BASE_VALID_RULES,
        {
            "rule_type": "sub_limit",
            "rule_key": "Appendectomy",
            "value": 80000.0,
            "unit": "INR",
            "page": 3,
            "clause": "3.2",
            "source_text": "Appendectomy sub-limit capped at INR 80,000"
        }
    ]

    # Costs: 50,000 to 60,000 (both < 80,000 sub-limit)
    result = FinancialCalculationEngine.calculate_out_of_pocket(
        base_min_cost=50000.0,
        base_max_cost=60000.0,
        procedure_name="Appendectomy",
        city="Pune",
        room_category="Standard",
        policy_rules=rules
    )

    assert result["status"] == "calculated"
    assert result["eligible_amount"]["min"] == 50000.0
    assert result["eligible_amount"]["max"] == 60000.0
    assert result["copay_amount"]["min"] == 5000.0
    assert result["copay_amount"]["max"] == 6000.0
    assert result["insurance_contribution"]["min"] == 45000.0
    assert result["insurance_contribution"]["max"] == 54000.0
    assert result["patient_payable"]["min"] == 5000.0
    assert result["patient_payable"]["max"] == 6000.0

def test_2_treatment_cost_above_sublimit():
    """TEST 2: Treatment cost above sub-limit."""
    rules = [
        *BASE_VALID_RULES,
        {
            "rule_type": "sub_limit",
            "rule_key": "Cataract Surgery",
            "value": 40000.0,
            "unit": "INR",
            "page": 3,
            "clause": "3.3",
            "source_text": "Cataract Surgery procedure cap: INR 40,000"
        }
    ]

    # Costs: 50,000 to 70,000 (both > 40,000 sub-limit)
    result = FinancialCalculationEngine.calculate_out_of_pocket(
        base_min_cost=50000.0,
        base_max_cost=70000.0,
        procedure_name="Cataract Surgery",
        city="Mumbai",
        room_category="Standard",
        policy_rules=rules
    )

    assert result["status"] == "calculated"
    assert result["eligible_amount"]["min"] == 40000.0
    assert result["eligible_amount"]["max"] == 40000.0
    assert result["insurance_contribution"]["min"] == 36000.0
    assert result["insurance_contribution"]["max"] == 36000.0
    # Patient payable = treatment_cost - insurance_contribution
    assert result["patient_payable"]["min"] == 14000.0
    assert result["patient_payable"]["max"] == 34000.0

def test_3_ten_percent_copay():
    """TEST 3: 10% co-payment."""
    rules = [
        *BASE_VALID_RULES,
        {
            "rule_type": "sub_limit",
            "rule_key": "Appendectomy",
            "value": 150000.0,
            "unit": "INR",
            "page": 2,
            "clause": "2.2",
            "source_text": "Appendectomy limit INR 1,50,000"
        }
    ]

    result = FinancialCalculationEngine.calculate_out_of_pocket(
        base_min_cost=100000.0,
        base_max_cost=100000.0,
        procedure_name="Appendectomy",
        city="Pune",
        room_category="Standard",
        policy_rules=rules
    )

    assert result["copay_percent"] == 10.0
    assert result["copay_amount"]["min"] == 10000.0
    assert result["insurance_contribution"]["min"] == 90000.0
    assert result["patient_payable"]["min"] == 10000.0

def test_4_zero_percent_copay():
    """TEST 4: 0% co-payment (No co-payment)."""
    rules = [
        {
            "rule_type": "sum_insured",
            "value": 500000.0,
            "unit": "INR",
            "page": 1,
            "clause": "1.1",
            "source_text": "Sum Insured: INR 5,00,000"
        },
        {
            "rule_type": "copay",
            "value": 0.0,
            "unit": "percent",
            "page": 2,
            "clause": "2.1",
            "source_text": "0% co-payment policy"
        }
    ]

    result = FinancialCalculationEngine.calculate_out_of_pocket(
        base_min_cost=100000.0,
        base_max_cost=100000.0,
        procedure_name="Appendectomy",
        city="Pune",
        room_category="Standard",
        policy_rules=rules
    )

    assert result["copay_percent"] == 0.0
    assert result["copay_amount"]["min"] == 0.0
    assert result["insurance_contribution"]["min"] == 100000.0
    assert result["patient_payable"]["min"] == 0.0

def test_5_missing_sublimit():
    """TEST 5: Missing sub-limit (Full eligible amount covered up to Sum Insured)."""
    rules = [
        {
            "rule_type": "sum_insured",
            "value": 500000.0,
            "unit": "INR",
            "page": 1,
            "clause": "1.1",
            "source_text": "Sum Insured: INR 5,00,000"
        },
        {
            "rule_type": "copay",
            "value": 10.0,
            "unit": "percent",
            "page": 2,
            "clause": "2.1",
            "source_text": "10% Copay"
        }
    ]

    result = FinancialCalculationEngine.calculate_out_of_pocket(
        base_min_cost=75000.0,
        base_max_cost=95000.0,
        procedure_name="Appendectomy",
        city="Pune",
        room_category="Standard",
        policy_rules=rules
    )

    assert result["applicable_sublimit"] is None
    assert result["eligible_amount"]["min"] == 75000.0
    assert result["eligible_amount"]["max"] == 95000.0
    assert result["insurance_contribution"]["min"] == 67500.0
    assert result["insurance_contribution"]["max"] == 85500.0

def test_6_missing_treatment_cost():
    """TEST 6: Missing treatment cost benchmark."""
    result = FinancialCalculationEngine.calculate_out_of_pocket(
        base_min_cost=0.0,
        base_max_cost=0.0,
        procedure_name="Experimental Surgery",
        city="Pune",
        room_category="Standard",
        policy_rules=BASE_VALID_RULES,
        cost_found=False
    )

    assert result["status"] == "UNABLE_TO_ESTIMATE"
    assert result["confidence"] == "LOW"
    assert "benchmark" in result["message"].lower()

def test_7_invalid_negative_cost():
    """TEST 7: Invalid negative treatment cost."""
    result = FinancialCalculationEngine.calculate_out_of_pocket(
        base_min_cost=-50000.0,
        base_max_cost=80000.0,
        procedure_name="Appendectomy",
        city="Pune",
        room_category="Standard",
        policy_rules=BASE_VALID_RULES
    )

    assert result["status"] == "UNABLE_TO_ESTIMATE"
    assert "negative" in result["confidence_reason"].lower()

def test_8_excluded_treatment():
    """TEST 8: Excluded treatment."""
    rules = [
        *BASE_VALID_RULES,
        {
            "rule_type": "exclusion",
            "rule_key": "Cosmetic Surgery",
            "value": "Cosmetic and aesthetic treatments strictly excluded",
            "unit": "text",
            "page": 8,
            "clause": "Clause 4.1(a)",
            "source_text": "Cosmetic surgery and procedures are explicitly excluded from coverage."
        }
    ]

    result = FinancialCalculationEngine.calculate_out_of_pocket(
        base_min_cost=80000.0,
        base_max_cost=120000.0,
        procedure_name="Cosmetic Surgery",
        city="Mumbai",
        room_category="Standard",
        policy_rules=rules
    )

    assert result["status"] == "EXCLUDED"
    assert result["insurance_contribution"]["min"] == 0.0
    assert result["insurance_contribution"]["max"] == 0.0
    assert result["patient_payable"]["min"] == 80000.0
    assert result["patient_payable"]["max"] == 120000.0
    assert result["coverage_checks"]["exclusion_status"] == "found"
    assert len(result["citations"]) >= 1
    assert result["citations"][0]["page"] == 8

def test_9_waiting_period_not_satisfied():
    """TEST 9: Waiting period not satisfied."""
    rules = [
        *BASE_VALID_RULES,
        {
            "rule_type": "waiting_period",
            "rule_key": "Knee Replacement",
            "value": "24 months waiting period",
            "unit": "months",
            "page": 5,
            "clause": "Clause 3.2",
            "source_text": "A waiting period of 24 months applies for Knee Replacement surgery."
        }
    ]

    # Scenario: Policy active for only 12 months (less than 24 months)
    result = FinancialCalculationEngine.calculate_out_of_pocket(
        base_min_cost=180000.0,
        base_max_cost=240000.0,
        procedure_name="Knee Replacement",
        city="Pune",
        room_category="Standard",
        policy_rules=rules,
        scenario={"policy_tenure_months": 12}
    )

    assert result["status"] == "WAITING_PERIOD"
    assert result["insurance_contribution"]["min"] == 0.0
    assert result["coverage_checks"]["waiting_period_status"] == "not_satisfied"
    assert "24 months" in result["message"]

def test_10_waiting_period_satisfied():
    """TEST 10: Waiting period satisfied."""
    rules = [
        *BASE_VALID_RULES,
        {
            "rule_type": "waiting_period",
            "rule_key": "Knee Replacement",
            "value": "24 months waiting period",
            "unit": "months",
            "page": 5,
            "clause": "Clause 3.2",
            "source_text": "A waiting period of 24 months applies for Knee Replacement surgery."
        }
    ]

    # Scenario: Policy active for 36 months (greater than 24 months)
    result = FinancialCalculationEngine.calculate_out_of_pocket(
        base_min_cost=180000.0,
        base_max_cost=240000.0,
        procedure_name="Knee Replacement",
        city="Pune",
        room_category="Standard",
        policy_rules=rules,
        scenario={"policy_tenure_months": 36}
    )

    assert result["status"] == "calculated"
    assert result["insurance_contribution"]["min"] > 0
    assert result["coverage_checks"]["waiting_period_status"] == "satisfied"

def test_11_missing_policy_rule():
    """TEST 11: Missing policy rule / ungrounded evidence rejected."""
    invalid_rules = [
        {
            "rule_type": "sum_insured",
            "value": 500000.0,
            # page is missing!
            # source_text is missing!
        }
    ]

    result = FinancialCalculationEngine.calculate_out_of_pocket(
        base_min_cost=75000.0,
        base_max_cost=95000.0,
        procedure_name="Appendectomy",
        city="Pune",
        room_category="Standard",
        policy_rules=invalid_rules
    )

    assert result["status"] == "UNABLE_TO_ESTIMATE"
    assert result["confidence"] == "LOW"

def test_12_room_rule_ambiguity():
    """TEST 12: Room rule ambiguity (no hardcoded 30% penalty; medium confidence)."""
    rules = [
        *BASE_VALID_RULES,
        {
            "rule_type": "room_rent_limit",
            "value": 5000.0,
            "page": 1,
            "clause": "1.2",
            "source_text": "Standard Room Rent Limit INR 5,000 / day"
        }
    ]

    result = FinancialCalculationEngine.calculate_out_of_pocket(
        base_min_cost=100000.0,
        base_max_cost=100000.0,
        procedure_name="Appendectomy",
        city="Mumbai",
        room_category="Deluxe",
        policy_rules=rules
    )

    # Does not apply arbitrary 30% deduction
    assert result["eligible_amount"]["max"] == 100000.0
    assert result["confidence"] == "MEDIUM"
    assert "proportionate deduction" in result["confidence_reason"]

def test_13_sum_insured_limitation():
    """TEST 13: Available Sum Insured limits insurance contribution."""
    rules = [
        {
            "rule_type": "sum_insured",
            "value": 200000.0,  # Sum Insured capped at 2,00,000
            "unit": "INR",
            "page": 1,
            "clause": "1.1",
            "source_text": "Base policy Sum Insured: INR 2,00,000"
        },
        {
            "rule_type": "copay",
            "value": 0.0,
            "unit": "percent",
            "page": 2,
            "clause": "2.1",
            "source_text": "Zero co-payment applies"
        }
    ]

    # Treatment costs 3,00,000 - 4,00,000 (exceeding sum insured of 2,00,000)
    result = FinancialCalculationEngine.calculate_out_of_pocket(
        base_min_cost=300000.0,
        base_max_cost=400000.0,
        procedure_name="Angioplasty",
        city="Mumbai",
        room_category="Standard",
        policy_rules=rules
    )

    assert result["status"] == "calculated"
    assert result["eligible_amount"]["min"] == 200000.0
    assert result["eligible_amount"]["max"] == 200000.0
    assert result["insurance_contribution"]["min"] == 200000.0
    assert result["insurance_contribution"]["max"] == 200000.0
    # Patient pays remaining balance:
    # Min: 300,000 - 200,000 = 100,000
    # Max: 400,000 - 200,000 = 200,000
    assert result["patient_payable"]["min"] == 100000.0
    assert result["patient_payable"]["max"] == 200000.0

def test_14_successful_complete_calculation():
    """TEST 14: Successful complete calculation with exact deterministic values."""
    rules = [
        *BASE_VALID_RULES,
        {
            "rule_type": "sub_limit",
            "rule_key": "Appendectomy",
            "value": 90000.0,
            "unit": "INR",
            "page": 2,
            "clause": "2.3",
            "source_text": "Appendectomy procedure sub-limit: INR 90,000"
        }
    ]

    # Appendectomy Pune: Cost 75,000 - 95,000, Sublimit 90,000, Copay 10%
    result = FinancialCalculationEngine.calculate_out_of_pocket(
        base_min_cost=75000.0,
        base_max_cost=95000.0,
        procedure_name="Appendectomy",
        city="Pune",
        room_category="Standard",
        policy_rules=rules
    )

    assert result["status"] == "calculated"
    assert result["confidence"] == "HIGH"
    assert result["treatment_cost"]["min"] == 75000.0
    assert result["treatment_cost"]["max"] == 95000.0
    assert result["applicable_sublimit"] == 90000.0
    # Eligible: min(75000, 90000)=75000, min(95000, 90000)=90000
    assert result["eligible_amount"]["min"] == 75000.0
    assert result["eligible_amount"]["max"] == 90000.0
    # Copay (10%): 7,500 to 9,000
    assert result["copay_percent"] == 10.0
    assert result["copay_amount"]["min"] == 7500.0
    assert result["copay_amount"]["max"] == 9000.0
    # Insurance: 75,000 - 7,500 = 67,500; 90,000 - 9,000 = 81,000
    assert result["insurance_contribution"]["min"] == 67500.0
    assert result["insurance_contribution"]["max"] == 81000.0
    # Patient OOP: 75,000 - 67,500 = 7,500; 95,000 - 81,000 = 14,000
    assert result["patient_payable"]["min"] == 7500.0
    assert result["patient_payable"]["max"] == 14000.0
    assert len(result["citations"]) >= 3
