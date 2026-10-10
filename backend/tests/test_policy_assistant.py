import os
import sys
from pathlib import Path
import pytest

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.rag.policy_assistant import PolicyAssistantEngine
from app.services.policy_service import PolicyService

# Sample canonical policy representing a real-world health policy
SAMPLE_CANONICAL_POLICY = {
    "policy_id": "test_pol_123",
    "document_id": "doc_123",
    "policy_metadata": {
        "policy_name": "Optima Secure Health Policy",
        "policy_number": "POL-998877",
        "sum_insured": "₹10,00,000",
        "product_type": "Health Insurance",
        "policy_period": "1 Year"
    },
    "pages": [
        {
            "page_number": 1,
            "content": "Optima Secure Health Insurance Policy Schedule\nDisclaimer: This is a sample document for testing contracts, but it is not a real insurance contract and must not be used to buy, claim or compare cover."
        },
        {
            "page_number": 2,
            "content": "Base Policy Sum Insured: Rs. 10,00,000\nCo-payment: Nil (0%)\nRoom Category: Single Private A/C Room"
        },
        {
            "page_number": 7,
            "content": "Pre-hospitalisation: Expenses up to 60 days prior to admission are covered.\nPost-hospitalisation: Expenses up to 90 days after discharge are covered.\nCataract Surgery: Sub-limit Rs. 40,000 per eye.\nRoad Ambulance: Rs. 3,000 per hospitalisation."
        },
        {
            "page_number": 8,
            "content": "Cumulative Bonus: 5% per claim-free year, maximum 25% of Sum Insured."
        },
        {
            "page_number": 9,
            "content": "Waiting Periods:\nInitial Waiting Period: 30 days\nSpecific Diseases (Cataract, Hernia, Joint Replacement): 24 months\nPre-Existing Diseases: 36 months"
        }
    ],
    "rules": [
        {
            "rule_id": "sum_insured",
            "name": "Sum Insured",
            "category": "coverage",
            "value": 1000000.0,
            "formatted_value": "₹10,00,000",
            "page": 2,
            "clause": "Policy Schedule",
            "source_text": "Sum Insured: Rs. 10,00,000",
            "status": "VERIFIED",
            "confidence": 0.98
        },
        {
            "rule_id": "copay",
            "name": "Co-payment",
            "category": "copayment",
            "value": 0.0,
            "formatted_value": "0% (Nil)",
            "qualifiers": "Nil co-payment",
            "conditions": "all hospitals",
            "page": 2,
            "clause": "Policy Schedule",
            "source_text": "Co-payment: Nil (0%)",
            "status": "VERIFIED",
            "confidence": 0.98
        },
        {
            "rule_id": "cataract_sublimit",
            "name": "Cataract Surgery",
            "category": "sublimit",
            "value": 40000.0,
            "formatted_value": "₹40,000",
            "qualifiers": "per eye",
            "page": 7,
            "clause": "Section 2.4",
            "source_text": "Cataract surgery capped at Rs. 40,000 per eye",
            "status": "VERIFIED",
            "confidence": 0.95
        },
        {
            "rule_id": "pre_hospitalisation",
            "name": "Pre-Hospitalisation",
            "category": "coverage",
            "value": 60.0,
            "formatted_value": "60 days",
            "page": 7,
            "clause": "Section 2.1",
            "source_text": "Expenses up to 60 days prior to admission are covered",
            "status": "VERIFIED",
            "confidence": 0.95
        },
        {
            "rule_id": "post_hospitalisation",
            "name": "Post-Hospitalisation",
            "category": "coverage",
            "value": 90.0,
            "formatted_value": "90 days",
            "page": 7,
            "clause": "Section 2.2",
            "source_text": "Expenses up to 90 days after discharge are covered",
            "status": "VERIFIED",
            "confidence": 0.95
        },
        {
            "rule_id": "specific_disease_waiting_period",
            "name": "Specific Disease Waiting Period",
            "category": "waiting_period",
            "value": 24.0,
            "formatted_value": "24 months",
            "qualifiers": "includes cataract and joint replacement",
            "page": 9,
            "clause": "Clause 4.2",
            "source_text": "24 months waiting period applies for cataract, hernia, and joint replacement",
            "status": "VERIFIED",
            "confidence": 0.95
        },
        {
            "rule_id": "ambulance_sublimit",
            "name": "Road Ambulance",
            "category": "sublimit",
            "value": 3000.0,
            "formatted_value": "₹3,000",
            "qualifiers": "per hospitalisation",
            "page": 7,
            "clause": "Section 2.8",
            "source_text": "Road ambulance covered up to Rs. 3,000 per hospitalisation",
            "status": "VERIFIED",
            "confidence": 0.95
        },
        {
            "rule_id": "cumulative_bonus",
            "name": "Cumulative Bonus",
            "category": "bonus",
            "values": {
                "increment": {"value": 5, "unit": "percent"},
                "maximum": {"value": 25, "unit": "percent", "basis": "sum_insured"}
            },
            "frequency": "claim-free year",
            "page": 8,
            "clause": "Section 3.2",
            "source_text": "5% per claim-free year, maximum 25% of Sum Insured",
            "status": "VERIFIED",
            "confidence": 0.95
        }
    ]
}

