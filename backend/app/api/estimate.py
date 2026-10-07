from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any

from app.database.db import get_db
from app.services.policy_service import PolicyService
from app.extraction.intelligence import PolicyIntelligenceExtractor
from app.calculation.engine import FinancialCalculationEngine
from app.schemas.estimate import EstimateRequest, EstimateResponse

from app.services.treatment_service import TreatmentService

router = APIRouter(tags=["Financial Estimation"])

def process_calculation_request(request: EstimateRequest) -> EstimateResponse:
    effective_procedure = request.get_effective_procedure()

    # 1. Fetch Policy & Preserved Pages
    policy = PolicyService.get_policy(request.policy_id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy with ID '{request.policy_id}' not found."
        )

    # 2. Check if Policy Rules exist in DB, else Extract & Cache them
    policy_rules: List[Dict[str, Any]] = []
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM policy_rules WHERE policy_id = ?;", (request.policy_id,))
        rows = cursor.fetchall()

        if rows:
            policy_rules = rows
        else:
            pages = policy.get("pages", [])
            extracted_rules = PolicyIntelligenceExtractor.extract_structured_rules(pages)

            for r in extracted_rules:
                cursor.execute("""
                    INSERT INTO policy_rules (
                        policy_id, rule_type, rule_key, value, unit, page, clause, source_text, confidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    request.policy_id,
                    r["rule_type"],
                    r.get("rule_key", r["rule_type"]),
                    r.get("value"),
                    r.get("unit"),
                    r.get("page", 1),
                    r.get("clause", "N/A"),
                    r.get("source_text", ""),
                    r.get("confidence", "HIGH")
                ))
            policy_rules = extracted_rules

    # 3. Lookup Procedure & City Cost Range using TreatmentService (Step 4 & 5)
    treatment_data = TreatmentService.get_treatment_cost(effective_procedure, request.city)
    base_min_cost = 0.0
    base_max_cost = 0.0
    source_name = "State Healthcare Package Benchmark 2025"
    data_type_val = "synthetic"
    city_tier_val = "Tier-1"
    cost_found = False

    if treatment_data:
        base_min_cost = treatment_data["cost_min"]
        base_max_cost = treatment_data["cost_max"]
        source_name = treatment_data["source"]
        data_type_val = treatment_data.get("data_type", "synthetic")
        city_tier_val = treatment_data.get("city_tier", "Tier-1")
        cost_found = True

    # 4. Prepare scenario payload
    scenario = dict(request.scenario or {})
    if request.condition:
        scenario["condition"] = request.condition
        if "pre-existing" in request.condition.lower() or "ped" in request.condition.lower():
            scenario["is_ped"] = True

    # 5. Run Financial Calculation Engine (Phases 1, 3, 4, 5, 6, 7, 8, 9, 10, 14)
    calculation_result = FinancialCalculationEngine.calculate_out_of_pocket(
        base_min_cost=base_min_cost,
        base_max_cost=base_max_cost,
        procedure_name=effective_procedure,
        city=request.city,
        city_tier=city_tier_val,
        room_category=request.room_category,
        policy_rules=policy_rules,
        data_source=source_name,
        data_type=data_type_val,
        cost_found=cost_found,
        scenario=scenario
    )

    return EstimateResponse(
        policy_id=request.policy_id,
        procedure=effective_procedure,
        city=request.city,
        room_category=request.room_category,
        treatment_cost_range=calculation_result["treatment_cost_range"],
        eligible_amount_range=calculation_result["eligible_amount_range"],
        estimated_coverage_range=calculation_result["estimated_coverage_range"],
        estimated_oop_range=calculation_result["estimated_oop_range"],
        applied_rules=calculation_result.get("applied_rules", []),
        citations=calculation_result.get("citations", []),
        confidence=calculation_result.get("confidence", "LOW"),
        confidence_reason=calculation_result.get("confidence_reason") or calculation_result.get("message", "Evidence verified"),
        data_source=calculation_result.get("data_source", source_name),
        data_type=calculation_result.get("data_type", data_type_val),
        status=calculation_result.get("status", "calculated"),
        treatment_cost=calculation_result.get("treatment_cost"),
        applicable_sublimit=calculation_result.get("applicable_sublimit"),
        eligible_amount=calculation_result.get("eligible_amount"),
        copay_percent=calculation_result.get("copay_percent"),
        copay_amount=calculation_result.get("copay_amount"),
        insurance_contribution=calculation_result.get("insurance_contribution"),
        patient_payable=calculation_result.get("patient_payable"),
        rules_applied=calculation_result.get("rules_applied"),
        evidence=calculation_result.get("evidence"),
        coverage_checks=calculation_result.get("coverage_checks")
    )

@router.post("/estimate", response_model=EstimateResponse)
def calculate_estimate_endpoint(request: EstimateRequest):
    """
    POST /api/estimate
    Calculates deterministic insurance coverage and out-of-pocket expenses.
    """
    return process_calculation_request(request)

@router.post("/calculate", response_model=EstimateResponse)
def calculate_endpoint(request: EstimateRequest):
    """
    POST /api/calculate
    Alias endpoint for Treatment Cost Calculation.
    """
    return process_calculation_request(request)
