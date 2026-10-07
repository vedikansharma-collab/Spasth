import pytest
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.calculation.engine import FinancialCalculationEngine
from app.database.db import init_db, get_db

def setup_module(module):
    init_db()

def test_cost_lookup_and_copay_calculation():
    # Base scenario: Appendectomy in Pune (₹75k - ₹95k), 10% co-pay
    rules = [
        {"rule_type": "sum_insured", "value": 500000.0, "page": 1, "clause": "1.1", "source_text": "Sum Insured: 500,000"},
        {"rule_type": "copay", "value": 10.0, "page": 2, "clause": "2.1", "source_text": "10% Co-Payment mandatory"}
    ]

    result = FinancialCalculationEngine.calculate_out_of_pocket(
        base_min_cost=75000.0,
        base_max_cost=95000.0,
        procedure_name="Appendectomy",
        city="Pune",
        room_category="Standard",
        policy_rules=rules
    )

    assert result["procedure"] == "Appendectomy"
    assert result["city"] == "Pune"
    assert result["treatment_cost_range"]["min"] == 75000.0
    assert result["treatment_cost_range"]["max"] == 95000.0
    
    # Coverage should be 90% of base cost (10% copay applied)
    assert result["estimated_coverage_range"]["min"] == 67500.0
    assert result["estimated_coverage_range"]["max"] == 85500.0
    
    # OOP should be 10% of base cost
    assert result["estimated_oop_range"]["min"] == 7500.0
    assert result["estimated_oop_range"]["max"] == 9500.0
    assert len(result["citations"]) == 2
    assert result["confidence"] == "HIGH"
    print("Cost lookup & Co-pay calculation test PASSED!")

def test_procedure_sub_limit_calculation():
    # Cataract procedure (Cost ₹45k - ₹65k) with ₹40k sub-limit cap
    rules = [
        {"rule_type": "copay", "value": 10.0, "page": 2, "clause": "2.1", "source_text": "10% Copay"},
        {"rule_type": "sub_limit", "rule_key": "Cataract Surgery", "value": 40000.0, "page": 2, "clause": "2.2", "source_text": "Cataract cap: INR 40,000"}
    ]

    result = FinancialCalculationEngine.calculate_out_of_pocket(
        base_min_cost=45000.0,
        base_max_cost=65000.0,
        procedure_name="Cataract Surgery",
        city="Mumbai",
        room_category="Standard",
        policy_rules=rules
    )

    # Sub-limit caps eligible expense at 40,000
    assert result["eligible_amount_range"]["max"] == 40000.0
    # 90% of 40,000 covered = 36,000
    assert result["estimated_coverage_range"]["max"] == 36000.0
    # OOP max = 65,000 - 36,000 = 29,000
    assert result["estimated_oop_range"]["max"] == 29000.0
    print("Procedure sub-limit calculation test PASSED!")

def test_room_rent_proportionate_deduction():
    # Deluxe room upgrade scenario triggers 30% proportionate deduction penalty
    rules = [
        {"rule_type": "copay", "value": 10.0, "page": 2, "clause": "2.1", "source_text": "10% Copay"},
        {"rule_type": "room_rent_limit", "value": 5000.0, "page": 1, "clause": "1.2", "source_text": "Room cap INR 5,000. 30% proportionate deduction penalty applies for room category upgrades."}
    ]

    result = FinancialCalculationEngine.calculate_out_of_pocket(
        base_min_cost=100000.0,
        base_max_cost=100000.0,
        procedure_name="Appendectomy",
        city="Mumbai",
        room_category="Deluxe",
        policy_rules=rules
    )

    # Eligible amount reduced by 30% penalty ratio (0.70 * 100k = 70k)
    assert result["eligible_amount_range"]["max"] == 70000.0
    # 90% of 70k covered = 63,000
    assert result["estimated_coverage_range"]["max"] == 63000.0
    # OOP = 100,000 - 63,000 = 37,000
    assert result["estimated_oop_range"]["max"] == 37000.0
    print("Room rent proportionate deduction penalty test PASSED!")

def test_citation_preservation():
    rules = [
        {"rule_type": "copay", "value": 15.0, "page": 14, "clause": "Clause 4.2", "source_text": "15% Co-payment applies"}
    ]

    result = FinancialCalculationEngine.calculate_out_of_pocket(
        base_min_cost=50000.0,
        base_max_cost=50000.0,
        procedure_name="C-Section",
        city="Pune",
        room_category="Standard",
        policy_rules=rules
    )

    citations = result["citations"]
    assert len(citations) >= 1
    assert citations[0]["page"] == 14
    assert citations[0]["clause"] == "Clause 4.2"
    assert "15% Co-payment" in citations[0]["source_text"]
    print("Citation preservation test PASSED!")

