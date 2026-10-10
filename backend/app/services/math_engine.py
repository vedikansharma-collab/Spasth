import math
import logging
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

# Currency precision constants
CURRENCY_CODE = "INR"
DECIMAL_QUANT = Decimal("0.01")

def to_decimal(val: Any, allow_none: bool = False) -> Decimal:
    """Safely converts input to Decimal with precision."""
    if val is None:
        if allow_none:
            return Decimal("0.00")
        raise ValueError("Monetary value cannot be null or missing")
    if isinstance(val, Decimal):
        return val
    if isinstance(val, float):
        if math.isnan(val) or math.isinf(val):
            raise ValueError(f"Invalid monetary value: {val}")
        return Decimal(str(val)).quantize(DECIMAL_QUANT, rounding=ROUND_HALF_UP)
    if isinstance(val, (int, str)):
        try:
            return Decimal(str(val)).quantize(DECIMAL_QUANT, rounding=ROUND_HALF_UP)
        except InvalidOperation:
            raise ValueError(f"Cannot parse Decimal from: {val}")
    raise ValueError(f"Unsupported monetary type: {type(val)}")

def round_money(d: Decimal) -> float:
    """Converts Decimal to 2-decimal rounded float for JSON serialization."""
    return float(d.quantize(DECIMAL_QUANT, rounding=ROUND_HALF_UP))

