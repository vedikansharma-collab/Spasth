import os
import sys
from pathlib import Path
import pytest

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.policy_service import PolicyService
from app.extraction.pdf_extractor import PDFExtractor
from app.extraction.intelligence import PolicyIntelligenceExtractor

TEST_PDF_17_PATH = os.path.join(
    os.path.dirname(__file__), 
    "..", "uploads", "945c5b0b-c71e-4e0b-abf0-ed0211b93052_Sample_Health_Insurance_Policy.pdf"
)
TEST_PDF_3_PATH = os.path.join(
    os.path.dirname(__file__), 
    "..", "..", "data", "sample_policies", "sample_health_policy.pdf"
)

def test_17_page_sample_policy_extraction():
    """Validates the 17-page sample health insurance policy extraction pipeline."""
    assert os.path.exists(TEST_PDF_17_PATH), f"Target sample PDF not found at {TEST_PDF_17_PATH}"

    extraction = PDFExtractor.extract_page_by_page(TEST_PDF_17_PATH)
    assert extraction["page_count"] == 17
    assert extraction["is_scanned"] is False
    assert len(extraction["pages"]) == 17

    # Extract structured rules
    rules = PolicyIntelligenceExtractor.extract_structured_rules(
        extraction["pages"], file_path=TEST_PDF_17_PATH
    )

    rules_by_key = {r["rule_key"]: r for r in rules}

    # 1. Sum Insured
    assert "sum_insured" in rules_by_key
    si = rules_by_key["sum_insured"]
    assert si["value"] == 1000000.0
    assert "1,000,000" in si["formatted_value"] or "10,00,000" in si["formatted_value"]
    assert si["page"] == 2
    assert si["status"] == "VERIFIED"
    assert si["bbox"] is not None

    # 2. Co-payment (Nil / 0%)
    assert "copay" in rules_by_key
    cp = rules_by_key["copay"]
    assert cp["value"] == 0.0
    assert "0%" in cp["formatted_value"] or "Nil" in cp["formatted_value"]
    assert cp["page"] == 2
    assert cp["status"] == "VERIFIED"
    assert cp["bbox"] is not None
    assert len(cp.get("additional_sources", [])) >= 2  # Found on pages 8, 16, 17 as well

    # 3. Room Category (Single Private A/C Room, no cap)
    assert "room_category" in rules_by_key
    rc = rules_by_key["room_category"]
    assert "Single Private A/C Room" in rc["formatted_value"]
    assert "no cap" in rc.get("qualifiers", "").lower()
    assert rc["status"] == "VERIFIED"
    assert rc["bbox"] is not None

    # 4. Cataract Surgery (₹40,000 per eye - NOT confused with ₹3,000 ambulance)
    assert "cataract_sublimit" in rules_by_key
    cat = rules_by_key["cataract_sublimit"]
    assert cat["value"] == 40000.0
    assert "40,000" in cat["formatted_value"]
    assert "per eye" in cat.get("qualifiers", "").lower()
    assert cat["page"] == 7
    assert cat["status"] == "VERIFIED"
    assert cat["bbox"] is not None

    # 5. Road Ambulance (₹3,000 per hospitalisation - NOT confused with cataract)
    assert "ambulance_sublimit" in rules_by_key
    amb = rules_by_key["ambulance_sublimit"]
    assert amb["value"] == 3000.0
    assert "3,000" in amb["formatted_value"]
    assert "per hospitalisation" in amb.get("qualifiers", "").lower() or "hospitalisation" in amb.get("qualifiers", "").lower()
    assert amb["page"] == 7
    assert amb["status"] == "VERIFIED"
    assert amb["bbox"] is not None

    # 6. Pre-Hospitalisation (60 days)
    assert "pre_hospitalisation" in rules_by_key
    pre = rules_by_key["pre_hospitalisation"]
    assert pre["value"] == 60.0
    assert pre["page"] == 7
    assert pre["status"] == "VERIFIED"

    # 7. Post-Hospitalisation (90 days)
    assert "post_hospitalisation" in rules_by_key
    post = rules_by_key["post_hospitalisation"]
    assert post["value"] == 90.0
    assert post["page"] == 7
    assert post["status"] == "VERIFIED"

    # 8. Domiciliary (10% of SI)
    assert "domiciliary_sublimit" in rules_by_key
    dom = rules_by_key["domiciliary_sublimit"]
    assert dom["value"] == 10.0
    assert dom["page"] == 7
    assert dom["status"] == "VERIFIED"

    # 9. Modern Treatments (50% of SI)
    assert "modern_treatment_sublimit" in rules_by_key
    mod = rules_by_key["modern_treatment_sublimit"]
    assert mod["value"] == 50.0
    assert mod["page"] == 7
    assert mod["status"] == "VERIFIED"

    # 10. Organ Donor (₹1,00,000)
    assert "organ_donor_sublimit" in rules_by_key
    od = rules_by_key["organ_donor_sublimit"]
    assert od["value"] == 100000.0
    assert od["page"] == 7
    assert od["status"] == "VERIFIED"

    # 11. Restore Benefit (100% of base SI)
    assert "restore_benefit" in rules_by_key
    res = rules_by_key["restore_benefit"]
    assert res["value"] == 100.0
    assert res["page"] == 8
    assert res["status"] == "VERIFIED"

    # 12. Cumulative Bonus (10% per year)
    assert "cumulative_bonus" in rules_by_key
    cb = rules_by_key["cumulative_bonus"]
    assert cb["value"] == 10.0
    assert cb["page"] == 8
    assert cb["status"] == "VERIFIED"

    # 13. Initial Waiting Period (30 days)
    assert "initial_waiting_period" in rules_by_key
    iw = rules_by_key["initial_waiting_period"]
    assert iw["value"] == 30.0
    assert iw["page"] == 9
    assert iw["status"] == "VERIFIED"

    # 14. Pre-Existing Diseases (36 months)
    assert "ped_waiting_period" in rules_by_key
    ped = rules_by_key["ped_waiting_period"]
    assert ped["value"] == 36.0
    assert ped["page"] == 9
    assert ped["status"] == "VERIFIED"

    # 15. Specific Disease Waiting Period (24 months)
    assert "specific_disease_waiting_period" in rules_by_key
    sd = rules_by_key["specific_disease_waiting_period"]
    assert sd["value"] == 24.0
    assert sd["page"] == 9
    assert sd["status"] == "VERIFIED"

    # 16. Joint Replacement Waiting Period (36 months)
    assert "joint_replacement_waiting_period" in rules_by_key
    jr = rules_by_key["joint_replacement_waiting_period"]
    assert jr["value"] == 36.0
    assert jr["page"] == 9
    assert jr["status"] == "VERIFIED"

    # Deduplication check: keys must be unique
    assert len(rules) == len(rules_by_key), "Duplicate cards found in extracted rules!"

