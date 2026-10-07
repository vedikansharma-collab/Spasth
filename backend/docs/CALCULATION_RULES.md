# Spasth Financial Calculation & Rule Engine Specification

## Overview

This document specifies the deterministic mathematical rules and policy verification logic implemented in the Spasth (FIN-01) Treatment Cost Calculator backend.

In accordance with strict architectural guarantees:
- **LLMs (Gemini) NEVER compute financial amounts.** Gemini only extracts and interprets policy text clauses into structured policy rule representations with page numbers, clauses, and source text quotes.
- **The Python Math Engine performs 100% of the mathematical calculations.**
- **No universal percentages (like arbitrary 30% Deluxe room penalties) are hardcoded.** Any deduction must be grounded in verified contract text; otherwise, the engine flags uncertainty.
- **Synthetic treatment cost benchmarks are explicitly labeled as `synthetic`** and never presented as official hospital quotations.

---

## Processing Flow

```
Policy PDF
  ↓
PDF Text Extraction (PyMuPDF with Page Preservation)
  ↓
Gemini Policy Extraction / Rule Extraction
  ↓
Structured Policy JSON
  ↓
[PHASE 1 & 14] VALIDATION LAYER (PolicyValidator)
  ↓
[PHASE 3] RULE MATCHER (TreatmentRuleMatcher)
  ↓
[PHASE 4, 5, 6] COVERAGE / EXCLUSION / WAITING PERIOD CHECK (CoverageChecker)
  ↓
[PHASE 7, 8] DETERMINISTIC PYTHON MATH ENGINE (FinancialCalculationEngine)
  ↓
[PHASE 9, 10] STRUCTURED BREAKDOWN & CONFIDENCE SCORING
```

---

## Core Financial Rules Specification

Each rule follows the mandatory specification flow:
**INPUT → CONDITION → FORMULA / LOGIC → OUTPUT**

---

### Rule 1: Policy JSON Validation & Grounding Safety

*Status: Fully Implemented*

#### INPUT
- Raw extracted policy rules array from Gemini / Parser: `[{rule_type, rule_key, value, unit, page, clause, source_text}]`

#### CONDITION
- `page >= 1` (integer)
- `source_text` is non-empty string (length >= 3)
- Monetary values: `value >= 0`
- Co-payment values: `0.0 <= value <= 100.0`
- `treatment_min <= treatment_max` and costs >= 0

#### FORMULA / LOGIC
```
FOR each rule in raw_rules:
    IF page is missing OR source_text is empty:
        REJECT rule (do not invent missing grounding)
    IF value is non-numeric OR violates bounds:
        REJECT rule
IF no valid rules remain:
    RETURN status = "UNABLE_TO_CONFIDENTLY_ESTIMATE"
```

#### OUTPUT
- `ValidationResult(is_valid: bool, validated_rules: List, rejected_rules: List, status: str)`

---

### Rule 2: Treatment Exclusion Check

*Status: Fully Implemented*

#### INPUT
- Selected procedure name `P`
- Validated policy exclusion rules `E`

#### CONDITION
- Does any exclusion rule match procedure `P` or its medical keywords?

#### FORMULA / LOGIC
```
IF match_found(P, exclusion_rules):
    status = "EXCLUDED"
    is_eligible_for_calculation = False
    eligible_amount = 0
    insurance_contribution = 0
    patient_payable = treatment_cost (100%)
    citation = preserved exclusion clause evidence
```

#### OUTPUT
- Calculation halted. Structured exclusion report with clause citation and page number.

---

### Rule 3: Waiting Period Verification

*Status: Fully Implemented*

#### INPUT
- Selected procedure `P`
- Scenario parameters: `policy_tenure_months`, `is_ped`
- Validated policy waiting period rules `W`

#### CONDITION
- Pre-Existing Disease (PED) active AND tenure < policy PED waiting period (e.g., 36 months)
- OR Disease-specific waiting period for `P` active AND tenure < procedure waiting period (e.g., 24 months)
- OR Initial waiting period active (e.g. tenure < 30 days)

#### FORMULA / LOGIC
```
IF is_ped AND policy_tenure_months < ped_waiting_months:
    status = "WAITING_PERIOD"
    insurance_contribution = 0
    patient_payable = treatment_cost (100%)
ELSE IF proc_waiting_months AND policy_tenure_months < proc_waiting_months:
    status = "WAITING_PERIOD"
    insurance_contribution = 0
    patient_payable = treatment_cost (100%)
```

#### OUTPUT
- Calculation halted with `status = "WAITING_PERIOD"`, citation, and explanation.

---

### Rule 4: Procedure Sub-Limit Capping

*Status: Fully Implemented*