def test_1_copay_direct_query():
    """TEST 1: What is my co-pay?"""
    res = PolicyAssistantEngine.process_query("test_pol_123", "What is my co-pay?", SAMPLE_CANONICAL_POLICY)
    assert res["grounding_status"] == "GROUNDED"
    assert res["citations"][0]["page"] == 2
    assert "0%" in res["answer"] or "Nil" in res["answer"] or "no cost-sharing" in res["answer"].lower()

def test_2_copay_percentage_query():
    """TEST 2: Do I have to pay any percentage of my claim myself?"""
    res = PolicyAssistantEngine.process_query("test_pol_123", "Do I have to pay any percentage of my claim myself?", SAMPLE_CANONICAL_POLICY)
    assert res["grounding_status"] == "GROUNDED"
    assert res["citations"][0]["page"] == 2, f"Expected Page 2 co-pay citation, got Page {res['citations'][0]['page']}"
    assert "Page 1" not in res["citations"][0]["source_text"], "Must not cite Page 1 disclaimer"

def test_3_copay_percentage_claim_query():
    """TEST 3: What percentage of the claim do I have to pay?"""
    res = PolicyAssistantEngine.process_query("test_pol_123", "What percentage of the claim do I have to pay?", SAMPLE_CANONICAL_POLICY)
    assert res["grounding_status"] == "GROUNDED"
    assert res["citations"][0]["page"] == 2

def test_4_copay_how_much_query():
    """TEST 4: How much of the claim do I have to pay?"""
    res = PolicyAssistantEngine.process_query("test_pol_123", "How much of the claim do I have to pay?", SAMPLE_CANONICAL_POLICY)
    assert res["grounding_status"] == "GROUNDED"
    assert res["citations"][0]["page"] == 2

def test_5_cost_sharing_query():
    """TEST 5: Is there any cost sharing in my policy?"""
    res = PolicyAssistantEngine.process_query("test_pol_123", "Is there any cost sharing in my policy?", SAMPLE_CANONICAL_POLICY)
    assert res["grounding_status"] == "GROUNDED"
    assert res["citations"][0]["page"] == 2

def test_6_sum_insured_query():
    """TEST 6: What is my sum insured?"""
    res = PolicyAssistantEngine.process_query("test_pol_123", "What is my sum insured?", SAMPLE_CANONICAL_POLICY)
    assert res["grounding_status"] == "GROUNDED"
    assert "10,00,000" in res["answer"] or "1000000" in res["answer"]
    assert res["citations"][0]["page"] == 2

