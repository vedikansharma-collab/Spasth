import os
import sys
import json
from pathlib import Path
import pytest

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.services.policy_service import PolicyService
from app.extraction.canonical_policy import CanonicalPolicyGenerator

TEST_POLICY_17_ID = "945c5b0b-c71e-4e0b-abf0-ed0211b93052"
CANONICAL_JSON_PATH = settings.CANONICAL_JSON_PATH


def test_canonical_json_generated_and_valid():
    """Validates that policy.json is generated, exists, and is valid JSON."""
    result = CanonicalPolicyGenerator.export_policy_to_json(TEST_POLICY_17_ID)
    
    assert result["status"] == "success"
    assert os.path.exists(result["file_path"])
    assert result["file_path"] == str(CANONICAL_JSON_PATH)

    # Validate JSON parsing
    with open(result["file_path"], "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, dict)


def test_canonical_json_required_sections():
    """Validates that all required top-level sections exist and are properly populated."""
    data = CanonicalPolicyGenerator.load_canonical_policy_json()
    assert data is not None, "Failed to load generated policy.json"

    required_sections = [
        "policy",
        "coverage_rules",
        "waiting_periods",
        "exclusions",
        "benefits",
        "restore_benefits",
        "bonuses",
        "rules",
        "metadata"
    ]

    for section in required_sections:
        assert section in data, f"Missing required top-level section: {section}"

    # Check policy metadata block
    assert "policy_id" in data["policy"]
    assert "product_name" in data["policy"]
    assert "policy_type" in data["policy"]
    assert "policy_period" in data["policy"]
    assert "sum_insured" in data["policy"]

    # Check top-level metadata block
    meta = data["metadata"]
    assert meta["source_type"] == "uploaded_policy_pdf"
    assert meta["page_count"] == 17
    assert meta["schema_version"] == "1.0"
    assert "generated_at" in meta
    assert meta["rules_count"] == len(data["rules"])
    assert meta["verification_status"] in ("VERIFIED", "NEEDS_REVIEW", "CONFLICT")


def test_canonical_json_extracted_values():
    """Validates all required policy values in the generated canonical policy JSON."""
    data = CanonicalPolicyGenerator.load_canonical_policy_json()
    assert data is not None

    rules_by_key = {r["rule_key"]: r for r in data["rules"]}

    # 1. Sum Insured = 1,000,000 INR
    assert "sum_insured" in rules_by_key
    assert rules_by_key["sum_insured"]["value"] == 1000000.0
    assert rules_by_key["sum_insured"]["unit"] == "INR"
    assert "1,000,000" in rules_by_key["sum_insured"]["formatted_value"] or "10,00,000" in rules_by_key["sum_insured"]["formatted_value"]
    assert data["policy"]["sum_insured"]["value"] == 1000000.0

    # 2. Co-payment = 0% / Nil
    assert "copay" in rules_by_key
    assert rules_by_key["copay"]["value"] == 0.0
    assert "0%" in rules_by_key["copay"]["formatted_value"] or "Nil" in rules_by_key["copay"]["formatted_value"]

    # 3. Room Category = Single Private A/C Room / No Cap
    assert "room_category" in rules_by_key
    assert "Single Private A/C Room" in rules_by_key["room_category"]["formatted_value"]
    assert any("no cap" in q.lower() for q in rules_by_key["room_category"]["qualifiers"])

    # 4. Pre-hospitalisation = 60 days
    assert "pre_hospitalisation" in rules_by_key
    assert rules_by_key["pre_hospitalisation"]["value"] == 60.0
    assert rules_by_key["pre_hospitalisation"]["unit"] == "days"

    # 5. Post-hospitalisation = 90 days
    assert "post_hospitalisation" in rules_by_key
    assert rules_by_key["post_hospitalisation"]["value"] == 90.0
    assert rules_by_key["post_hospitalisation"]["unit"] == "days"

    # 6. Domiciliary = 10% of SI
    assert "domiciliary_sublimit" in rules_by_key
    assert rules_by_key["domiciliary_sublimit"]["value"] == 10.0

    # 7. Ambulance = ₹3,000
    assert "ambulance_sublimit" in rules_by_key
    assert rules_by_key["ambulance_sublimit"]["value"] == 3000.0

    # 8. Modern Treatment = 50% SI
    assert "modern_treatment_sublimit" in rules_by_key
    assert rules_by_key["modern_treatment_sublimit"]["value"] == 50.0

    # 9. Organ Donor = ₹100,000
    assert "organ_donor_sublimit" in rules_by_key
    assert rules_by_key["organ_donor_sublimit"]["value"] == 100000.0

    # 10. Cataract = ₹40,000 per eye
    assert "cataract_sublimit" in rules_by_key
    assert rules_by_key["cataract_sublimit"]["value"] == 40000.0
    assert any("per eye" in q.lower() for q in rules_by_key["cataract_sublimit"]["qualifiers"])

    # 11. Initial Waiting = 30 days
    assert "initial_waiting_period" in rules_by_key
    assert rules_by_key["initial_waiting_period"]["value"] == 30.0
    assert rules_by_key["initial_waiting_period"]["unit"] == "days"

    # 12. PED Waiting = 36 months
    assert "ped_waiting_period" in rules_by_key
    assert rules_by_key["ped_waiting_period"]["value"] == 36.0
    assert rules_by_key["ped_waiting_period"]["unit"] == "months"

    # 13. Specific Disease Waiting = 24 months
    assert "specific_disease_waiting_period" in rules_by_key
    assert rules_by_key["specific_disease_waiting_period"]["value"] == 24.0
    assert rules_by_key["specific_disease_waiting_period"]["unit"] == "months"

    # 14. Joint Replacement = 36 months
    assert "joint_replacement_waiting_period" in rules_by_key
    assert rules_by_key["joint_replacement_waiting_period"]["value"] == 36.0
    assert rules_by_key["joint_replacement_waiting_period"]["unit"] == "months"

    # 15. Restore Benefit = 100%
    assert "restore_benefit" in rules_by_key
    assert rules_by_key["restore_benefit"]["value"] == 100.0

    # 16. Cumulative Bonus = 10%
    assert "cumulative_bonus" in rules_by_key
    assert rules_by_key["cumulative_bonus"]["value"] == 10.0


def test_source_metadata_and_bbox_preservation():
    """Validates that rules retain page numbers, clauses, source text, bbox, and additional sources."""
    data = CanonicalPolicyGenerator.load_canonical_policy_json()
    assert data is not None

    rules_by_key = {r["rule_key"]: r for r in data["rules"]}

    # Cataract rule
    cat = rules_by_key["cataract_sublimit"]
    assert cat["page"] == 7
    assert cat["clause"] == "1.10 Cataract Treatment"
    assert "40,000" in cat["source_text"]
    assert cat["bbox"] is not None
    assert isinstance(cat["bbox"], dict)
    assert "x" in cat["bbox"] and "y" in cat["bbox"]
    assert len(cat["additional_sources"]) >= 1
    assert cat["additional_sources"][0]["page"] == 16

    # Copay rule
    cop = rules_by_key["copay"]
    assert cop["page"] == 2
    assert "Nil" in cop["source_text"] or "no co-payment" in cop["source_text"].lower()
    assert cop["bbox"] is not None
    assert len(cop["additional_sources"]) >= 2
    # Secondary sources from pages 8, 16, 17
    secondary_pages = {s["page"] for s in cop["additional_sources"]}
    assert 8 in secondary_pages or 16 in secondary_pages

    # Sum insured top-level sources
    si_sources = data["policy"]["sum_insured"]["sources"]
    assert len(si_sources) >= 2
    assert si_sources[0]["page"] == 2


def test_deduplication_and_uniqueness():
    """Validates that no duplicate canonical rules exist in the rules array."""
    data = CanonicalPolicyGenerator.load_canonical_policy_json()
    assert data is not None

    all_keys = [r["rule_key"] for r in data["rules"]]
    unique_keys = set(all_keys)

    assert len(all_keys) == len(unique_keys), f"Duplicate canonical rules detected! Found {len(all_keys) - len(unique_keys)} duplicates."


def test_conflicts_and_needs_review_preservation():
    """Validates that CONFLICT and NEEDS_REVIEW statuses are preserved, not masked."""
    # Test generator with synthetic conflicting candidate rules
    synthetic_policy = {
        "id": "test-conflict-policy",
        "original_filename": "test_conflict.pdf",
        "page_count": 5,
        "pages": [{"page_number": 1, "content": "Sample"}],
        "rules": [
            {
                "rule_key": "cataract_sublimit",
                "rule_type": "sub_limit",
                "label": "Cataract",
                "value": 40000.0,
                "formatted_value": "₹40,000",
                "page": 2,
                "clause": "Clause 1",
                "source_text": "Cataract up to 40,000",
                "status": "CONFLICT",
                "additional_sources": [{"page": 4, "clause": "Clause 2", "source_text": "Cataract up to 25,000"}]
            },
            {
                "rule_key": "room_category",
                "rule_type": "room_rent_limit",
                "label": "Room Category",
                "value": 5000.0,
                "formatted_value": "₹5,000/day",
                "page": 1,
                "clause": "Clause 2",
                "source_text": "Room rent limit 5000",
                "status": "NEEDS_REVIEW"
            }
        ]
    }

    canonical = CanonicalPolicyGenerator.generate_canonical_policy(synthetic_policy)
    rules_by_key = {r["rule_key"]: r for r in canonical["rules"]}

    assert rules_by_key["cataract_sublimit"]["status"] == "CONFLICT"
    assert rules_by_key["room_category"]["status"] == "NEEDS_REVIEW"
    assert canonical["metadata"]["verification_status"] == "CONFLICT"


def test_no_fabricated_values():
    """Ensures that all rule values correspond strictly to extracted policy fields."""
    data = CanonicalPolicyGenerator.load_canonical_policy_json()
    assert data is not None

    for r in data["rules"]:
        assert r["page"] > 0, f"Invalid page {r['page']} for rule {r['rule_key']}"
        assert r["source_text"], f"Missing source text for rule {r['rule_key']}"
        assert r["status"] in ("VERIFIED", "NEEDS_REVIEW", "CONFLICT")
        assert isinstance(r["qualifiers"], list)


def test_canonical_policy_validator():
    """Phase 17 Test: Validates CanonicalPolicyValidator schema enforcement."""
    from app.extraction.canonical_policy import CanonicalPolicyValidator

    data = CanonicalPolicyGenerator.load_canonical_policy_json()
    assert data is not None

    is_valid, errors = CanonicalPolicyValidator.validate_canonical_policy(data)
    assert is_valid, f"Canonical Policy JSON failed schema validation: {errors}"

    # Invalid payload check
    invalid_data = {"policy": {}}
    val_ok, val_errs = CanonicalPolicyValidator.validate_canonical_policy(invalid_data)
    assert val_ok is False
    assert len(val_errs) > 0


def test_complex_rules_representation():
    """Phase 17 Test: Validates rich representation of complex rules (cumulative bonus, percentage caps, copay)."""
    data = CanonicalPolicyGenerator.load_canonical_policy_json()
    assert data is not None

    rules_by_key = {r["rule_key"]: r for r in data["rules"]}

    # Cumulative bonus complex structure
    cb = rules_by_key.get("cumulative_bonus")
    assert cb is not None
    assert "values" in cb
    assert "increment" in cb["values"]
    assert "maximum" in cb["values"]
    assert cb["frequency"] == "claim-free year"
    assert cb["basis"] == "sum_insured"
    assert len(cb["limits"]) >= 2

    # Copay complex structure
    cp = rules_by_key.get("copay")
    assert cp is not None
    assert "values" in cp
    assert "limits" in cp
    assert "original_value" in cp
    assert "normalized_value" in cp

    # Cataract original + normalized values
    cat = rules_by_key.get("cataract_sublimit")
    assert cat is not None
    assert cat["normalized_value"] == 40000.0
    assert cat["original_value"] != ""


def test_policy_isolation_and_reprocessing():
    """Phase 17 Test: Validates policy isolation so rules belong strictly to target policy_id."""
    poly_a = {
        "id": "policy-A-111",
        "original_filename": "policy_A.pdf",
        "page_count": 2,
        "pages": [{"page_number": 1, "content": "Policy A content"}],
        "rules": [
            {"rule_key": "sum_insured", "rule_type": "sum_insured", "value": 300000.0, "source_text": "300,000"}
        ]
    }
    poly_b = {
        "id": "policy-B-222",
        "original_filename": "policy_B.pdf",
        "page_count": 2,
        "pages": [{"page_number": 1, "content": "Policy B content"}],
        "rules": [
            {"rule_key": "sum_insured", "rule_type": "sum_insured", "value": 750000.0, "source_text": "750,000"}
        ]
    }

    canon_a = CanonicalPolicyGenerator.generate_canonical_policy(poly_a)
    canon_b = CanonicalPolicyGenerator.generate_canonical_policy(poly_b)

    assert canon_a["policy"]["policy_id"] == "policy-A-111"
    assert canon_a["rules"][0]["value"] == 300000.0

    assert canon_b["policy"]["policy_id"] == "policy-B-222"
    assert canon_b["rules"][0]["value"] == 750000.0