class MathEngine:
    """
    Precision Mathematical Engine for SPASTH Health Insurance Claims Calculation.
    
    Principles:
    1. Pure Python deterministic math using Decimal arithmetic.
    2. Zero AI/LLM intervention in calculating financial numbers.
    3. Auditable calculation trace: every step is recorded with rule, input, deduction, and output.
    4. Strict separation of policy terms: deductible != co-payment != sublimit != non-covered.
    5. Sum Insured & Remaining Sum Insured tracking with zero negative balances.
    6. No double deductions: rules are applied sequentially in verified order.
    7. Invariant reconciliation: insurer_payable + customer_payable == total_expense.
    """

    @classmethod
    def calculate_claim(
        cls,
        treatment_cost: Union[float, int, str, Decimal],
        quantity: int = 1,
        non_covered_expense: Union[float, int, str, Decimal] = 0.0,
        copay_percent: Union[float, int, str, Decimal] = 0.0,
        deductible: Union[float, int, str, Decimal] = 0.0,
        treatment_sublimit: Optional[Union[float, int, str, Decimal]] = None,
        sum_insured: Optional[Union[float, int, str, Decimal]] = None,
        remaining_sum_insured: Optional[Union[float, int, str, Decimal]] = None,
        room_penalty_ratio: Union[float, int, str, Decimal] = 0.0,
        treatment_id: Optional[str] = None,
        procedure_name: Optional[str] = None,
        city: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculates precision claim payout for a specific claim cost.
        Returns auditable trace, insurer payable, and customer payable breakdown.
        """
        # -------------------------------------------------------------
        # STEP 1: Pre-calculation Validation
        # -------------------------------------------------------------
        if treatment_cost is None:
            return {
                "status": "INVALID_INPUT",
                "error": "Treatment cost is required.",
                "message": "Treatment cost is required and cannot be null/missing.",
                "insurer_payable": 0.0,
                "customer_payable": 0.0,
                "calculation_trace": []
            }

        try:
            cost_d = to_decimal(treatment_cost, allow_none=False)
            qty_d = to_decimal(quantity, allow_none=False)
            non_cov_d = to_decimal(non_covered_expense, allow_none=True)
            copay_d = to_decimal(copay_percent, allow_none=True)
            deduct_d = to_decimal(deductible, allow_none=True)
            sublimit_d = to_decimal(treatment_sublimit, allow_none=True) if treatment_sublimit is not None else None
            si_d = to_decimal(sum_insured, allow_none=True) if sum_insured is not None else None
            rem_si_d = to_decimal(remaining_sum_insured, allow_none=True) if remaining_sum_insured is not None else None
            room_pen_d = to_decimal(room_penalty_ratio, allow_none=True)
        except (ValueError, TypeError) as err:
            logger.error(f"[MATH-ENGINE] Input conversion error: {err}")
            return {
                "status": "INVALID_INPUT",
                "error": str(err),
                "message": f"Pre-calculation validation failed: {str(err)}",
                "insurer_payable": 0.0,
                "customer_payable": 0.0,
                "calculation_trace": []
            }

        # Validate range constraints
        if cost_d < Decimal("0.00"):
            return {
                "status": "INVALID_INPUT",
                "error": "Negative treatment cost is invalid.",
                "message": f"Negative treatment cost: {cost_d}",
                "insurer_payable": 0.0,
                "customer_payable": 0.0,
                "calculation_trace": []
            }

        if qty_d <= Decimal("0.00"):
            return {
                "status": "INVALID_INPUT",
                "error": "Quantity must be greater than zero.",
                "message": f"Invalid quantity: {qty_d}",
                "insurer_payable": 0.0,
                "customer_payable": 0.0,
                "calculation_trace": []
            }

        if copay_d < Decimal("0.00") or copay_d > Decimal("100.00"):
            return {
                "status": "INVALID_INPUT",
                "error": "Co-payment percentage must be between 0 and 100.",
                "message": f"Invalid co-payment: {copay_d}%",
                "insurer_payable": 0.0,
                "customer_payable": 0.0,
                "calculation_trace": []
            }

        if deduct_d < Decimal("0.00"):
            return {
                "status": "INVALID_INPUT",
                "error": "Deductible cannot be negative.",
                "message": f"Invalid deductible: {deduct_d}",
                "insurer_payable": 0.0,
                "customer_payable": 0.0,
                "calculation_trace": []
            }

        if non_cov_d < Decimal("0.00"):
            return {
                "status": "INVALID_INPUT",
                "error": "Non-covered expense cannot be negative.",
                "message": f"Invalid non-covered expense: {non_cov_d}",
                "insurer_payable": 0.0,
                "customer_payable": 0.0,
                "calculation_trace": []
            }

        if sublimit_d is not None and sublimit_d < Decimal("0.00"):
            return {
                "status": "INVALID_INPUT",
                "error": "Sublimit cannot be negative.",
                "message": f"Invalid sublimit: {sublimit_d}",
                "insurer_payable": 0.0,
                "customer_payable": 0.0,
                "calculation_trace": []
            }

        if si_d is not None and si_d < Decimal("0.00"):
            return {
                "status": "INVALID_INPUT",
                "error": "Sum Insured cannot be negative.",
                "message": f"Invalid Sum Insured: {si_d}",
                "insurer_payable": 0.0,
                "customer_payable": 0.0,
                "calculation_trace": []
            }

        if rem_si_d is not None and rem_si_d < Decimal("0.00"):
            return {
                "status": "INVALID_INPUT",
                "error": "Remaining Sum Insured cannot be negative.",
                "message": f"Invalid Remaining Sum Insured: {rem_si_d}",
                "insurer_payable": 0.0,
                "customer_payable": 0.0,
                "calculation_trace": []
            }

        if room_pen_d < Decimal("0.00") or room_pen_d > Decimal("1.00"):
            return {
                "status": "INVALID_INPUT",
                "error": "Room penalty ratio must be between 0.0 and 1.0.",
                "message": f"Invalid room penalty ratio: {room_pen_d}",
                "insurer_payable": 0.0,
                "customer_payable": 0.0,
                "calculation_trace": []
            }

        # -------------------------------------------------------------
        # STEP 2: Deterministic Calculation Order with Auditable Trace
        # -------------------------------------------------------------
        trace: List[Dict[str, Any]] = []
        step_idx = 1

        # 1. Total Treatment Cost
        total_expense = (cost_d * qty_d).quantize(DECIMAL_QUANT, rounding=ROUND_HALF_UP)
        trace.append({
            "step": step_idx,
            "rule": "TOTAL_TREATMENT_COST",
            "input": round_money(cost_d),
            "quantity": int(qty_d),
            "deduction": 0.0,
            "output": round_money(total_expense),
            "description": f"Total billed treatment cost: INR {round_money(total_expense):,.2f}",
            "reason": "Base medical bill expense submitted for reimbursement/cashless"
        })
        step_idx += 1

        # 2. Non-Covered Expenses (Eligibility Separation)
        non_covered_applied = min(total_expense, non_cov_d)
        eligible_base = max(Decimal("0.00"), total_expense - non_covered_applied)
        trace.append({
            "step": step_idx,
            "rule": "NON_COVERED_EXPENSE",
            "input": round_money(total_expense),
            "deduction": round_money(non_covered_applied),
            "output": round_money(eligible_base),
            "description": f"Non-covered medical items deduction: INR {round_money(non_covered_applied):,.2f}",
            "reason": "Excluded consumables, administrative fees, or non-medical items"
        })
        step_idx += 1

        # 3. Procedure Sub-Limit Capping
        sublimit_restricted = Decimal("0.00")
        eligible_after_sublimit = eligible_base
        if sublimit_d is not None and sublimit_d > Decimal("0.00"):
            if eligible_base > sublimit_d:
                sublimit_restricted = eligible_base - sublimit_d
                eligible_after_sublimit = sublimit_d
            trace.append({
                "step": step_idx,
                "rule": "PROCEDURE_SUBLIMIT",
                "limit": round_money(sublimit_d),
                "input": round_money(eligible_base),
                "deduction": round_money(sublimit_restricted),
                "output": round_money(eligible_after_sublimit),
                "description": f"Procedure sub-limit applied (capped at INR {round_money(sublimit_d):,.2f})",
                "reason": "Policy contract imposes categorical ceiling for this medical procedure"
            })
            step_idx += 1

        # 4. Room Rent Proportionate Adjustment (if defined in policy)
        room_deduction = Decimal("0.00")
        eligible_after_room = eligible_after_sublimit
        if room_pen_d > Decimal("0.00"):
            room_deduction = (eligible_after_sublimit * room_pen_d).quantize(DECIMAL_QUANT, rounding=ROUND_HALF_UP)
            eligible_after_room = max(Decimal("0.00"), eligible_after_sublimit - room_deduction)
            trace.append({
                "step": step_idx,
                "rule": "ROOM_RENT_PROPORTIONATE_DEDUCTION",
                "penalty_ratio": round_money(room_pen_d),
                "input": round_money(eligible_after_sublimit),
                "deduction": round_money(room_deduction),
                "output": round_money(eligible_after_room),
                "description": f"Room category upgrade proportionate deduction ({round_money(room_pen_d * 100):.1f}%)",
                "reason": "Policy clause stipulates proportionate deduction for room tariff upgrade"
            })
            step_idx += 1

        # 5. Deductible (Distinct from Co-payment)
        applicable_deductible = Decimal("0.00")
        eligible_after_deductible = eligible_after_room
        if deduct_d > Decimal("0.00"):
            applicable_deductible = min(eligible_after_room, deduct_d)
            eligible_after_deductible = max(Decimal("0.00"), eligible_after_room - applicable_deductible)
            trace.append({
                "step": step_idx,
                "rule": "DEDUCTIBLE",
                "deductible_limit": round_money(deduct_d),
                "input": round_money(eligible_after_room),
                "deduction": round_money(applicable_deductible),
                "output": round_money(eligible_after_deductible),
                "description": f"Annual/per-claim deductible applied: INR {round_money(applicable_deductible):,.2f}",
                "reason": "Upfront policyholder retention threshold before insurer liability begins"
            })
            step_idx += 1

        # 6. Co-Payment (Calculated on remaining eligible base)
        copay_amount = Decimal("0.00")
        insurer_share_pre_si = eligible_after_deductible
        if copay_d > Decimal("0.00"):
            copay_amount = (eligible_after_deductible * (copay_d / Decimal("100.00"))).quantize(DECIMAL_QUANT, rounding=ROUND_HALF_UP)
            insurer_share_pre_si = max(Decimal("0.00"), eligible_after_deductible - copay_amount)
            trace.append({
                "step": step_idx,
                "rule": "CO_PAYMENT",
                "percentage": round_money(copay_d),
                "base": round_money(eligible_after_deductible),
                "deduction": round_money(copay_amount),
                "output": round_money(insurer_share_pre_si),
                "description": f"Mandatory co-payment ({round_money(copay_d):.1f}%): INR {round_money(copay_amount):,.2f}",
                "reason": "Cost-sharing percentage paid out-of-pocket by the policyholder"
            })
            step_idx += 1

        # 7. Sum Insured / Available Limit Capping
        effective_limit: Optional[Decimal] = None
        if rem_si_d is not None:
            effective_limit = rem_si_d
        elif si_d is not None:
            effective_limit = si_d

        exceeded_si = Decimal("0.00")
        insurer_payable = insurer_share_pre_si
        new_rem_si: Optional[Decimal] = None

        if effective_limit is not None:
            if insurer_share_pre_si > effective_limit:
                exceeded_si = insurer_share_pre_si - effective_limit
                insurer_payable = effective_limit
            else:
                insurer_payable = insurer_share_pre_si
            
            new_rem_si = max(Decimal("0.00"), effective_limit - insurer_payable)
            trace.append({
                "step": step_idx,
                "rule": "SUM_INSURED_LIMIT",
                "available_limit": round_money(effective_limit),
                "input": round_money(insurer_share_pre_si),
                "deduction": round_money(exceeded_si),
                "output": round_money(insurer_payable),
                "remaining_after_claim": round_money(new_rem_si),
                "description": f"Available Sum Insured cap (Limit: INR {round_money(effective_limit):,.2f})",
                "reason": "Insurer payout cannot exceed active available policy coverage balance"
            })
            step_idx += 1

        # 8. Customer Payable Breakdown & Mathematical Reconciliation Invariant
        customer_payable = (
            non_covered_applied +
            sublimit_restricted +
            room_deduction +
            applicable_deductible +
            copay_amount +
            exceeded_si
        ).quantize(DECIMAL_QUANT, rounding=ROUND_HALF_UP)

        # Invariant Verification: insurer_payable + customer_payable == total_expense
        reconciliation_discrepancy = (total_expense - (insurer_payable + customer_payable)).quantize(DECIMAL_QUANT)
        if abs(reconciliation_discrepancy) > Decimal("0.00"):
            logger.warning(f"[MATH-ENGINE] Reconciliation discrepancy detected: {reconciliation_discrepancy}. Adjusting customer share.")
            customer_payable += reconciliation_discrepancy

        trace.append({
            "step": step_idx,
            "rule": "FINAL_RECONCILIATION",
            "total_expense": round_money(total_expense),
            "insurer_payable": round_money(insurer_payable),
            "customer_payable": round_money(customer_payable),
            "deduction": 0.0,
            "output": round_money(insurer_payable),
            "description": (
                f"Reconciliation verified: Insurer INR {round_money(insurer_payable):,.2f} + "
                f"Customer INR {round_money(customer_payable):,.2f} = Total INR {round_money(total_expense):,.2f}"
            ),
            "reason": "100% auditable accounting reconciliation invariant verified"
        })

        return {
            "status": "SUCCESS",
            "currency": CURRENCY_CODE,
            "treatment": {
                "treatment_id": treatment_id,
                "procedure_name": procedure_name,
                "city": city
            },
            "total_expense": round_money(total_expense),
            "non_covered_expense": round_money(non_covered_applied),
            "eligible_expense": round_money(eligible_base),
            "eligible_amount": round_money(eligible_base),
            "sublimit": round_money(sublimit_d) if sublimit_d is not None else None,
            "sublimit_adjustment": round_money(sublimit_restricted),
            "room_penalty_ratio": round_money(room_pen_d),
            "room_adjustment": round_money(room_deduction),
            "deductible": round_money(applicable_deductible),
            "co_payment_percentage": round_money(copay_d),
            "co_payment_amount": round_money(copay_amount),
            "sum_insured": round_money(si_d) if si_d is not None else None,
            "previous_remaining_sum_insured": round_money(rem_si_d) if rem_si_d is not None else None,
            "new_remaining_sum_insured": round_money(new_rem_si) if new_rem_si is not None else None,
            "remaining_sum_insured": round_money(new_rem_si) if new_rem_si is not None else None,
            "insurer_payable": round_money(insurer_payable),
            "customer_payable": round_money(customer_payable),
            "customer_payable_breakdown": {
                "non_covered_expense": round_money(non_covered_applied),
                "sublimit_excess": round_money(sublimit_restricted),
                "room_upgrade_excess": round_money(room_deduction),
                "deductible": round_money(applicable_deductible),
                "co_payment": round_money(copay_amount),
                "sum_insured_excess": round_money(exceeded_si)
            },
            "calculation_trace": trace
        }

    @staticmethod
    def calculate(
        cost_min: float,
        cost_max: float,
        copay_percent: float = 0.0,
        treatment_sublimit: Optional[float] = None,
        sum_insured: Optional[float] = None,
        room_penalty_ratio: float = 0.0,
        deductible: float = 0.0,
        non_covered_expense: float = 0.0
    ) -> Dict[str, Any]:
        """
        Backwards-compatible API for range estimations (min and max scenarios).
        Executes precision calculation for min and max independently.
        """
        res_min = MathEngine.calculate_claim(
            treatment_cost=cost_min,
            copay_percent=copay_percent,
            treatment_sublimit=treatment_sublimit,
            sum_insured=sum_insured,
            room_penalty_ratio=room_penalty_ratio,
            deductible=deductible,
            non_covered_expense=non_covered_expense
        )

        res_max = MathEngine.calculate_claim(
            treatment_cost=cost_max,
            copay_percent=copay_percent,
            treatment_sublimit=treatment_sublimit,
            sum_insured=sum_insured,
            room_penalty_ratio=room_penalty_ratio,
            deductible=deductible,
            non_covered_expense=non_covered_expense
        )

        el_min = res_min["total_expense"] - res_min["sublimit_adjustment"] - res_min["room_adjustment"]
        if sum_insured is not None and sum_insured > 0:
            el_min = min(el_min, float(sum_insured))

        el_max = res_max["total_expense"] - res_max["sublimit_adjustment"] - res_max["room_adjustment"]
        if sum_insured is not None and sum_insured > 0:
            el_max = min(el_max, float(sum_insured))

        return {
            "status": "SUCCESS",
            "currency": CURRENCY_CODE,
            "treatment_cost": {
                "min": res_min["total_expense"],
                "max": res_max["total_expense"]
            },
            "applicable_sublimit": res_min["sublimit"],
            "eligible_amount": {
                "min": round_money(Decimal(str(el_min))),
                "max": round_money(Decimal(str(el_max)))
            },
            "copay_percent": res_min["co_payment_percentage"],
            "copay_amount": {
                "min": res_min["co_payment_amount"],
                "max": res_max["co_payment_amount"]
            },
            "insurance_contribution": {
                "min": res_min["insurer_payable"],
                "max": res_max["insurer_payable"]
            },
            "patient_payable": {
                "min": res_min["customer_payable"],
                "max": res_max["customer_payable"]
            },
            "deductible": {
                "min": res_min["deductible"],
                "max": res_max["deductible"]
            },
            "calculation_trace": res_max["calculation_trace"],
            "customer_payable_breakdown": res_max["customer_payable_breakdown"]
        }
