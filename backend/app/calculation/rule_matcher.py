import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class MatchedRules:
    procedure: str
    city: str
    city_tier: Optional[str] = None
    room_category: str = "Standard"
    
    # Financial parameters
    sum_insured: Optional[float] = None
    sum_insured_rule: Optional[Dict[str, Any]] = None
    
    copay_percent: float = 0.0
    copay_rule: Optional[Dict[str, Any]] = None
    
    procedure_sublimit: Optional[float] = None
    sublimit_rule: Optional[Dict[str, Any]] = None
    
    room_rent_cap_daily: Optional[float] = None
    room_allowed_category: Optional[str] = None
    room_proportionate_deduction_rate: Optional[float] = None  # None if not defined in policy
    room_rule: Optional[Dict[str, Any]] = None
    
    # Waiting periods and exclusions
    waiting_period_rules: List[Dict[str, Any]] = field(default_factory=list)
    exclusion_rules: List[Dict[str, Any]] = field(default_factory=list)
    
    # Matched evidence items
    matched_citations: List[Dict[str, Any]] = field(default_factory=list)


class TreatmentRuleMatcher:
    """
    Phase 3: Matches policy rules against selected treatment, city, room category, and scenario.
    Extracts relevant sub-limits, co-payments, room policies, waiting periods, and exclusions
    with complete grounded evidence preserved.
    """

    @classmethod
    def match_rules(
        cls,
        procedure: str,
        city: str,
        city_tier: Optional[str],
        room_category: str,
        validated_rules: List[Dict[str, Any]]
    ) -> MatchedRules:
        matched = MatchedRules(
            procedure=procedure,
            city=city,
            city_tier=city_tier,
            room_category=room_category
        )

        proc_lower = procedure.lower()
        proc_keywords = [proc_lower]
        # Common procedure synonym aliases for matching
        if "cataract" in proc_lower:
            proc_keywords.extend(["cataract", "eye surgery", "ophthalm"])
        elif "append" in proc_lower:
            proc_keywords.extend(["appendectomy", "appendix"])
        elif "knee" in proc_lower or "tkr" in proc_lower:
            proc_keywords.extend(["knee replacement", "joint replacement", "arthroplasty"])
        elif "c-section" in proc_lower or "cesarean" in proc_lower or "caesarean" in proc_lower:
            proc_keywords.extend(["c-section", "caesarean", "cesarean", "maternity"])
        elif "angio" in proc_lower or "stent" in proc_lower:
            proc_keywords.extend(["angioplasty", "ptca", "cardiac stent"])

        for rule in validated_rules:
            rule_type = rule.get("rule_type")
            rule_key = str(rule.get("rule_key") or "").lower()
            source_text = str(rule.get("source_text") or "").lower()
            val = rule.get("value")
            page = rule.get("page")
            clause = rule.get("clause") or "N/A"

            # 1. Sum Insured
            if rule_type == "sum_insured":
                if matched.sum_insured is None or (isinstance(val, (int, float)) and val > (matched.sum_insured or 0)):
                    matched.sum_insured = float(val) if isinstance(val, (int, float)) else None
                    matched.sum_insured_rule = rule
                    matched.matched_citations.append({
                        "rule": "Sum Insured",
                        "details": f"INR {matched.sum_insured:,.2f}" if matched.sum_insured else str(val),
                        "page": page,
                        "clause": clause,
                        "source_text": rule.get("source_text", "")
                    })

            # 2. Co-Payment
            elif rule_type == "copay":
                if isinstance(val, (int, float)):
                    matched.copay_percent = float(val)
                    matched.copay_rule = rule
                    matched.matched_citations.append({
                        "rule": "Mandatory Co-Payment",
                        "details": f"{val:.1f}% Co-Pay Deduction",
                        "page": page,
                        "clause": clause,
                        "source_text": rule.get("source_text", "")
                    })

            # 3. Treatment Sub-Limit
            elif rule_type == "sub_limit":
                # Check if this sub-limit matches the procedure
                is_proc_match = any(kw in rule_key or kw in source_text for kw in proc_keywords)
                if is_proc_match and isinstance(val, (int, float)) and val > 0:
                    matched.procedure_sublimit = float(val)
                    matched.sublimit_rule = rule
                    matched.matched_citations.append({
                        "rule": f"{procedure} Procedure Sub-Limit",
                        "details": f"Capped at INR {val:,.2f}",
                        "page": page,
                        "clause": clause,
                        "source_text": rule.get("source_text", "")
                    })

            # 4. Room Rent Limits & Rules
            elif rule_type == "room_rent_limit":
                matched.room_rule = rule
                if isinstance(val, (int, float)) and val > 0:
                    matched.room_rent_cap_daily = float(val)
                # Check if source text mentions allowed room category
                if "single" in source_text or "standard" in source_text:
                    matched.room_allowed_category = "Standard Single Room"
                elif "twin" in source_text or "shared" in source_text:
                    matched.room_allowed_category = "Shared Room"

                # Check if source text specifies an explicit proportionate deduction formula/penalty
                prop_match = re.search(r'(\d+)\s*%\s*(?:proportionate|deduction|reduction|penalty)', source_text)
                if prop_match:
                    try:
                        matched.room_proportionate_deduction_rate = float(prop_match.group(1)) / 100.0
                    except ValueError:
                        pass

                matched.matched_citations.append({
                    "rule": "Room Rent Limit",
                    "details": f"INR {val:,.2f} / day" if isinstance(val, (int, float)) else str(val),
                    "page": page,
                    "clause": clause,
                    "source_text": rule.get("source_text", "")
                })

            # 5. Waiting Periods
            elif rule_type == "waiting_period":
                # Check if general or disease specific to procedure
                is_relevant = any(kw in rule_key or kw in source_text for kw in proc_keywords) or (
                    "initial" in source_text or "30 days" in source_text or "pre-existing" in source_text or "ped" in source_text
                )
                if is_relevant:
                    matched.waiting_period_rules.append(rule)
                    matched.matched_citations.append({
                        "rule": "Waiting Period Clause",
                        "details": f"{rule.get('value', 'Specific Waiting Period')}",
                        "page": page,
                        "clause": clause,
                        "source_text": rule.get("source_text", "")
                    })

            # 6. Exclusions
            elif rule_type == "exclusion":
                # Check if matches procedure or condition
                is_excl_match = any(kw in rule_key or kw in source_text for kw in proc_keywords)
                if is_excl_match:
                    matched.exclusion_rules.append(rule)
                    matched.matched_citations.append({
                        "rule": f"Exclusion Clause ({procedure})",
                        "details": str(rule.get("value") or "Specifically Excluded"),
                        "page": page,
                        "clause": clause,
                        "source_text": rule.get("source_text", "")
                    })

        return matched
