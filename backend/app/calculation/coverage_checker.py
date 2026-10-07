import logging
import re
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from .rule_matcher import MatchedRules

logger = logging.getLogger(__name__)

@dataclass
class CoverageCheckResult:
    status: str  # "COVERED", "EXCLUDED", "WAITING_PERIOD", "INSUFFICIENT_INFORMATION"
    is_eligible_for_calculation: bool
    reason: str
    evidence_rule: Optional[Dict[str, Any]] = None
    page: Optional[int] = None
    clause: Optional[str] = None
    source_text: Optional[str] = None
    waiting_period_info: Optional[Dict[str, Any]] = None
    
    # Step 7: Structured check statuses
    coverage_status: str = "covered"
    waiting_period_status: str = "satisfied"
    exclusion_status: str = "not_found"
    sublimit_status: str = "not_applicable"
    copay_status: str = "not_applicable"
    room_rule_status: str = "not_applicable"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "coverage_status": self.coverage_status,
            "waiting_period_status": self.waiting_period_status,
            "exclusion_status": self.exclusion_status,
            "sublimit_status": self.sublimit_status,
            "copay_status": self.copay_status,
            "room_rule_status": self.room_rule_status,
            "is_eligible_for_calculation": self.is_eligible_for_calculation,
            "reason": self.reason
        }