def test_prompt_step12_required_cases():
    # TEST 1: Treatment = 100000, Sub-limit = 80000, Co-pay = 10%
    # Expected: Eligible = 80000, Coverage = 72000, OOP = 28000
    rules1 = [
        {"rule_type": "sum_insured", "value": 500000.0, "page": 1, "clause": "1.1", "source_text": "Sum Insured: 500,000"},
        {"rule_type": "sub_limit", "rule_key": "Appendectomy", "value": 80000.0, "page": 2, "clause": "2.2", "source_text": "Appendectomy cap: INR 80,000"},
        {"rule_type": "copay", "value": 10.0, "page": 2, "clause": "2.1", "source_text": "10% Co-Payment"}
    ]
    res1 = FinancialCalculationEngine.calculate_out_of_pocket(
        base_min_cost=100000.0, base_max_cost=100000.0, procedure_name="Appendectomy", city="Pune", room_category="Standard", policy_rules=rules1
    )
    assert res1["eligible_amount_range"]["min"] == 80000.0
    assert res1["estimated_coverage_range"]["min"] == 72000.0
    assert res1["estimated_oop_range"]["min"] == 28000.0

    # TEST 2: Treatment = 50000, Sub-limit = 80000, Co-pay = 10%
    # Expected: Eligible = 50000, Coverage = 45000, OOP = 5000
    res2 = FinancialCalculationEngine.calculate_out_of_pocket(
        base_min_cost=50000.0, base_max_cost=50000.0, procedure_name="Appendectomy", city="Pune", room_category="Standard", policy_rules=rules1
    )
    assert res2["eligible_amount_range"]["min"] == 50000.0
    assert res2["estimated_coverage_range"]["min"] == 45000.0
    assert res2["estimated_oop_range"]["min"] == 5000.0

    # TEST 3: Treatment range = 75000-95000, Sub-limit = 80000, Co-pay = 10%
    # Expected: Coverage = 67500-72000, OOP = 7500-23000
    res3 = FinancialCalculationEngine.calculate_out_of_pocket(
        base_min_cost=75000.0, base_max_cost=95000.0, procedure_name="Appendectomy", city="Pune", room_category="Standard", policy_rules=rules1
    )
    assert res3["estimated_coverage_range"]["min"] == 67500.0
    assert res3["estimated_coverage_range"]["max"] == 72000.0
    assert res3["estimated_oop_range"]["min"] == 7500.0
    assert res3["estimated_oop_range"]["max"] == 23000.0

    # TEST 4: Missing cost benchmark / policy parameter uncertainty handling
    res4 = FinancialCalculationEngine.calculate_out_of_pocket(
        base_min_cost=0.0, base_max_cost=0.0, procedure_name="Unknown Procedure", city="Pune", room_category="Standard", policy_rules=rules1, cost_found=False
    )
    assert res4["status"] == "UNABLE_TO_ESTIMATE"
    assert res4["confidence"] == "LOW"
    assert res4["estimated_coverage_range"]["min"] == 0.0

    # TEST 5: Co-pay = 0%
    # Expected: Coverage = eligible amount.
    rules5 = [
        {"rule_type": "sum_insured", "value": 500000.0, "page": 1, "clause": "1.1", "source_text": "Sum Insured: 500,000"},
        {"rule_type": "sub_limit", "rule_key": "Appendectomy", "value": 80000.0, "page": 2, "clause": "2.2", "source_text": "Appendectomy cap: INR 80,000"},
        {"rule_type": "copay", "value": 0.0, "page": 2, "clause": "2.1", "source_text": "0% Co-Payment"}
    ]
    res5 = FinancialCalculationEngine.calculate_out_of_pocket(
        base_min_cost=75000.0, base_max_cost=95000.0, procedure_name="Appendectomy", city="Pune", room_category="Standard", policy_rules=rules5
    )
    assert res5["estimated_coverage_range"]["min"] == 75000.0
    assert res5["estimated_coverage_range"]["max"] == 80000.0
    assert res5["estimated_oop_range"]["min"] == 0.0
    assert res5["estimated_oop_range"]["max"] == 15000.0

if __name__ == "__main__":
    test_cost_lookup_and_copay_calculation()
    test_procedure_sub_limit_calculation()
    test_room_rent_proportionate_deduction()
    test_citation_preservation()
    test_prompt_step12_required_cases()

