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
        coverage_checks=calculation_result.get("coverage_checks"),
        calculation_trace=calculation_result.get("calculation_trace"),
        customer_payable_breakdown=calculation_result.get("customer_payable_breakdown"),
        currency="INR"
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

@router.post("/estimate/calculate-claim")
@router.post("/calculate-claim")
def calculate_claim_precision_endpoint(request: Dict[str, Any]):
    """
    POST /api/estimate/calculate-claim & POST /api/calculate-claim
    Direct interface to the Precision Math Engine.
    Resolves authoritative backend policy rules if policy_id is provided, preventing frontend overrides.
    """
    from app.services.math_engine import MathEngine
    from app.services.policy_service import PolicyService
    from app.services.treatment_service import TreatmentService
    from app.calculation.rule_matcher import TreatmentRuleMatcher
    from app.calculation.coverage_checker import CoverageChecker

    policy_id = request.get("policy_id")
    procedure_name = request.get("procedure_name") or request.get("procedure") or request.get("treatment")
    city = request.get("city") or "Pune"
    room_category = request.get("room_category") or "Standard"
    treatment_cost_input = request.get("treatment_cost")
    quantity = request.get("quantity", 1)
    non_covered_expense = request.get("non_covered_expense", 0.0)
    deductible = request.get("deductible", 0.0)
    condition = request.get("condition")
    scenario = dict(request.get("scenario") or {})
    if request.get("policy_tenure_months") is not None:
        try:
            scenario["policy_tenure_months"] = int(request.get("policy_tenure_months"))
        except (ValueError, TypeError):
            pass
    if request.get("is_ped") is not None:
        scenario["is_ped"] = bool(request.get("is_ped"))
    if condition:
        scenario["condition"] = condition
        if "pre-existing" in condition.lower() or "ped" in condition.lower():
            scenario["is_ped"] = True

    # 1. Validate explicit numeric inputs
    if treatment_cost_input is not None:
        try:
            if float(treatment_cost_input) < 0:
                return {
                    "status": "INVALID_INPUT",
                    "error": "Negative treatment cost is invalid.",
                    "message": f"Negative treatment cost: {treatment_cost_input}",
                    "total_expense": 0.0,
                    "insurer_payable": 0.0,
                    "customer_payable": 0.0,
                    "calculation_trace": []
                }
        except (ValueError, TypeError):
            return {
                "status": "INVALID_INPUT",
                "error": "Invalid treatment cost format.",
                "message": f"Treatment cost must be numeric: {treatment_cost_input}",
                "total_expense": 0.0,
                "insurer_payable": 0.0,
                "customer_payable": 0.0,
                "calculation_trace": []
            }

    try:
        qty_num = float(quantity)
        if qty_num <= 0:
            return {
                "status": "INVALID_INPUT",
                "error": "Quantity must be greater than zero.",
                "message": f"Quantity must be positive: {quantity}",
                "total_expense": 0.0,
                "insurer_payable": 0.0,
                "customer_payable": 0.0,
                "calculation_trace": []
            }
    except (ValueError, TypeError):
        return {
            "status": "INVALID_INPUT",
            "error": "Invalid quantity format.",
            "message": f"Quantity must be numeric: {quantity}",
            "total_expense": 0.0,
            "insurer_payable": 0.0,
            "customer_payable": 0.0,
            "calculation_trace": []
        }

    # 2. Lookup Procedure & City Benchmark Data
    treatment_data = None
    if procedure_name:
        treatment_data = TreatmentService.get_treatment_cost(procedure_name, city)

    # 3. Resolve Treatment Cost & Cost Boundaries
    explicit_user_cost = (treatment_cost_input is not None and str(treatment_cost_input).strip() != "")
    if request.get("cost_mode") == "reference" or (not explicit_user_cost and treatment_data):
        cost_source = "REFERENCE_DATASET"
        cost_source_label = "Reference treatment cost (from SPASTH treatment dataset)"
        cost_min = float(treatment_data.get("cost_min", 0.0))
        cost_max = float(treatment_data.get("cost_max", 0.0))
        cost_mid = float(treatment_data.get("reference_cost", 0.0))
        treatment_cost = cost_mid
        is_range = (cost_min != cost_max)
    elif explicit_user_cost:
        cost_source = "USER_PROVIDED"
        cost_source_label = "User-provided actual treatment cost"
        treatment_cost = float(treatment_cost_input)
        cost_min = treatment_cost
        cost_max = treatment_cost
        cost_mid = treatment_cost
        is_range = False
    elif procedure_name:
        return {
            "status": "TREATMENT_COST_NOT_AVAILABLE",
            "error": "TREATMENT_COST_NOT_AVAILABLE",
            "message": f"Unable to estimate: No baseline healthcare benchmark available for '{procedure_name}' in '{city}'.",
            "treatment": {
                "procedure_name": procedure_name,
                "city": city
            },
            "total_expense": 0.0,
            "insurer_payable": 0.0,
            "customer_payable": 0.0,
            "calculation_trace": []
        }
    else:
        return {
            "status": "INVALID_INPUT",
            "error": "Treatment cost is required.",
            "message": "Treatment cost is required.",
            "total_expense": 0.0,
            "insurer_payable": 0.0,
            "customer_payable": 0.0,
            "calculation_trace": []
        }

    # 3. Resolve Policy Parameters (Source of Trust: Backend policy data overrides frontend parameters)
    copay_pct = request.get("copay_percent", 0.0)
    sublimit = request.get("treatment_sublimit")
    sum_insured = request.get("sum_insured")
    room_penalty = request.get("room_penalty_ratio", 0.0)
    citations = []
    confidence = "HIGH"
    confidence_reason = "Authoritative backend policy and benchmark resolution"
    source_name = treatment_data.get("source", "State Healthcare Package Benchmark 2025") if treatment_data else "Hospital Package Benchmark"
    data_type_val = treatment_data.get("data_type", "synthetic") if treatment_data else "reference"

    if policy_id:
        policy = PolicyService.get_policy(policy_id)
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Policy with ID '{policy_id}' not found."
            )

        policy_rules = policy.get("rules", [])
        if procedure_name:
            matched = TreatmentRuleMatcher.match_rules(
                procedure=procedure_name,
                city=city,
                city_tier=treatment_data.get("city_tier") if treatment_data else "Tier-1",
                room_category=room_category,
                validated_rules=policy_rules
            )

            # Check coverage (exclusions & waiting periods)
            coverage_check = CoverageChecker.check_coverage(
                procedure=procedure_name,
                matched_rules=matched,
                scenario=scenario
            )

            if not coverage_check.is_eligible_for_calculation:
                try:
                    qty_num = int(quantity) if int(quantity) > 0 else 1
                except Exception:
                    qty_num = 1
                total_billed = cost_mid * qty_num
                total_billed_min = cost_min * qty_num
                total_billed_max = cost_max * qty_num
                return {
                    "status": coverage_check.status,  # "EXCLUDED", "WAITING_PERIOD", "INSUFFICIENT_INFORMATION"
                    "currency": "INR",
                    "is_range": is_range,
                    "treatment": {
                        "treatment_id": treatment_data.get("treatment_id") if treatment_data else None,
                        "procedure_name": procedure_name,
                        "city": city
                    },
                    "total_expense": total_billed,
                    "treatment_cost_range": {"min": total_billed_min, "max": total_billed_max},
                    "treatment_cost": {"min": total_billed_min, "max": total_billed_max} if is_range else total_billed,
                    "non_covered_expense": 0.0,
                    "eligible_expense": 0.0,
                    "eligible_amount": 0.0,
                    "eligible_amount_range": {"min": 0.0, "max": 0.0},
                    "sublimit": None,
                    "sublimit_adjustment": 0.0,
                    "room_penalty_ratio": 0.0,
                    "room_adjustment": 0.0,
                    "deductible": 0.0,
                    "co_payment_percentage": 0.0,
                    "co_payment_amount": 0.0,
                    "sum_insured": matched.sum_insured,
                    "remaining_sum_insured": matched.sum_insured,
                    "remaining_sum_insured_range": {"min": matched.sum_insured, "max": matched.sum_insured},
                    "insurer_payable": 0.0,
                    "customer_payable": total_billed,
                    "estimated_coverage_range": {"min": 0.0, "max": 0.0},
                    "estimated_oop_range": {"min": total_billed_min, "max": total_billed_max},
                    "insurance_contribution": {"min": 0.0, "max": 0.0},
                    "patient_payable": {"min": total_billed_min, "max": total_billed_max},
                    "customer_payable_breakdown": {
                        "non_covered_expense": 0.0,
                        "sublimit_excess": 0.0,
                        "room_upgrade_excess": 0.0,
                        "deductible": 0.0,
                        "co_payment": 0.0,
                        "sum_insured_excess": 0.0,
                        "ineligible_claim": total_billed
                    },
                    "calculation_trace": [{
                        "step": 1,
                        "rule": coverage_check.status,
                        "input": total_billed,
                        "deduction": total_billed,
                        "output": 0.0,
                        "description": coverage_check.reason,
                        "reason": f"Claim denied per policy {coverage_check.status.replace('_', ' ').title()}"
                    }],
                    "citations": matched.matched_citations,
                    "evidence": matched.matched_citations,
                    "coverage_checks": coverage_check.to_dict(),
                    "confidence": "HIGH" if coverage_check.page is not None else "MEDIUM",
                    "confidence_reason": coverage_check.reason,
                    "data_source": source_name,
                    "data_type": data_type_val,
                    "treatment_cost_source": cost_source,
                    "treatment_cost_source_label": cost_source_label,
                    "calculation": {
                        "is_range": is_range,
                        "cost_range": {"min": total_billed_min, "max": total_billed_max},
                        "coverage_range": {"min": 0.0, "max": 0.0},
                        "oop_range": {"min": total_billed_min, "max": total_billed_max},
                        "eligible_amount": 0.0,
                        "sublimit_excess": 0.0,
                        "deductible": 0.0,
                        "copay_percent": 0.0,
                        "copay_amount": 0.0,
                        "insurer_payable": 0.0,
                        "customer_payable": total_billed,
                        "remaining_sum_insured": matched.sum_insured
                    },
                    "trace": [{
                        "step": 1,
                        "rule": coverage_check.status,
                        "input": total_billed,
                        "deduction": total_billed,
                        "output": 0.0,
                        "description": coverage_check.reason,
                        "reason": f"Claim denied per policy {coverage_check.status.replace('_', ' ').title()}"
                    }]
                }

            # Grounded policy parameters override frontend values
            if matched.sum_insured is not None:
                sum_insured = matched.sum_insured
            copay_pct = matched.copay_percent
            sublimit = matched.procedure_sublimit
            if matched.deductible_rule is not None:
                deductible = matched.deductible

            if room_category.strip().lower() != "standard":
                room_penalty = matched.room_proportionate_deduction_rate or 0.0
            else:
                room_penalty = 0.0

            citations = matched.matched_citations

    # 4. Pure Deterministic Python Math Engine Calculation
    # Calculate for midpoint
    res_mid = MathEngine.calculate_claim(
        treatment_cost=cost_mid if 'cost_mid' in locals() else treatment_cost,
        quantity=quantity,
        non_covered_expense=non_covered_expense,
        copay_percent=copay_pct,
        deductible=deductible,
        treatment_sublimit=sublimit,
        sum_insured=sum_insured,
        remaining_sum_insured=request.get("remaining_sum_insured"),
        room_penalty_ratio=room_penalty,
        treatment_id=treatment_data.get("treatment_id") if treatment_data else request.get("treatment_id"),
        procedure_name=procedure_name,
        city=city
    )

    # Calculate for bounds if range
    if 'is_range' in locals() and is_range:
        res_min = MathEngine.calculate_claim(
            treatment_cost=cost_min,
            quantity=quantity,
            non_covered_expense=non_covered_expense,
            copay_percent=copay_pct,
            deductible=deductible,
            treatment_sublimit=sublimit,
            sum_insured=sum_insured,
            remaining_sum_insured=request.get("remaining_sum_insured"),
            room_penalty_ratio=room_penalty,
            treatment_id=treatment_data.get("treatment_id") if treatment_data else request.get("treatment_id"),
            procedure_name=procedure_name,
            city=city
        )
        res_max = MathEngine.calculate_claim(
            treatment_cost=cost_max,
            quantity=quantity,
            non_covered_expense=non_covered_expense,
            copay_percent=copay_pct,
            deductible=deductible,
            treatment_sublimit=sublimit,
            sum_insured=sum_insured,
            remaining_sum_insured=request.get("remaining_sum_insured"),
            room_penalty_ratio=room_penalty,
            treatment_id=treatment_data.get("treatment_id") if treatment_data else request.get("treatment_id"),
            procedure_name=procedure_name,
            city=city
        )
    else:
        is_range = False
        res_min = res_mid
        res_max = res_mid

    res = dict(res_mid)
    res["is_range"] = is_range
    res["cost_min"] = res_min.get("total_expense", 0.0)
    res["cost_max"] = res_max.get("total_expense", 0.0)
    res["treatment_cost_range"] = {
        "min": res_min.get("total_expense", 0.0),
        "max": res_max.get("total_expense", 0.0)
    }
    res["treatment_cost"] = res["treatment_cost_range"] if is_range else res_mid.get("total_expense", 0.0)
    res["estimated_coverage_range"] = {
        "min": res_min.get("insurer_payable", 0.0),
        "max": res_max.get("insurer_payable", 0.0)
    }
    res["insurance_contribution"] = res["estimated_coverage_range"]
    res["estimated_oop_range"] = {
        "min": res_min.get("customer_payable", 0.0),
        "max": res_max.get("customer_payable", 0.0)
    }
    res["patient_payable"] = res["estimated_oop_range"]
    res["eligible_amount_range"] = {
        "min": res_min.get("eligible_expense", 0.0),
        "max": res_max.get("eligible_expense", 0.0)
    }
    res["remaining_sum_insured_range"] = {
        "min": res_max.get("new_remaining_sum_insured"),
        "max": res_min.get("new_remaining_sum_insured")
    }

    # 5. Determine Cost Source Classification
    if 'cost_source' not in locals():
        use_actual = request.get("cost_mode") == "actual" or request.get("use_actual_cost", False)
        if use_actual and treatment_cost_input is not None:
            cost_source = "USER_PROVIDED"
            cost_source_label = "User-provided actual treatment cost"
        else:
            cost_source = "REFERENCE_DATASET"
            cost_source_label = "Reference treatment cost (from SPASTH treatment dataset)"

    if citations:
        res["citations"] = citations
        res["evidence"] = citations
    res["room_category"] = room_category
    res["procedure"] = procedure_name
    res["city"] = city
    res["confidence"] = confidence
    res["confidence_reason"] = confidence_reason
    res["data_source"] = source_name
    res["data_type"] = data_type_val
    res["policy_id"] = policy_id
    res["treatment_cost_source"] = cost_source
    res["treatment_cost_source_label"] = cost_source_label

    # Section 9 auditable calculation trace contract
    res["calculation"] = {
        "is_range": is_range,
        "cost_range": res["treatment_cost_range"],
        "coverage_range": res["estimated_coverage_range"],
        "oop_range": res["estimated_oop_range"],
        "eligible_amount": res.get("eligible_amount", res.get("eligible_expense", 0.0)),
        "sublimit_excess": res.get("customer_payable_breakdown", {}).get("sublimit_excess", 0.0),
        "deductible": res.get("customer_payable_breakdown", {}).get("deductible", 0.0),
        "copay_percent": res.get("co_payment_percentage", 0.0),
        "copay_amount": res.get("customer_payable_breakdown", {}).get("co_payment", 0.0),
        "insurer_payable": res.get("insurer_payable", 0.0),
        "customer_payable": res.get("customer_payable", 0.0),
        "remaining_sum_insured": res.get("remaining_sum_insured")
    }
    res["trace"] = res.get("calculation_trace", [])

    return res