class CoverageChecker:
    """
    Step 7: Performs coverage determination prior to mathematical estimation.
    Checks explicit policy exclusions, waiting period conditions (general, disease-specific, PED),
    and validates whether sufficient grounded policy information exists to compute a reliable estimate.
    """

    @classmethod
    def check_coverage(
        cls,
        procedure: str,
        matched_rules: MatchedRules,
        scenario: Optional[Dict[str, Any]] = None
    ) -> CoverageCheckResult:
        scenario = scenario or {}

        sublimit_status = "applicable" if (matched_rules.procedure_sublimit and matched_rules.procedure_sublimit > 0) else "not_applicable"
        copay_status = "applicable" if (matched_rules.copay_percent and matched_rules.copay_percent > 0) else "not_applicable"
        room_rule_status = "applicable" if matched_rules.room_rent_cap_daily else "not_applicable"
        if matched_rules.room_category.lower() != "standard" and matched_rules.room_rent_cap_daily and matched_rules.room_proportionate_deduction_rate is None:
            room_rule_status = "uncertain"

        # ---------------------------------------------------------
        # Step 7 Check 2: Exclusion Check
        # ---------------------------------------------------------
        if matched_rules.exclusion_rules:
            excl_rule = matched_rules.exclusion_rules[0]
            page = excl_rule.get("page")
            clause = excl_rule.get("clause") or "N/A"
            source_text = excl_rule.get("source_text") or "Clause states treatment is not covered."
            reason = f"Treatment '{procedure}' is explicitly excluded by policy terms under Clause {clause} (Page {page})."

            logger.info(f"[COVERAGE-CHECK] EXCLUDED: {reason}")
            return CoverageCheckResult(
                status="EXCLUDED",
                coverage_status="excluded",
                waiting_period_status="not_applicable",
                exclusion_status="found",
                sublimit_status=sublimit_status,
                copay_status=copay_status,
                room_rule_status=room_rule_status,
                is_eligible_for_calculation=False,
                reason=reason,
                evidence_rule=excl_rule,
                page=page,
                clause=clause,
                source_text=source_text
            )

        # ---------------------------------------------------------
        # Step 7 Check 3 & 4: Waiting Period Check
        # ---------------------------------------------------------
        policy_tenure_months = scenario.get("policy_tenure_months")
        is_ped = scenario.get("is_ped") or (str(scenario.get("condition", "")).lower() == "pre-existing condition")

        for wp_rule in matched_rules.waiting_period_rules:
            source_text = str(wp_rule.get("source_text") or "").lower()
            rule_key = str(wp_rule.get("rule_key") or "").lower()
            val_str = str(wp_rule.get("value") or "").lower()
            page = wp_rule.get("page")
            clause = wp_rule.get("clause") or "N/A"

            months_required = cls._parse_months_from_rule(source_text, val_str)

            # Pre-Existing Disease (PED)
            if is_ped and ("ped" in source_text or "pre-existing" in source_text or "pre existing" in source_text):
                if policy_tenure_months is not None and months_required is not None:
                    if policy_tenure_months < months_required:
                        reason = (
                            f"Pre-existing condition waiting period not elapsed. Policy active for {policy_tenure_months} months, "
                            f"but policy Clause {clause} (Page {page}) requires {months_required} months continuous coverage."
                        )
                        return CoverageCheckResult(
                            status="WAITING_PERIOD",
                            coverage_status="waiting_period",
                            waiting_period_status="not_satisfied",
                            exclusion_status="not_found",
                            sublimit_status=sublimit_status,
                            copay_status=copay_status,
                            room_rule_status=room_rule_status,
                            is_eligible_for_calculation=False,
                            reason=reason,
                            evidence_rule=wp_rule,
                            page=page,
                            clause=clause,
                            source_text=wp_rule.get("source_text"),
                            waiting_period_info={
                                "type": "PED",
                                "required_months": months_required,
                                "elapsed_months": policy_tenure_months
                            }
                        )

            # Disease-Specific Waiting Period
            proc_lower = procedure.lower()
            if proc_lower in source_text or proc_lower in rule_key:
                if policy_tenure_months is not None and months_required is not None:
                    if policy_tenure_months < months_required:
                        reason = (
                            f"Disease-specific waiting period for {procedure} not elapsed. Policy active for {policy_tenure_months} months, "
                            f"but Clause {clause} (Page {page}) mandates {months_required} months."
                        )
                        return CoverageCheckResult(
                            status="WAITING_PERIOD",
                            coverage_status="waiting_period",
                            waiting_period_status="not_satisfied",
                            exclusion_status="not_found",
                            sublimit_status=sublimit_status,
                            copay_status=copay_status,
                            room_rule_status=room_rule_status,
                            is_eligible_for_calculation=False,
                            reason=reason,
                            evidence_rule=wp_rule,
                            page=page,
                            clause=clause,
                            source_text=wp_rule.get("source_text"),
                            waiting_period_info={
                                "type": "Disease-Specific",
                                "required_months": months_required,
                                "elapsed_months": policy_tenure_months
                            }
                        )

        # ---------------------------------------------------------
        # Check: Insufficient Information
        # ---------------------------------------------------------
        if not matched_rules.matched_citations and matched_rules.sum_insured is None:
            return CoverageCheckResult(
                status="INSUFFICIENT_INFORMATION",
                coverage_status="insufficient_information",
                waiting_period_status="unknown",
                exclusion_status="unknown",
                sublimit_status=sublimit_status,
                copay_status=copay_status,
                room_rule_status=room_rule_status,
                is_eligible_for_calculation=False,
                reason="Policy does not contain verifiable schedule or coverage parameters for this scenario."
            )

        # Satisfied & Covered
        return CoverageCheckResult(
            status="COVERED",
            coverage_status="covered",
            waiting_period_status="satisfied" if matched_rules.waiting_period_rules else "not_applicable",
            exclusion_status="not_found",
            sublimit_status=sublimit_status,
            copay_status=copay_status,
            room_rule_status=room_rule_status,
            is_eligible_for_calculation=True,
            reason="Treatment appears covered under active policy rules."
        )

    @staticmethod
    def _parse_months_from_rule(source_text: str, val_str: str) -> Optional[int]:
        combined = f"{source_text} {val_str}"
        m_match = re.search(r'(\d+)\s*(?:month|months)', combined)
        if m_match:
            try:
                return int(m_match.group(1))
            except ValueError:
                pass

        y_match = re.search(r'(\d+)\s*(?:year|years)', combined)
        if y_match:
            try:
                return int(y_match.group(1)) * 12
            except ValueError:
                pass

        return None