#### INPUT
- Benchmark treatment cost range: `[treatment_min, treatment_max]`
- Applicable procedure sub-limit: `applicable_sublimit` (e.g. INR 80,000)

#### CONDITION
- `applicable_sublimit` exists in validated policy rules AND `applicable_sublimit > 0`

#### FORMULA / LOGIC
```
eligible_min = min(treatment_min, applicable_sublimit)
eligible_max = min(treatment_max, applicable_sublimit)
```

#### OUTPUT
- Capped eligible expense range: `[eligible_min, eligible_max]`

---

### Rule 5: Hospital Room Rent Rule

*Status: Fully Implemented*

#### INPUT
- Selected room category: `Standard` vs `Deluxe` (upgraded)
- Validated daily room cap: `room_rent_cap_daily`
- Validated proportionate deduction clause: `room_proportionate_deduction_rate`

#### CONDITION
- Case A: `room_category == "Standard"` → Within allowance. No penalty.
- Case B: `room_category != "Standard"` AND policy defines explicit proportionate deduction rate `R`:
  - Retain `(1 - R)` ratio of eligible expenses.
- Case C: `room_category != "Standard"` AND policy defines daily cap but NO explicit proportionate deduction rate:
  - Do NOT hardcode arbitrary 30%!
  - Do NOT invent deductions.
  - Apply standard eligible amount, set confidence = `MEDIUM`, and append room ambiguity alert.

#### FORMULA / LOGIC
```
IF room_category == "Standard":
    penalty = 0.0
ELSE IF policy_defines_proportionate_deduction(R):
    eligible_min = eligible_min * (1.0 - R)
    eligible_max = eligible_max * (1.0 - R)
ELSE:
    flag_uncertainty(confidence="MEDIUM", reason="Room deduction percentage not defined in contract text")
```

#### OUTPUT
- Adjusted eligible amounts and room category applied rule annotation.

---

### Rule 6: Sum Insured Cap

*Status: Fully Implemented*

#### INPUT
- Eligible amount range: `[eligible_min, eligible_max]`
- Validated base policy sum insured: `sum_insured`

#### CONDITION
- `sum_insured > 0`

#### FORMULA / LOGIC
```
eligible_min = min(eligible_min, sum_insured)
eligible_max = min(eligible_max, sum_insured)
```

#### OUTPUT
- Policy-capped eligible amount range.

---

### Rule 7: Co-Payment Deduction

*Status: Fully Implemented*

#### INPUT
- Eligible amount: `[eligible_min, eligible_max]`
- Mandatory co-payment percent: `copay_percent` (0% to 100%)

#### CONDITION
- Validated co-pay rule present

#### FORMULA / LOGIC
```
copay_amount_min = eligible_min * (copay_percent / 100.0)
copay_amount_max = eligible_max * (copay_percent / 100.0)
```

#### OUTPUT
- Exact co-payment deductions: `[copay_amount_min, copay_amount_max]`

---

### Rule 8: Insurance Contribution & Patient Payable

*Status: Fully Implemented*

#### INPUT
- Base treatment cost: `[treatment_min, treatment_max]`
- Eligible amount: `[eligible_min, eligible_max]`
- Co-payment amount: `[copay_amount_min, copay_amount_max]`

#### CONDITION
- Validated calculation state

#### FORMULA / LOGIC
```
insurance_payment_min = max(0.0, eligible_min - copay_amount_min)
insurance_payment_max = max(0.0, eligible_max - copay_amount_max)

patient_payment_min = max(0.0, treatment_min - insurance_payment_min)
patient_payment_max = max(0.0, treatment_max - insurance_payment_max)
```

#### OUTPUT
- Net Insurance Contribution: `[insurance_payment_min, insurance_payment_max]`
- Patient Payable Out-of-Pocket Liability: `[patient_payment_min, patient_payment_max]`

---

### Rule 9: Confidence & Uncertainty Determination

*Status: Fully Implemented*

#### INPUT
- Presence of Sum Insured citation
- Cost benchmark availability
- Room rule ambiguity status
- Policy validation status

#### CONDITION & FORMULA
```
IF cost_found == False OR base_min_cost <= 0:
    confidence = "LOW"
    status = "UNABLE_TO_ESTIMATE"
ELSE IF sum_insured is None OR no citations:
    confidence = "LOW"
ELSE IF room_rule_ambiguity == True:
    confidence = "MEDIUM"
ELSE:
    confidence = "HIGH"
```

#### OUTPUT
- Structured confidence score (`HIGH` / `MEDIUM` / `LOW`) and transparent rationale.

---

### Rule 10: Treatment Cost Lookup Service

*Status: Fully Implemented*

