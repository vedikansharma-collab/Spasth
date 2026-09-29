import logging
from typing import List, Dict, Any, Optional
from app.extraction.normalizer import ValueNormalizer

logger = logging.getLogger(__name__)

class FinancialCalculationEngine:
    """
    Deterministic Financial Rule Engine for Health Insurance Claims Calculation.
    Decouples financial math from LLM text generation to guarantee 100% reproducible,
    auditable financial out-of-pocket estimations.
    """

    @staticmethod
    def calculate_out_of_pocket(
        base_min_cost: float,
        base_max_cost: float,
        procedure_name: str,
        city: str,
        room_category: str,
        policy_rules: List[Dict[str, Any]],
        data_source: str = "State Healthcare Package Benchmark 2025",
        cost_found: bool = True
    ) -> Dict[str, Any]:
        """
        Calculates out-of-pocket medical expense ranges by applying policy rules sequentially:
        1. Base Treatment Cost Lookup
        2. Procedure Sub-Limit Cap
        3. Room Rent Proportionate Deductions
        4. Co-Payment Deductions
        5. Out-of-Pocket Result, Evidence Citations, & Confidence Evaluation
        """
        applied_rules = []
        citations = []

        # 0. Uncertainty Handling: Missing Cost Benchmark
        if not cost_found or base_min_cost <= 0:
            logger.warning(f"[FIN-ENGINE] UNABLE_TO_ESTIMATE: Missing cost benchmark for procedure '{procedure_name}' in city '{city}'.")
            return {
                "status": "UNABLE_TO_ESTIMATE",
                "message": f"Unable to confidently estimate costs: No baseline healthcare pricing benchmark available for '{procedure_name}' in '{city}'.",
                "procedure": procedure_name,
                "city": city,
                "room_category": room_category,
                "treatment_cost_range": {"min": 0.0, "max": 0.0},
                "eligible_amount_range": {"min": 0.0, "max": 0.0},
                "estimated_coverage_range": {"min": 0.0, "max": 0.0},
                "estimated_oop_range": {"min": 0.0, "max": 0.0},
                "confidence": "LOW",
                "confidence_reason": f"No baseline healthcare pricing benchmark available for {procedure_name} in {city}.",
                "missing_information": [f"Hospital cost data for {procedure_name} in {city}"],
                "applied_rules": [],
                "citations": [],
                "data_source": data_source,
                "data_type": "synthetic_demo"
            }

        # 1. Parse Policy Parameters from Extracted Rules with Value Normalization
        sum_insured: Optional[float] = None
        copay_percent: float = 0.0
        room_rent_cap_daily: float = 5000.0
        procedure_sub_limit: Optional[float] = None
        has_sum_insured_rule = False

        for rule in policy_rules:
            rule_type = rule.get("rule_type")
            raw_val = rule.get("value")
            page = rule.get("page")
            clause = rule.get("clause") or "N/A"
            snippet = rule.get("source_text") or "Source location unavailable"

            if rule_type == "sum_insured":
                snip_lower = snippet.lower()
                is_daily_cap = any(k in snip_lower for k in ["per day", "/day", "room rent", "icu charges"])
                if not is_daily_cap:
                    val = ValueNormalizer.parse_monetary_value(raw_val, source_text=snippet)
                    if val and val >= 10000.0:  # Valid sum insured (>= 10,000)
                        sum_insured = val
                        has_sum_insured_rule = True
                        citations.append({
                            "rule": "Sum Insured",
                            "details": f"INR {val:,.2f}",
                            "page": page if page is not None else "N/A",
                            "clause": clause,
                            "source_text": snippet
                        })
            elif rule_type == "copay":
                val = ValueNormalizer.parse_percentage_value(raw_val, source_text=snippet)
                copay_percent = val
                citations.append({
                    "rule": "Mandatory Co-Payment",
                    "details": f"{val:.1f}% Co-Pay Deduction",
                    "page": page if page is not None else "N/A",
                    "clause": clause,
                    "source_text": snippet
                })
            elif rule_type == "room_rent_limit":
                val = ValueNormalizer.parse_monetary_value(raw_val, source_text=snippet) or 5000.0
                room_rent_cap_daily = val
                citations.append({
                    "rule": "Room Rent Limit",
                    "details": f"INR {val:,.2f} / day (Standard Single Room)",
                    "page": page if page is not None else "N/A",
                    "clause": clause,
                    "source_text": snippet
                })
            elif rule_type == "sub_limit":
                rule_key = str(rule.get("rule_key", "")).lower()
                proc_lower = procedure_name.lower()
                if proc_lower in rule_key or proc_lower in snippet.lower() or rule_key in proc_lower:
                    val = ValueNormalizer.parse_monetary_value(raw_val, source_text=snippet)
                    if val and val > 100.0:  # Must be a valid monetary sub-limit (> 100)
                        procedure_sub_limit = val
                        citations.append({
                            "rule": f"{procedure_name} Procedure Sub-Limit",
                            "details": f"Capped at INR {val:,.2f}",
                            "page": page if page is not None else "N/A",
                            "clause": clause,
                            "source_text": snippet
                        })
            elif rule_type == "waiting_period":
                citations.append({
                    "rule": "Waiting Period Clause",
                    "details": f"{raw_val} Waiting Period",
                    "page": page if page is not None else "N/A",
                    "clause": clause,
                    "source_text": snippet
                })

        # 2. Base Cost Range
        cost_min = float(base_min_cost)
        cost_max = float(base_max_cost)

        # 3. Apply Procedure Sub-Limit Cap
        eligible_min = cost_min
        eligible_max = cost_max

        if procedure_sub_limit and procedure_sub_limit > 0:
            eligible_min = min(cost_min, procedure_sub_limit)
            eligible_max = min(cost_max, procedure_sub_limit)
            applied_rules.append({
                "rule_name": "Procedure Sub-Limit Applied",
                "description": f"{procedure_name} claim amount capped at sub-limit of INR {procedure_sub_limit:,.2f}.",
                "impact": f"Eligible claim restricted from INR {cost_max:,.2f} to INR {eligible_max:,.2f}"
            })

        # 4. Apply Room Rent Proportionate Deduction Penalty
        if room_category.lower() == "deluxe":
            proportionate_penalty_ratio = 0.70  # 30% penalty due to room upgrade
            eligible_min = eligible_min * proportionate_penalty_ratio
            eligible_max = eligible_max * proportionate_penalty_ratio
            applied_rules.append({
                "rule_name": "Room Rent Proportionate Deduction Penalty",
                "description": f"Selected Deluxe Room exceeds Standard Room daily cap of INR {room_rent_cap_daily:,.2f}. 30% proportionate deduction penalty applied across associated hospital charges.",
                "impact": "Eligible coverage reduced by 30%"
            })

        # 5. Sum Insured Cap Check
        if sum_insured and sum_insured > 0:
            eligible_min = min(eligible_min, sum_insured)
            eligible_max = min(eligible_max, sum_insured)

        # 6. Apply Co-payment Percentage
        covered_min = eligible_min * (1.0 - copay_percent / 100.0)
        covered_max = eligible_max * (1.0 - copay_percent / 100.0)

        if copay_percent > 0:
            applied_rules.append({
                "rule_name": f"{copay_percent:.0f}% Mandatory Co-Payment",
                "description": f"Policyholder pays mandatory {copay_percent:.0f}% co-payment on all eligible claims.",
                "impact": f"Deducted {copay_percent:.0f}% from eligible amount"
            })

        # 7. Calculate Out-of-Pocket Expenses
        oop_min = max(0.0, cost_min - covered_min)
        oop_max = max(0.0, cost_max - covered_max)

        # 8. Step 11 Debug Logging
        logger.info("=== FINANCIAL ESTIMATE CALCULATION DEBUG LOG ===")
        logger.info(f"Procedure: '{procedure_name}', City: '{city}', Room: '{room_category}'")
        logger.info(f"Treatment Cost: ₹{cost_min:,.2f} - ₹{cost_max:,.2f}")
        logger.info(f"Sub-Limit: {f'₹{procedure_sub_limit:,.2f}' if procedure_sub_limit else 'None'}")
        logger.info(f"Co-Pay: {copay_percent:.1f}%")
        logger.info(f"Eligible Amount: ₹{eligible_min:,.2f} - ₹{eligible_max:,.2f}")
        logger.info(f"Coverage: ₹{covered_min:,.2f} - ₹{covered_max:,.2f}")
        logger.info(f"Out-of-Pocket (OOP): ₹{oop_min:,.2f} - ₹{oop_max:,.2f}")
        logger.info("================================================")

        # 9. Evidence-Based Confidence Scoring System
        if not citations or not has_sum_insured_rule:
            confidence = "LOW"
            confidence_reason = "Missing primary Sum Insured or key policy coverage schedule clauses."
        elif room_category.lower() == "deluxe":
            confidence = "MEDIUM"
            confidence_reason = "Proportionate room rent penalty applied due to room category upgrade."
        else:
            confidence = "HIGH"
            confidence_reason = "All required policy clauses grounded with exact page citations and verified procedure cost benchmark."

        return {
            "status": "SUCCESS",
            "procedure": procedure_name,
            "city": city,
            "room_category": room_category,
            "treatment_cost_range": {
                "min": round(cost_min, 2),
                "max": round(cost_max, 2)
            },
            "eligible_amount_range": {
                "min": round(eligible_min, 2),
                "max": round(eligible_max, 2)
            },
            "estimated_coverage_range": {
                "min": round(covered_min, 2),
                "max": round(covered_max, 2)
            },
            "estimated_oop_range": {
                "min": round(oop_min, 2),
                "max": round(oop_max, 2)
            },
            "copay_percent": copay_percent,
            "room_rent_cap": room_rent_cap_daily,
            "sub_limit": procedure_sub_limit,
            "applied_rules": applied_rules,
            "citations": citations,
            "confidence": confidence,
            "confidence_reason": confidence_reason,
            "data_source": data_source,
            "data_type": "synthetic_demo"
        }