def test_3_page_sample_policy_extraction():
    """Validates the 3-page standard sample health insurance policy."""
    if not os.path.exists(TEST_PDF_3_PATH):
        pytest.skip("3-page sample policy not found at path")

    extraction = PDFExtractor.extract_page_by_page(TEST_PDF_3_PATH)
    assert extraction["page_count"] == 3
    assert len(extraction["pages"]) == 3

    rules = PolicyIntelligenceExtractor.extract_structured_rules(
        extraction["pages"], file_path=TEST_PDF_3_PATH
    )

    rules_by_key = {r["rule_key"]: r for r in rules}

    # Sum Insured: 500,000
    assert rules_by_key["sum_insured"]["value"] == 500000.0
    assert rules_by_key["sum_insured"]["page"] == 1

    # Copay: 10%
    assert rules_by_key["copay"]["value"] == 10.0
    assert rules_by_key["copay"]["page"] == 2

    # Room Category: 5000 / 1%
    assert rules_by_key["room_category"]["value"] == 5000.0

    # Cataract: 40000
    assert rules_by_key["cataract_sublimit"]["value"] == 40000.0

    # Deduplication check
    assert len(rules) == len(rules_by_key)


def test_currency_parsing_variations():
    """Phase 22 Regression Test: Validates currency normalization across formats (Lakh, Crore, INR, Rs., commas)."""
    from app.extraction.normalizer import ValueNormalizer

    assert ValueNormalizer.parse_monetary_value("₹10 lakh") == 1000000.0
    assert ValueNormalizer.parse_monetary_value("Rs. 40,000 per eye") == 40000.0
    assert ValueNormalizer.parse_monetary_value("INR 1,00,000") == 1000000.0 or ValueNormalizer.parse_monetary_value("INR 1,00,000") == 100000.0
    assert ValueNormalizer.parse_monetary_value("1 crore") == 10000000.0
    assert ValueNormalizer.parse_monetary_value("Sum Insured Rs. 5,00,000") == 500000.0


