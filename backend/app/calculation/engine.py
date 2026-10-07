import logging
from typing import List, Dict, Any, Optional

from app.validation.policy_validator import PolicyValidator, ValidationError
from app.calculation.rule_matcher import TreatmentRuleMatcher, MatchedRules
from app.calculation.coverage_checker import CoverageChecker, CoverageCheckResult
from app.services.math_engine import MathEngine

logger = logging.getLogger(__name__)

class FinancialCalculationEngine:
    """
    Deterministic Financial Rule Engine for Health Insurance Claims Calculation.
    Decouples financial math from LLM text generation to guarantee 100% reproducible,
    auditable financial out-of-pocket estimations.
    
    Phases 1, 3, 4, 5, 6, 7, 8, 9, 10, 14 compliant:
    - Never uses raw LLM output; verifies policy evidence.
    - Deterministic Python math: sub-limits, co-payments, sum insured.
    - Evaluates coverage, exclusions, waiting periods, room rules.
    - No hardcoded universal room penalty: requires explicit policy definition or flags uncertainty.
    """

    @staticmethod
    def calculate_out_of_pocket(
        base_min_cost: float,
        base_max_cost: float,
        procedure_name: str,
        city: str,
        room_category: str = "Standard",
        policy_rules: Optional[List[Dict[str, Any]]] = None,
        data_source: str = "State Healthcare Package Benchmark 2025",
        data_type: str = "synthetic",
        cost_found: bool = True,
        city_tier: Optional[str] = None,
        scenario: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes complete deterministic calculation pipeline:
        1. Input Validation & Safety checks
        2. Policy JSON Validation Layer
        3. Benchmark Lookup Verification
        4. Rule Matching
        5. Coverage, Exclusion, Waiting-Period Checks
        6. Mathematical Computation (sub-limit, room, co-pay, insurance, patient payable)
        7. Evidence Preservation & Confidence Scoring
        """
        policy_rules = policy_rules or []
        scenario = scenario or {}

        # -------------------------------------------------------------
        # Phase 14: Input Validation / Safety Checks
        # -------------------------------------------------------------
        try:
            PolicyValidator.validate_calculation_inputs(
                treatment_min=base_min_cost,
                treatment_max=base_max_cost,
                room_category=room_category
            )
        except ValidationError as ve:
            logger.error(f"[FIN-ENGINE] Input validation failed: {str(ve)}")
            return {
                "status": "UNABLE_TO_ESTIMATE",
                "message": f"Input validation error: {str(ve)}",
                "error": str(ve),
                "procedure": procedure_name,
                "city": city,
                "room_category": room_category,
                "treatment_cost_range": {"min": 0.0, "max": 0.0},
                "treatment_cost": {"min": 0.0, "max": 0.0},
                "applicable_sublimit": None,
                "eligible_amount_range": {"min": 0.0, "max": 0.0},
                "eligible_amount": {"min": 0.0, "max": 0.0},
                "copay_percent": 0.0,
                "copay_amount": {"min": 0.0, "max": 0.0},
                "estimated_coverage_range": {"min": 0.0, "max": 0.0},
                "insurance_contribution": {"min": 0.0, "max": 0.0},
                "estimated_oop_range": {"min": 0.0, "max": 0.0},
                "patient_payable": {"min": 0.0, "max": 0.0},
                "confidence": "LOW",
                "confidence_reason": str(ve),
                "applied_rules": [],
                "rules_applied": [],
                "citations": [],
                "evidence": [],
                "data_source": data_source,
                "data_type": data_type
            }

        # -------------------------------------------------------------
        # Phase 2 / Uncertainty: Missing Cost Benchmark
        # -------------------------------------------------------------
        if not cost_found or base_min_cost <= 0:
            logger.warning(f"[FIN-ENGINE] Missing benchmark for '{procedure_name}' in '{city}'.")
            return {
                "status": "UNABLE_TO_ESTIMATE",
                "message": f"Unable to confidently estimate costs: No baseline healthcare pricing benchmark available for '{procedure_name}' in '{city}'.",
                "procedure": procedure_name,
                "city": city,
                "room_category": room_category,
                "treatment_cost_range": {"min": 0.0, "max": 0.0},
                "treatment_cost": {"min": 0.0, "max": 0.0},
                "applicable_sublimit": None,
                "eligible_amount_range": {"min": 0.0, "max": 0.0},
                "eligible_amount": {"min": 0.0, "max": 0.0},
                "copay_percent": 0.0,
                "copay_amount": {"min": 0.0, "max": 0.0},
                "estimated_coverage_range": {"min": 0.0, "max": 0.0},
                "insurance_contribution": {"min": 0.0, "max": 0.0},
                "estimated_oop_range": {"min": 0.0, "max": 0.0},
                "patient_payable": {"min": 0.0, "max": 0.0},
                "confidence": "LOW",
                "confidence_reason": f"No baseline healthcare pricing benchmark available for '{procedure_name}' in '{city}'.",
                "missing_information": [f"Hospital cost data for {procedure_name} in {city}"],
                "applied_rules": [],
                "rules_applied": [],
                "citations": [],
                "evidence": [],
                "data_source": data_source,
                "data_type": data_type
            }

        # -------------------------------------------------------------
        # Phase 1: Policy JSON Validation Layer
        # -------------------------------------------------------------
        validation_result = PolicyValidator.validate_policy_rules(policy_rules)
        if not validation_result.is_valid:
            logger.warning("[FIN-ENGINE] Policy rules validation failed or returned no usable rules.")
            return {
                "status": "UNABLE_TO_ESTIMATE",
                "message": "Unable to confidently estimate: Policy lacks validated grounded financial rules.",
                "procedure": procedure_name,
                "city": city,
                "room_category": room_category,
                "treatment_cost_range": {"min": 0.0, "max": 0.0},
                "treatment_cost": {"min": 0.0, "max": 0.0},
                "applicable_sublimit": None,
                "eligible_amount_range": {"min": 0.0, "max": 0.0},
                "eligible_amount": {"min": 0.0, "max": 0.0},
                "copay_percent": 0.0,
                "copay_amount": {"min": 0.0, "max": 0.0},
                "estimated_coverage_range": {"min": 0.0, "max": 0.0},
                "insurance_contribution": {"min": 0.0, "max": 0.0},
                "estimated_oop_range": {"min": 0.0, "max": 0.0},
                "patient_payable": {"min": 0.0, "max": 0.0},
                "confidence": "LOW",
                "confidence_reason": "Policy document has no validated coverage schedule or clauses.",
                "missing_information": validation_result.errors or ["Valid policy rules with page and text evidence"],
                "applied_rules": [],
                "rules_applied": [],
                "citations": [],
                "evidence": [],
                "data_source": data_source,
                "data_type": data_type
            }

        # -------------------------------------------------------------
        # Phase 3: Rule Matching Service
        # -------------------------------------------------------------
        matched = TreatmentRuleMatcher.match_rules(
            procedure=procedure_name,
            city=city,
            city_tier=city_tier,
            room_category=room_category,
            validated_rules=validation_result.validated_rules
        )

        # -------------------------------------------------------------
        # Phase 4, 5, 6: Coverage, Exclusion, Waiting-Period Checks
        # -------------------------------------------------------------
        coverage_check = CoverageChecker.check_coverage(
            procedure=procedure_name,
            matched_rules=matched,
            scenario=scenario
        )

        if not coverage_check.is_eligible_for_calculation:
            # Excluded, Waiting-Period active, or Insufficient information
            logger.info(f"[FIN-ENGINE] Coverage Check halted calculation: {coverage_check.status} - {coverage_check.reason}")
            citations = []
            if coverage_check.evidence_rule:
                citations.append({
                    "rule": f"{coverage_check.status.replace('_', ' ').title()} Clause",
                    "details": coverage_check.reason,
                    "page": coverage_check.page or "N/A",
                    "clause": coverage_check.clause or "N/A",
                    "source_text": coverage_check.source_text or ""
                })

            return {
                "status": coverage_check.status,  # "EXCLUDED", "WAITING_PERIOD", "INSUFFICIENT_INFORMATION"
                "message": coverage_check.reason,
                "procedure": procedure_name,
                "city": city,
                "room_category": room_category,
                "treatment_cost_range": {"min": round(base_min_cost, 2), "max": round(base_max_cost, 2)},
                "treatment_cost": {"min": round(base_min_cost, 2), "max": round(base_max_cost, 2)},
                "applicable_sublimit": None,
                "eligible_amount_range": {"min": 0.0, "max": 0.0},
                "eligible_amount": {"min": 0.0, "max": 0.0},
                "copay_percent": 0.0,
                "copay_amount": {"min": 0.0, "max": 0.0},
                "estimated_coverage_range": {"min": 0.0, "max": 0.0},
                "insurance_contribution": {"min": 0.0, "max": 0.0},
                # For excluded / waiting period, patient liability is full treatment cost
                "estimated_oop_range": {"min": round(base_min_cost, 2), "max": round(base_max_cost, 2)},
                "patient_payable": {"min": round(base_min_cost, 2), "max": round(base_max_cost, 2)},
                "confidence": "HIGH" if coverage_check.page is not None else "MEDIUM",
                "confidence_reason": coverage_check.reason,
                "applied_rules": [{
                    "rule_name": f"Policy {coverage_check.status.replace('_', ' ').title()}",
                    "description": coverage_check.reason,
                    "impact": "100% Patient Payable (Zero Insurance Coverage)"
                }],
                "rules_applied": [{
                    "rule_name": f"Policy {coverage_check.status.replace('_', ' ').title()}",
                    "description": coverage_check.reason,
                    "impact": "100% Patient Payable (Zero Insurance Coverage)"
                }],
                "citations": citations,
                "evidence": citations,
                "coverage_checks": coverage_check.to_dict(),
                "data_source": data_source,
                "data_type": data_type
            }

        # -------------------------------------------------------------
        # Phase 7 & 8: Deterministic Math Engine
        # -------------------------------------------------------------
        cost_min = float(base_min_cost)
        cost_max = float(base_max_cost)

        applied_rules = []
        citations = list(matched.matched_citations)

        # 1. Base eligible amount initialized to treatment cost range
        eligible_min = cost_min
        eligible_max = cost_max

        # 2. Procedure Sub-Limit Cap
        sub_limit_val = matched.procedure_sublimit
        if sub_limit_val and sub_limit_val > 0:
            eligible_min = min(eligible_min, sub_limit_val)
            eligible_max = min(eligible_max, sub_limit_val)
            applied_rules.append({
                "rule_name": "Procedure Sub-Limit Applied",
                "description": f"{procedure_name} claim amount capped at sub-limit of INR {sub_limit_val:,.2f}.",
                "impact": f"Eligible claim restricted from INR {cost_max:,.2f} to INR {eligible_max:,.2f}"
            })

        # 3. Room Rules (Phase 8 & 10) - No arbitrary hardcoded 30% penalty
        room_category_clean = room_category.strip().lower()
        room_rule_ambiguity = False
        room_penalty_ratio = 0.0

        if room_category_clean != "standard":
            # Upgraded room category (e.g., Deluxe)
            if matched.room_proportionate_deduction_rate is not None:
                # Policy explicitly defined a proportionate deduction rate
                room_penalty_ratio = matched.room_proportionate_deduction_rate
                applied_rules.append({
                    "rule_name": "Policy Proportionate Room Rent Deduction",
                    "description": (
                        f"Room upgraded to '{room_category}'. Policy clause prescribes "
                        f"{room_penalty_ratio * 100:.0f}% proportionate deduction across hospital charges."
                    ),
                    "impact": f"Eligible coverage reduced by {room_penalty_ratio * 100:.0f}%"
                })
            elif matched.room_rent_cap_daily:
                # Policy defines a daily cap but does NOT prescribe an exact proportionate deduction formula
                # Do NOT invent or hardcode 30%! Flag uncertainty.
                room_rule_ambiguity = True
                applied_rules.append({
                    "rule_name": "Room Category Alert",
                    "description": (
                        f"Selected '{room_category}' room may exceed daily allowance (INR {matched.room_rent_cap_daily:,.2f}/day). "
                        "Policy does not define a fixed proportionate deduction percentage formula; no arbitrary deduction applied."
                    ),
                    "impact": "Room penalty undetermined by contract text"
                })
        else:
            # Standard room fits within allowed schedule
            if matched.room_rent_cap_daily:
                applied_rules.append({
                    "rule_name": "Standard Room Rent Category Approved",
                    "description": f"Standard Room selected, within policy limit of INR {matched.room_rent_cap_daily:,.2f} / day.",
                    "impact": "No proportionate room deduction"
                })

        # 4. Deterministic Financial Math Engine (Step 8, 9, 10)
        math_result = MathEngine.calculate(
            cost_min=cost_min,
            cost_max=cost_max,
            copay_percent=matched.copay_percent,
            treatment_sublimit=matched.procedure_sublimit,
            sum_insured=matched.sum_insured,
            room_penalty_ratio=room_penalty_ratio
        )

        if matched.copay_percent > 0:
            applied_rules.append({
                "rule_name": f"{matched.copay_percent:.0f}% Mandatory Co-Payment",
                "description": f"Policyholder pays mandatory {matched.copay_percent:.0f}% co-payment on all eligible claims.",
                "impact": f"Deducted {matched.copay_percent:.0f}% from eligible amount"
            })

        # -------------------------------------------------------------
        # Phase 10: Confidence & Transparency Evaluation
        # -------------------------------------------------------------
        if not validation_result.has_sum_insured or not citations:
            confidence = "LOW"
            confidence_reason = "Missing primary Sum Insured or key schedule clauses in policy evidence."
        elif room_rule_ambiguity:
            confidence = "MEDIUM"
            confidence_reason = (
                f"Room upgrade to '{room_category}' has daily cap in policy, but contract text does not specify "
                "an exact proportionate deduction percentage."
            )
        else:
            confidence = "HIGH"
            confidence_reason = "All required policy rules verified with grounded page citations and active cost benchmark."

        # -------------------------------------------------------------
        # Phase 9: Structured Calculation Breakdown
        # -------------------------------------------------------------
        result = {
            "status": "calculated",
            "procedure": procedure_name,
            "city": city,
            "room_category": room_category,
            "treatment_cost": math_result["treatment_cost"],
            "treatment_cost_range": math_result["treatment_cost"],
            "applicable_sublimit": math_result["applicable_sublimit"],
            "sub_limit": math_result["applicable_sublimit"],
            "eligible_amount": math_result["eligible_amount"],
            "eligible_amount_range": math_result["eligible_amount"],
            "copay_percent": math_result["copay_percent"],
            "copay_amount": math_result["copay_amount"],
            "insurance_contribution": math_result["insurance_contribution"],
            "estimated_coverage_range": math_result["insurance_contribution"],
            "patient_payable": math_result["patient_payable"],
            "estimated_oop_range": math_result["patient_payable"],
            "room_rent_cap": matched.room_rent_cap_daily,
            "room_proportionate_deduction_rate": matched.room_proportionate_deduction_rate,
            "coverage_checks": coverage_check.to_dict(),
            "applied_rules": applied_rules,
            "rules_applied": applied_rules,
            "citations": citations,
            "evidence": citations,
            "confidence": confidence,
            "confidence_reason": confidence_reason,
            "data_source": data_source,
            "data_type": data_type
        }

        logger.info(
            f"[FIN-ENGINE] Computed: Cost ₹{cost_min:,.0f}-₹{cost_max:,.0f} | "
            f"Coverage ₹{math_result['insurance_contribution']['min']:,.0f}-₹{math_result['insurance_contribution']['max']:,.0f} | "
            f"OOP ₹{math_result['patient_payable']['min']:,.0f}-₹{math_result['patient_payable']['max']:,.0f}"
        )

        return result
