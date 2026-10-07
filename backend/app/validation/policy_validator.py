import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from app.extraction.normalizer import ValueNormalizer

logger = logging.getLogger(__name__)

class ValidationError(ValueError):
    """Custom exception raised when financial inputs or validation rules fail strict safety checks."""
    pass

@dataclass
class ValidationResult:
    is_valid: bool
    validated_rules: List[Dict[str, Any]] = field(default_factory=list)
    rejected_rules: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    has_sum_insured: bool = False
    has_copay: bool = False
    status: str = "VALIDATED"  # "VALIDATED", "UNABLE_TO_CONFIDENTLY_ESTIMATE", "INVALID"

class PolicyValidator:
    """
    Strict validation layer between LLM / Gemini policy extraction and the Math Engine.
    Ensures that NEVER does raw or hallucinated Gemini output pass directly to calculation,
    and guarantees all financial rules carry verifiable grounding evidence (page, clause, source text).
    """

    SUPPORTED_RULE_TYPES = {
        "sum_insured",
        "copay",
        "room_rent_limit",
        "sub_limit",
        "waiting_period",
        "exclusion"
    }

    @classmethod
    def validate_policy_rules(cls, raw_rules: List[Dict[str, Any]]) -> ValidationResult:
        """
        Validates extracted policy rules.
        Rejects or flags any rule that lacks required grounding evidence or violates financial sanity bounds.
        """
        if not raw_rules or not isinstance(raw_rules, list):
            return ValidationResult(
                is_valid=False,
                status="UNABLE_TO_CONFIDENTLY_ESTIMATE",
                errors=["No policy rules provided for validation."],
                warnings=["Policy rule set is empty."]
            )

        validated: List[Dict[str, Any]] = []
        rejected: List[Dict[str, Any]] = []
        warnings: List[str] = []
        errors: List[str] = []

        has_sum_insured = False
        has_copay = False

        for idx, rule in enumerate(raw_rules):
            if not isinstance(rule, dict):
                rejected.append({"rule_index": idx, "reason": "Rule must be a dictionary object."})
                continue

            rule_type = str(rule.get("rule_type", "")).strip().lower()
            if rule_type not in cls.SUPPORTED_RULE_TYPES:
                # Rule type not supported or recognized
                rejected.append({
                    "rule": rule,
                    "reason": f"Unsupported rule_type '{rule_type}'."
                })
                continue

            # 1. Evidence Verification: page, clause, source_text
            page = rule.get("page")
            clause = str(rule.get("clause") or "").strip()
            source_text = str(rule.get("source_text") or "").strip()
            section = str(rule.get("section") or clause or "N/A").strip()

            # Page must be a valid positive integer
            if page is None or not (isinstance(page, int) and page >= 1):
                # Try parsing if it's string representation of int
                try:
                    page = int(page)
                    if page < 1:
                        raise ValueError()
                except (TypeError, ValueError):
                    rejected.append({
                        "rule": rule,
                        "reason": f"Missing or invalid page evidence for rule '{rule_type}'. Page must be >= 1."
                    })
                    continue

            # Source text must not be empty or placeholder
            if not source_text or len(source_text) < 3:
                rejected.append({
                    "rule": rule,
                    "reason": f"Missing required source_text quotation for rule '{rule_type}'."
                })
                continue

            raw_value = rule.get("value")
            unit = str(rule.get("unit") or "").strip()
            rule_key = str(rule.get("rule_key") or rule_type).strip()

            # 2. Value and Sanity Checks by Rule Type
            rule_valid = True
            norm_value = raw_value

            if rule_type == "sum_insured":
                try:
                    norm_value = float(raw_value)
                    if norm_value < 10000.0:  # Clause number like 1.0 or 1.1
                        parsed_val = ValueNormalizer.parse_monetary_value(raw_value, source_text=source_text)
                        if parsed_val and parsed_val >= 10000.0:
                            norm_value = parsed_val
                        else:
                            # Not a valid sum insured
                            rule_valid = False

                    if rule_valid and norm_value >= 10000.0:
                        has_sum_insured = True
                    elif rule_valid and norm_value < 0:
                        rejected.append({
                            "rule": rule,
                            "reason": f"Sum Insured cannot be negative: {norm_value}"
                        })
                        rule_valid = False
                except (TypeError, ValueError):
                    parsed_val = ValueNormalizer.parse_monetary_value(raw_value, source_text=source_text)
                    if parsed_val and parsed_val >= 10000.0:
                        norm_value = parsed_val
                        has_sum_insured = True
                    else:
                        rejected.append({
                            "rule": rule,
                            "reason": f"Sum Insured value must be numeric, got '{raw_value}'."
                        })
                        rule_valid = False

            elif rule_type == "copay":
                try:
                    norm_value = float(raw_value)
                    if not (0.0 <= norm_value <= 100.0):
                        rejected.append({
                            "rule": rule,
                            "reason": f"Co-payment percentage must be between 0 and 100, got {norm_value}."
                        })
                        rule_valid = False
                    else:
                        has_copay = True
                except (TypeError, ValueError):
                    parsed_pct = ValueNormalizer.parse_percentage_value(raw_value, source_text=source_text)
                    if 0.0 <= parsed_pct <= 100.0:
                        norm_value = parsed_pct
                        has_copay = True
                    else:
                        rejected.append({
                            "rule": rule,
                            "reason": f"Co-payment value must be numeric, got '{raw_value}'."
                        })
                        rule_valid = False

            elif rule_type == "room_rent_limit":
                try:
                    norm_value = float(raw_value)
                    if norm_value < 100.0:
                        parsed_room = ValueNormalizer.parse_monetary_value(raw_value, source_text=source_text)
                        if parsed_room:
                            norm_value = parsed_room
                    if norm_value < 0:
                        rejected.append({
                            "rule": rule,
                            "reason": f"Room rent limit cannot be negative, got {norm_value}."
                        })
                        rule_valid = False
                except (TypeError, ValueError):
                    parsed_room = ValueNormalizer.parse_monetary_value(raw_value, source_text=source_text)
                    if parsed_room:
                        norm_value = parsed_room
                    elif isinstance(raw_value, str) and "%" in raw_value:
                        norm_value = raw_value
                    else:
                        rejected.append({
                            "rule": rule,
                            "reason": f"Room rent limit value must be numeric or valid rate, got '{raw_value}'."
                        })
                        rule_valid = False

            elif rule_type == "sub_limit":
                try:
                    norm_value = float(raw_value)
                    if norm_value < 100.0:  # Clause number like 2.0, 2.2, 2.3
                        parsed_sub = ValueNormalizer.parse_monetary_value(raw_value, source_text=source_text)
                        if parsed_sub:
                            norm_value = parsed_sub
                    if norm_value < 0:
                        rejected.append({
                            "rule": rule,
                            "reason": f"Sub-limit cannot be negative, got {norm_value}."
                        })
                        rule_valid = False
                except (TypeError, ValueError):
                    parsed_sub = ValueNormalizer.parse_monetary_value(raw_value, source_text=source_text)
                    if parsed_sub:
                        norm_value = parsed_sub
                    else:
                        rejected.append({
                            "rule": rule,
                            "reason": f"Sub-limit value must be numeric, got '{raw_value}'."
                        })
                        rule_valid = False

            elif rule_type in ("waiting_period", "exclusion"):
                # Non-monetary rules: ensure source_text is present and meaningful
                if not norm_value:
                    norm_value = source_text

            if rule_valid:
                validated_rule = {
                    "rule_type": rule_type,
                    "rule_key": rule_key,
                    "value": norm_value,
                    "unit": unit or ("INR" if rule_type in ("sum_insured", "sub_limit", "room_rent_limit") else "percent" if rule_type == "copay" else "text"),
                    "page": page,
                    "clause": clause or "N/A",
                    "source_text": source_text,
                    "section": section,
                    "confidence": rule.get("confidence", "HIGH")
                }
                validated.append(validated_rule)

        # Final assessment
        is_usable = len(validated) > 0
        status = "VALIDATED" if is_usable else "UNABLE_TO_CONFIDENTLY_ESTIMATE"

        if not has_sum_insured:
            warnings.append("No grounded Sum Insured rule was validated from the policy.")

        return ValidationResult(
            is_valid=is_usable,
            validated_rules=validated,
            rejected_rules=rejected,
            warnings=warnings,
            errors=errors,
            has_sum_insured=has_sum_insured,
            has_copay=has_copay,
            status=status
        )

    @staticmethod
    def validate_calculation_inputs(
        treatment_min: float,
        treatment_max: float,
        room_category: str = "Standard",
        copay_percent: Optional[float] = None,
        sub_limit: Optional[float] = None,
        sum_insured: Optional[float] = None
    ) -> None:
        """
        Safety validation on calculation parameters (Phase 14).
        Raises ValidationError if any numeric sanity condition is violated.
        Never silently converts invalid data.
        """
        # 1. Type checks
        if not isinstance(treatment_min, (int, float)) or not isinstance(treatment_max, (int, float)):
            raise ValidationError(f"Treatment costs must be numeric. Got min={type(treatment_min)}, max={type(treatment_max)}.")

        treatment_min = float(treatment_min)
        treatment_max = float(treatment_max)

        # 2. Non-negative bounds
        if treatment_min < 0 or treatment_max < 0:
            raise ValidationError(f"Treatment costs cannot be negative. Got min={treatment_min}, max={treatment_max}.")

        # 3. Range sanity: min <= max
        if treatment_min > treatment_max:
            raise ValidationError(
                f"Invalid treatment cost range: min ({treatment_min}) cannot be strictly greater than max ({treatment_max})."
            )

        # 4. Co-pay check if provided
        if copay_percent is not None:
            if not isinstance(copay_percent, (int, float)):
                raise ValidationError(f"Co-pay percent must be numeric, got {type(copay_percent)}.")
            if not (0.0 <= float(copay_percent) <= 100.0):
                raise ValidationError(f"Co-payment percentage must be between 0 and 100, got {copay_percent}.")

        # 5. Sub-limit check if provided
        if sub_limit is not None:
            if not isinstance(sub_limit, (int, float)):
                raise ValidationError(f"Sub-limit must be numeric, got {type(sub_limit)}.")
            if float(sub_limit) < 0:
                raise ValidationError(f"Sub-limit cannot be negative, got {sub_limit}.")

        # 6. Sum insured check if provided
        if sum_insured is not None:
            if not isinstance(sum_insured, (int, float)):
                raise ValidationError(f"Sum Insured must be numeric, got {type(sum_insured)}.")
            if float(sum_insured) < 0:
                raise ValidationError(f"Sum Insured cannot be negative, got {sum_insured}.")

        # 7. Room category
        if not room_category or not isinstance(room_category, str):
            raise ValidationError(f"Room category must be a non-empty string, got {room_category}.")