def test_7_coverage_query():
    """TEST 7: How much coverage do I have?"""
    res = PolicyAssistantEngine.process_query("test_pol_123", "How much coverage do I have?", SAMPLE_CANONICAL_POLICY)
    assert res["grounding_status"] == "GROUNDED"
    assert "10,00,000" in res["answer"] or "1000000" in res["answer"]
    assert res["citations"][0]["page"] == 2

def test_8_pre_hospitalisation_query():
    """TEST 8: How many days before hospitalization are covered?"""
    res = PolicyAssistantEngine.process_query("test_pol_123", "How many days before hospitalization are covered?", SAMPLE_CANONICAL_POLICY)
    assert res["grounding_status"] == "GROUNDED"
    assert "60 days" in res["answer"] or "60" in res["answer"]
    assert res["citations"][0]["page"] == 7

def test_9_post_hospitalisation_query():
    """TEST 9: What expenses after hospitalization are covered?"""
    res = PolicyAssistantEngine.process_query("test_pol_123", "What expenses after hospitalization are covered?", SAMPLE_CANONICAL_POLICY)
    assert res["grounding_status"] == "GROUNDED"
    assert "90 days" in res["answer"] or "90" in res["answer"]
    assert res["citations"][0]["page"] == 7

def test_10_cataract_limit_query():
    """TEST 10: What is the cataract limit?"""
    res = PolicyAssistantEngine.process_query("test_pol_123", "What is the cataract limit?", SAMPLE_CANONICAL_POLICY)
    assert res["grounding_status"] == "GROUNDED"
    assert "40,000" in res["answer"]
    assert res["citations"][0]["page"] == 7

def test_11_cataract_waiting_period_query():
    """TEST 11: What is the waiting period for cataract?"""
    res = PolicyAssistantEngine.process_query("test_pol_123", "What is the waiting period for cataract?", SAMPLE_CANONICAL_POLICY)
    assert res["grounding_status"] == "GROUNDED"
    assert "24 months" in res["answer"] or "24" in res["answer"]
    assert res["citations"][0]["page"] == 9

def test_12_genuinely_absent_query():
    """TEST 12: Ask something genuinely absent (e.g. space travel)."""
    res = PolicyAssistantEngine.process_query("test_pol_123", "Does my policy cover space travel?", SAMPLE_CANONICAL_POLICY)
    assert res["grounding_status"] == "NOT_FOUND"
    assert "could not find a specific provision" in res["answer"].lower()
    assert res["confidence"] < 0.50

def test_13_semantic_relationship_cumulative_bonus():
    """TEST 13: Semantic relationship preservation for cumulative bonus."""
    res = PolicyAssistantEngine.process_query("test_pol_123", "What is the cumulative bonus?", SAMPLE_CANONICAL_POLICY)
    assert res["grounding_status"] == "GROUNDED"
    assert "5%" in res["answer"]
    assert "25%" in res["answer"]
    assert "maximum" in res["answer"].lower() or "capped" in res["answer"].lower()
    # Must NOT state 25% per year
    assert "25% per year" not in res["answer"].lower()

def test_14_dual_limits_capped_rule():
    """TEST 14: Dual limits (% of SI capped at currency limit)."""
    dual_policy = {
        "policy_id": "dual_pol_123",
        "rules": [
            {
                "rule_id": "room_rent_limit",
                "name": "Room Rent Limit",
                "limits": [
                    {"value": 1.0, "unit": "percent", "basis": "Sum Insured"},
                    {"value": 1500, "unit": "INR", "basis": "absolute cap"}
                ],
                "page": 3,
                "clause": "Clause 2.1",
                "source_text": "1% of Sum Insured per policy period, capped at Rs. 1,500"
            }
        ]
    }
    res = PolicyAssistantEngine.process_query("dual_pol_123", "What is the room rent limit?", dual_policy)
    assert res["grounding_status"] == "GROUNDED"
    assert "1.0%" in res["answer"] or "1%" in res["answer"]
    assert "1,500" in res["answer"]