#### INPUT
- Selected procedure name `P`
- Selected city `C`
- Database table `treatment_costs`

#### CONDITION
- Exact match on `LOWER(procedure_name) = LOWER(P)` and `LOWER(city) = LOWER(C)`

#### FORMULA / LOGIC
```
IF benchmark_row exists:
    RETURN {cost_min, cost_max, source, source_date, notes, data_type="synthetic"}
ELSE:
    RETURN None
    flag_uncertainty(status="UNABLE_TO_ESTIMATE", reason="Unable to confidently estimate because treatment-cost data is unavailable.")
```

#### OUTPUT
- Structured benchmark dictionary or uncertainty signal. Never invents hospital prices.

---

### Rule 11: Structured Coverage Checks

*Status: Fully Implemented*

#### INPUT
- Matched policy rules & scenario inputs

#### CONDITION & LOGIC
```
coverage_status = "covered" | "excluded" | "waiting_period" | "insufficient_information"
waiting_period_status = "satisfied" | "not_satisfied" | "not_applicable"
exclusion_status = "found" | "not_found"
sublimit_status = "applicable" | "not_applicable"
copay_status = "applicable" | "not_applicable"
room_rule_status = "applicable" | "not_applicable" | "uncertain"
```

#### OUTPUT
- Structured coverage check dictionary embedded in calculation result.

---

## Implementation Status Summary & Test Coverage (14 Step 17 Tests)

| Step / Test | Description | Status | Implementation Module |
| :--- | :--- | :--- | :--- |
| **TEST 1** | Treatment cost below sub-limit | **Passed** | `test_math_engine_comprehensive.py` |
| **TEST 2** | Treatment cost above sub-limit | **Passed** | `test_math_engine_comprehensive.py` |
| **TEST 3** | 10% co-payment calculation | **Passed** | `test_math_engine_comprehensive.py` |
| **TEST 4** | 0% co-payment (No co-pay) | **Passed** | `test_math_engine_comprehensive.py` |
| **TEST 5** | Missing sub-limit handling | **Passed** | `test_math_engine_comprehensive.py` |
| **TEST 6** | Missing treatment cost benchmark | **Passed** | `test_math_engine_comprehensive.py` |
| **TEST 7** | Invalid negative financial cost | **Passed** | `test_math_engine_comprehensive.py` |
| **TEST 8** | Explicit policy exclusion | **Passed** | `test_math_engine_comprehensive.py` |
| **TEST 9** | Waiting period not satisfied | **Passed** | `test_math_engine_comprehensive.py` |
| **TEST 10** | Waiting period satisfied | **Passed** | `test_math_engine_comprehensive.py` |
| **TEST 11** | Missing policy rule / evidence | **Passed** | `test_math_engine_comprehensive.py` |
| **TEST 12** | Room rule ambiguity (no 30% guess) | **Passed** | `test_math_engine_comprehensive.py` |
| **TEST 13** | Sum insured capping limitation | **Passed** | `test_math_engine_comprehensive.py` |
| **TEST 14** | Successful complete calculation | **Passed** | `test_math_engine_comprehensive.py` |

---

## Known Limitations & Prototype Assumptions

1. **Available Sum Insured vs Remaining Balance**: The prototype bounds maximum insurance reimbursement against the uploaded policy's initial Sum Insured. It does not track cumulative historical claims for the current policy year (no arbitrary balance assumption).
2. **Synthetic Benchmarks**: Healthcare pricing benchmarks are synthetic demonstrations and labeled with `data_type = "synthetic"`. They are not official hospital tariff quotations.
3. **Room Rent Proportionate Deduction**: Proportionate penalties are applied only when explicit percentage formulas appear in policy text. If a room upgrade exceeds the daily cap but the contract defines no penalty percentage, the engine flags `confidence = "MEDIUM"` and leaves the base eligible amount unpenalized.

---

## Future Extensions (Deferred from this Phase)

The following advanced capabilities are deliberately deferred to future phases:
1. **ICU Proportionate Tier Deductions**: Separate itemized bill splitting between medical consumables, doctor consultation fees, and ICU bed rates.
2. **Cumulative Bonus / No-Claim Bonus (NCB)**: Incrementing the base Sum Insured dynamically based on historical claim-free years.
3. **Restoration / Reinstatement Benefit**: Tracking exhaustion of sum insured across multiple unrelated hospitalizations in the same policy year.
4. **Zone-Based Co-Payment Differentials**: Differential co-payment rules when treatment is sought in Zone 1 (Metro) under a Zone 2 policy.
5. **Multi-Policy Claim Sharing (Coordination of Benefits)**: Apportioning claims across two separate insurance policies.
