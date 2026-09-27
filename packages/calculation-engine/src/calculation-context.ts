import {
  ExtractedPolicy,
  HospitalCostScenario,
  Procedure,
  CalculationTraceStep,
  CitationReference,
  CalculationStatus,
  CategoricalConfidence,
  CostBreakdownItem,
} from '@policy-estimator/types';

export interface CalculationContext {
  policy: ExtractedPolicy;
  scenario: HospitalCostScenario;
  procedure?: Procedure | null;
  
  // Accumulated calculation state
  status: CalculationStatus;
  allowedRoomRent: number | null;
  roomFactor: number;
  coveredRoomRent: number;
  insurerProportionateShare: number;
  baseInsurerLiability: number;
  deductibleApplied: number;
  postDeductiblePay: number;
  copayPercentage: number;
  copayApplied: number;
  postCopayPay: number;
  subLimitApplied: number | null;
  finalInsurerPay: number;
  patientOutOfPocket: number;

  // Diagnostics and explanations
  trace: CalculationTraceStep[];
  citations: CitationReference[];
  breakdown: CostBreakdownItem[];
  warnings: string[];
  unknowns: string[];
  confidence: CategoricalConfidence;
}

export function createCalculationContext(
  policy: ExtractedPolicy,
  scenario: HospitalCostScenario,
  procedure?: Procedure | null
): CalculationContext {
  return {
    policy,
    scenario,
    procedure,
    status: 'CALCULATED',
    allowedRoomRent: null,
    roomFactor: 1,
    coveredRoomRent: 0,
    insurerProportionateShare: 0,
    baseInsurerLiability: 0,
    deductibleApplied: 0,
    postDeductiblePay: 0,
    copayPercentage: 0,
    copayApplied: 0,
    postCopayPay: 0,
    subLimitApplied: null,
    finalInsurerPay: 0,
    patientOutOfPocket: 0,
    trace: [],
    citations: [],
    breakdown: [],
    warnings: [],
    unknowns: [],
    confidence: {
      overall: 'HIGH',
      policyExtraction: 'HIGH',
      costMatching: 'HIGH',
      calculation: 'HIGH',
      reasons: [],
    },
  };
}