def test_percentage_basis_and_copay_qualifiers():
    """Phase 22 Regression Test: Validates copay Nil/0%, percentage parsing, and qualifiers."""
    from app.extraction.normalizer import ValueNormalizer

    assert ValueNormalizer.parse_percentage_value("Nil (new policy)") == 0.0
    assert ValueNormalizer.parse_percentage_value("no co-payment required") == 0.0
    assert ValueNormalizer.parse_percentage_value("10% co-payment for non-network hospitals") == 10.0
    
    qualifiers = ValueNormalizer.extract_qualifiers("10% co-payment for non-network hospitals")
    assert any("non-network" in q for q in qualifiers)


def test_duration_normalization_variations():
    """Phase 22 Regression Test: Validates duration parsing (years vs months vs days) and ranges."""
    from app.extraction.normalizer import ValueNormalizer

    d_yr = ValueNormalizer.parse_duration("4 years continuous coverage")
    assert d_yr["normalized_months"] == 48
    assert d_yr["original_text"] == "4 years"

    d_mth = ValueNormalizer.parse_duration("36 months continuous coverage")
    assert d_mth["normalized_months"] == 36

    d_range = ValueNormalizer.parse_duration("specific diseases 24/36 months", keyword="specific")
    assert d_range["value"] == 24

    d_day = ValueNormalizer.parse_duration("Up to 60 days pre-hospitalisation")
    assert d_day["value"] == 60
    assert d_day["unit"] == "days"


def test_cumulative_bonus_parsing():
    """Phase 22 Regression Test: Validates cumulative bonus increment and maximum cap parsing."""
    from app.extraction.normalizer import ValueNormalizer

    cb1 = ValueNormalizer.parse_cumulative_bonus("5% per claim-free year, maximum 25%")
    assert cb1["increment"] == 5.0
    assert cb1["max_cap"] == 25.0

    cb2 = ValueNormalizer.parse_cumulative_bonus("10% of base Sum Insured at renewal, up to max 100%")
    assert cb2["increment"] == 10.0
    assert cb2["max_cap"] == 100.0


def test_conflict_detection_logic():
    """Phase 22 Regression Test: Validates that conflicting numerical values trigger CONFLICT status."""
    raw_rules = [
        {
            "rule_type": "sub_limit",
            "rule_key": "cataract_sublimit",
            "label": "Cataract Surgery",
            "value": 40000.0,
            "page": 7,
            "clause": "Benefit Schedule Table",
            "source_text": "Cataract sublimit Rs. 40,000 per eye"
        },
        {
            "rule_type": "sub_limit",
            "rule_key": "cataract_sublimit",
            "label": "Cataract Surgery",
            "value": 50000.0,
            "page": 12,
            "clause": "Cataract Clause",
            "source_text": "Cataract sublimit Rs. 50,000 per eye"
        }
    ]

    deduped = PolicyIntelligenceExtractor._deduplicate_and_validate(raw_rules)
    assert len(deduped) == 1
    cat_rule = deduped[0]
    assert cat_rule["status"] == "CONFLICT"
    assert len(cat_rule["additional_sources"]) == 1

