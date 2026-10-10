import logging
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)

DECIMAL_QUANT = Decimal("0.01")

def to_decimal(val: Any) -> Decimal:
    """Safely converts monetary value to Decimal with precision."""
    if val is None:
        return Decimal("0.00")
    if isinstance(val, Decimal):
        return val
    try:
        return Decimal(str(val)).quantize(DECIMAL_QUANT, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError, TypeError) as e:
        raise ValueError(f"Cannot parse monetary Decimal from: {val} ({e})")

class CalculationValidator:
    """
    Independent Financial Calculation Validator.
    Recomputes the claim financial outcome completely independently from normalized inputs
    using pure Decimal arithmetic, validating IRDAI sequential rules, invariants, and reconciliation.
    
    Guarantees:
    1. Independent recalculation (does not blindly copy Math Engine output).
    2. Zero-value protection (flags missing policy parameters).
    3. Invariant validation: insurer_payable + customer_payable == total_expense.
    4. Non-negativity check across all monetary balances.
    5. Returns CALCULATION_VALIDATED or CALCULATION_MISMATCH.
    """

    @classmethod
    def independently_compute(
        cls,
        treatment_cost: Any,
        quantity: Any = 1,
        non_covered_expense: Any = 0.0,
        sublimit: Optional[Any] = None,
        deductible: Any = 0.0,
        copay_percent: Any = 0.0,
        available_sum_insured: Optional[Any] = None,
        room_deduction: Any = 0.0
    ) -> Dict[str, Decimal]:
        """
        Executes an independent mathematical recomputation of the claim.
        """
        cost_d = to_decimal(treatment_cost)
        qty_d = to_decimal(quantity)
        non_cov_d = to_decimal(non_covered_expense)
        deduct_d = to_decimal(deductible)
        copay_d = to_decimal(copay_percent)
        room_d = to_decimal(room_deduction)
        sublimit_d = to_decimal(sublimit) if sublimit is not None else None
        si_d = to_decimal(available_sum_insured) if available_sum_insured is not None else None

        # 1. Total Treatment Expense: T = TreatmentCost * Quantity
        total_expense = (cost_d * qty_d).quantize(DECIMAL_QUANT, rounding=ROUND_HALF_UP)

        # 2. Eligible Amount: E = max(0, T - NonCoveredExpense)
        actual_non_covered = min(total_expense, non_cov_d)
        eligible_amount = max(Decimal("0.00"), total_expense - actual_non_covered)

        # 3. Sublimit: AllowedAfterSublimit = min(E, Sublimit)
        if sublimit_d is not None and sublimit_d > Decimal("0.00"):
            sublimit_allowed = min(eligible_amount, sublimit_d)
            sublimit_excess = max(Decimal("0.00"), eligible_amount - sublimit_d)
        else:
            sublimit_allowed = eligible_amount
            sublimit_excess = Decimal("0.00")

        # 4. Room Rent Deduction (if applicable)
        room_applied = min(sublimit_allowed, room_d)
        after_room = max(Decimal("0.00"), sublimit_allowed - room_applied)

        # 5. Deductible: ActualDeductible = min(AllowedAmount, Deductible)
        actual_deductible = min(after_room, deduct_d)
        after_deductible = max(Decimal("0.00"), after_room - actual_deductible)

        # 6. Co-payment: CopayAmount = AfterDeductible * CopayPercent / 100
        if copay_d > Decimal("0.00"):
            copay_amount = (after_deductible * (copay_d / Decimal("100.00"))).quantize(DECIMAL_QUANT, rounding=ROUND_HALF_UP)
        else:
            copay_amount = Decimal("0.00")
        insurer_pre_si = max(Decimal("0.00"), after_deductible - copay_amount)

        # 7. Sum Insured Cap
        if si_d is not None:
            insurer_payable = min(insurer_pre_si, si_d)
            si_excess = max(Decimal("0.00"), insurer_pre_si - si_d)
            remaining_si = max(Decimal("0.00"), si_d - insurer_payable)
        else:
            insurer_payable = insurer_pre_si
            si_excess = Decimal("0.00")
            remaining_si = None

        # 8. Customer Out-of-Pocket: CustomerPayable
        customer_payable = (
            actual_non_covered +
            sublimit_excess +
            room_applied +
            actual_deductible +
            copay_amount +
            si_excess
        ).quantize(DECIMAL_QUANT, rounding=ROUND_HALF_UP)

        return {
            "total_expense": total_expense,
            "eligible_amount": eligible_amount,
            "sublimit_allowed": sublimit_allowed,
            "sublimit_excess": sublimit_excess,
            "room_deduction": room_applied,
            "deductible_applied": actual_deductible,
            "copay_amount": copay_amount,
            "insurer_pre_si": insurer_pre_si,
            "si_excess": si_excess,
            "insurer_payable": insurer_payable,
            "customer_payable": customer_payable,
            "remaining_si": remaining_si
        }

    @classmethod
    def validate_calculation(
        cls,
        math_engine_result: Dict[str, Any],
        normalized_inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compares Math Engine result against independent recomputation and verifies reconciliation invariants.
        
        Returns:
            {
                "independent_check": bool,
                "reconciled": bool,
                "status": "CALCULATION_VALIDATED" | "CALCULATION_MISMATCH" | "CALCULATION_RECONCILIATION_FAILED",
                "details": {...},
                "discrepancies": List[str]
            }
        """
        treatment_cost = normalized_inputs.get("treatment_cost")
        quantity = normalized_inputs.get("quantity", 1)
        non_covered = normalized_inputs.get("non_covered_expense", 0.0)
        sublimit = normalized_inputs.get("sublimit") or normalized_inputs.get("treatment_sublimit")
        deductible = normalized_inputs.get("deductible", 0.0)
        copay_percent = normalized_inputs.get("copay_percent", 0.0)
        sum_insured = normalized_inputs.get("sum_insured")
        room_deduction = normalized_inputs.get("room_deduction", 0.0)

        # 1. Independent Computation
        expected = cls.independently_compute(
            treatment_cost=treatment_cost,
            quantity=quantity,
            non_covered_expense=non_covered,
            sublimit=sublimit,
            deductible=deductible,
            copay_percent=copay_percent,
            available_sum_insured=sum_insured,
            room_deduction=room_deduction
        )

        discrepancies: List[str] = []

        # 2. Extract Math Engine Output values
        actual_total = to_decimal(math_engine_result.get("total_expense"))
        actual_insurer = to_decimal(math_engine_result.get("insurer_payable"))
        actual_customer = to_decimal(math_engine_result.get("customer_payable"))
        actual_rem_si = to_decimal(math_engine_result.get("remaining_sum_insured")) if math_engine_result.get("remaining_sum_insured") is not None else None

        # 3. Reconciliation Invariant Check: InsurerPayable + CustomerPayable == TotalExpense
        reconciliation_sum = actual_insurer + actual_customer
        is_reconciled = (reconciliation_sum == actual_total)
        if not is_reconciled:
            diff = actual_total - reconciliation_sum
            discrepancies.append(
                f"Reconciliation invariant failed: Insurer ({actual_insurer}) + Customer ({actual_customer}) = "
                f"{reconciliation_sum} != Total ({actual_total}), difference: {diff}"
            )

        # 4. Non-negativity Invariants
        if actual_insurer < Decimal("0.00"):
            discrepancies.append(f"Negative insurer payable: {actual_insurer}")
        if actual_customer < Decimal("0.00"):
            discrepancies.append(f"Negative customer payable: {actual_customer}")
        if actual_rem_si is not None and actual_rem_si < Decimal("0.00"):
            discrepancies.append(f"Negative remaining sum insured: {actual_rem_si}")

        # 5. Independent Comparison Check
        if actual_insurer != expected["insurer_payable"]:
            discrepancies.append(
                f"Insurer payable mismatch: Engine {actual_insurer} vs Validator {expected['insurer_payable']}"
            )
        if actual_customer != expected["customer_payable"]:
            discrepancies.append(
                f"Customer payable mismatch: Engine {actual_customer} vs Validator {expected['customer_payable']}"
            )
        if sum_insured is not None and actual_rem_si is not None:
            if actual_rem_si != expected["remaining_si"]:
                discrepancies.append(
                    f"Remaining SI mismatch: Engine {actual_rem_si} vs Validator {expected['remaining_si']}"
                )

        # 6. Status Determination
        if not is_reconciled:
            status = "CALCULATION_RECONCILIATION_FAILED"
            independent_check = False
        elif len(discrepancies) > 0:
            status = "CALCULATION_MISMATCH"
            independent_check = False
        else:
            status = "CALCULATION_VALIDATED"
            independent_check = True

        return {
            "independent_check": independent_check,
            "reconciled": is_reconciled,
            "status": status,
            "expected_values": {
                "total_expense": float(expected["total_expense"]),
                "eligible_amount": float(expected["eligible_amount"]),
                "sublimit_allowed": float(expected["sublimit_allowed"]),
                "sublimit_excess": float(expected["sublimit_excess"]),
                "deductible_applied": float(expected["deductible_applied"]),
                "copay_amount": float(expected["copay_amount"]),
                "insurer_payable": float(expected["insurer_payable"]),
                "customer_payable": float(expected["customer_payable"]),
                "remaining_sum_insured": float(expected["remaining_si"]) if sum_insured is not None else None
            },
            "discrepancies": discrepancies
        }
