from typing import Dict, Any, Optional

class MathEngine:
    """
    Step 8 & 9: Deterministic Math Engine for Health Insurance Claims Calculation.
    
    Principles:
    - Pure Python deterministic math.
    - Zero AI/LLM intervention in calculating financial numbers.
    - No hardcoded demo values.
    - Capped at Sum Insured without assuming unverified balances.
    """

    @staticmethod
    def calculate(
        cost_min: float,
        cost_max: float,
        copay_percent: float = 0.0,
        treatment_sublimit: Optional[float] = None,
        sum_insured: Optional[float] = None,
        room_penalty_ratio: float = 0.0
    ) -> Dict[str, Any]:
        """
        Calculates eligible claim amount, co-payment deductions, insurance contribution,
        and patient payable liability across min and max scenarios.
        """
        cost_min = float(cost_min)
        cost_max = float(cost_max)
        copay_percent = float(copay_percent)
        room_penalty_ratio = max(0.0, min(1.0, float(room_penalty_ratio)))

        # 1. Base Eligible Amount
        eligible_min = cost_min
        eligible_max = cost_max

        # 2. Procedure Sub-Limit Capping
        if treatment_sublimit is not None and treatment_sublimit > 0:
            eligible_min = min(eligible_min, float(treatment_sublimit))
            eligible_max = min(eligible_max, float(treatment_sublimit))

        # 3. Policy-defined Room Upgrade Penalty (if grounded in policy text)
        if room_penalty_ratio > 0.0:
            retained_factor = 1.0 - room_penalty_ratio
            eligible_min = eligible_min * retained_factor
            eligible_max = eligible_max * retained_factor

        # 4. Step 9: Available Sum Insured Check
        if sum_insured is not None and sum_insured > 0:
            eligible_min = min(eligible_min, float(sum_insured))
            eligible_max = min(eligible_max, float(sum_insured))

        # 5. Co-Payment Amount
        copay_min = eligible_min * (copay_percent / 100.0)
        copay_max = eligible_max * (copay_percent / 100.0)

        # 6. Insurance Contribution (cannot exceed Sum Insured or eligible amount)
        insurance_min = max(0.0, eligible_min - copay_min)
        insurance_max = max(0.0, eligible_max - copay_max)

        if sum_insured is not None and sum_insured > 0:
            insurance_min = min(insurance_min, float(sum_insured))
            insurance_max = min(insurance_max, float(sum_insured))

        # 7. Patient Payable Out-of-Pocket Liability
        patient_min = max(0.0, cost_min - insurance_min)
        patient_max = max(0.0, cost_max - insurance_max)

        return {
            "treatment_cost": {
                "min": round(cost_min, 2),
                "max": round(cost_max, 2)
            },
            "applicable_sublimit": round(treatment_sublimit, 2) if treatment_sublimit else None,
            "eligible_amount": {
                "min": round(eligible_min, 2),
                "max": round(eligible_max, 2)
            },
            "copay_percent": round(copay_percent, 2),
            "copay_amount": {
                "min": round(copay_min, 2),
                "max": round(copay_max, 2)
            },
            "insurance_contribution": {
                "min": round(insurance_min, 2),
                "max": round(insurance_max, 2)
            },
            "patient_payable": {
                "min": round(patient_min, 2),
                "max": round(patient_max, 2)
            }
        }
