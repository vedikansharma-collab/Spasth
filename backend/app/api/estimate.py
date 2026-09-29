from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any

from app.database.db import get_db
from app.services.policy_service import PolicyService
from app.extraction.intelligence import PolicyIntelligenceExtractor
from app.calculation.engine import FinancialCalculationEngine
from app.schemas.estimate import EstimateRequest, EstimateResponse

router = APIRouter(prefix="/estimate", tags=["Financial Estimation"])

@router.post("", response_model=EstimateResponse)
def calculate_estimate(request: EstimateRequest):
    """
    POST /api/estimate
    Combines extracted policy rules, treatment cost benchmarks, and user scenario
    to calculate deterministic insurance coverage and out-of-pocket expenses with citations.
    """
    # 1. Fetch Policy & Pages
    policy = PolicyService.get_policy(request.policy_id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy with ID {request.policy_id} not found."
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

    # 3. Lookup Procedure & City Cost Range in Treatment Costs DB
    base_min_cost = 0.0
    base_max_cost = 0.0
    source_name = "State Healthcare Package Benchmark 2025"
    data_type_val = "synthetic_demo"
    cost_found = False

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT min_cost, max_cost, source, data_type 
            FROM treatment_costs 
            WHERE LOWER(procedure_name) = LOWER(?) AND LOWER(city) = LOWER(?);
        """, (request.procedure, request.city))
        cost_row = cursor.fetchone()
        
        if cost_row:
            base_min_cost = cost_row["min_cost"]
            base_max_cost = cost_row["max_cost"]
            source_name = cost_row["source"]
            data_type_val = cost_row["data_type"]
            cost_found = True

    # 4. Run Financial Calculation Engine
    calculation_result = FinancialCalculationEngine.calculate_out_of_pocket(
        base_min_cost=base_min_cost,
        base_max_cost=base_max_cost,
        procedure_name=request.procedure,
        city=request.city,
        room_category=request.room_category,
        policy_rules=policy_rules,
        data_source=source_name,
        cost_found=cost_found
    )

    if calculation_result.get("status") == "UNABLE_TO_ESTIMATE":
        return EstimateResponse(
            policy_id=request.policy_id,
            procedure=request.procedure,
            city=request.city,
            room_category=request.room_category,
            treatment_cost_range={"min": 0, "max": 0},
            eligible_amount_range={"min": 0, "max": 0},
            estimated_coverage_range={"min": 0, "max": 0},
            estimated_oop_range={"min": 0, "max": 0},
            applied_rules=[],
            citations=[],
            confidence="LOW",
            confidence_reason=calculation_result.get("message", "Unable to confidently estimate cost."),
            data_source=source_name,
            data_type=data_type_val,
            status="UNABLE_TO_ESTIMATE"
        )

    return EstimateResponse(
        policy_id=request.policy_id,
        procedure=request.procedure,
        city=request.city,
        room_category=request.room_category,
        treatment_cost_range=calculation_result["treatment_cost_range"],
        eligible_amount_range=calculation_result["eligible_amount_range"],
        estimated_coverage_range=calculation_result["estimated_coverage_range"],
        estimated_oop_range=calculation_result["estimated_oop_range"],
        applied_rules=calculation_result["applied_rules"],
        citations=calculation_result["citations"],
        confidence=calculation_result["confidence"],
        confidence_reason=calculation_result.get("confidence_reason", "Verified policy evidence."),
        data_source=calculation_result["data_source"],
        data_type=data_type_val,
        status="SUCCESS"
    )
