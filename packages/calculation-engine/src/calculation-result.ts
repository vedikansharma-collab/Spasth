import {
  CalculationResponse,
  CalculationResult,
  CategoricalConfidence,
} from '@policy-estimator/types';
import { CalculationContext } from './calculation-context.js';

export const ENGINE_VERSION = '1.0.0';

export function finalizeCalculationResult(
  ctx: CalculationContext,
  calculationId: string = 'calc-' + Math.random().toString(36).substring(2, 9),
  policyId: string = 'policy-sample'
): CalculationResponse {
  const { scenario } = ctx;
  const totalHospitalBill = scenario.totalBill;

  if (ctx.status === 'CALCULATED') {
    // STEP 9 — FINAL OOP
    // OutOfPocket = max(0, TotalHospitalBill - FinalInsurerPay)
    const outOfPocket = Math.max(0, totalHospitalBill - ctx.finalInsurerPay);
    ctx.patientOutOfPocket = outOfPocket;

    ctx.trace.push({
      step: 'FINAL_OOP',
      title: 'Step 9: Final Patient Out-of-Pocket Expense',
      formula: `max(0, TotalHospitalBill (₹${totalHospitalBill}) - FinalInsurerPay (₹${ctx.finalInsurerPay})) = ₹${outOfPocket}`,
      inputs: {
        totalHospitalBill,
        finalInsurerPay: ctx.finalInsurerPay,
      },
      result: outOfPocket,
      notes: `Patient is estimated to pay ₹${outOfPocket.toLocaleString('en-IN')}; insurer covers ₹${ctx.finalInsurerPay.toLocaleString('en-IN')}.`,
    });

    // Add final summary adjustment breakdown row if needed
    const totalCoveredBreakdown = ctx.breakdown.reduce((sum, b) => sum + b.insurerCovered, 0);
    const postCopayDelta = totalCoveredBreakdown - ctx.finalInsurerPay;
    if (postCopayDelta > 0) {
      ctx.breakdown.push({
        name: 'Co-pay and/or Sub-limit Cap Deduction',
        category: 'ADJUSTMENT',
        hospitalBilled: 0,
        insurerCovered: -postCopayDelta,
        patientLiability: postCopayDelta,
        adjustmentReason: 'Deducted according to co-payment or disease sub-limit terms',
      });
    }
  } else {
    // Incomplete or invalid status
    ctx.patientOutOfPocket = totalHospitalBill;
    ctx.finalInsurerPay = 0;
  }

  // Assess categorical confidence deterministically
  const confidence = determineConfidence(ctx);

  const resultObj: CalculationResult = {
    allowedRoomRent: ctx.allowedRoomRent ?? 0,
    roomFactor: ctx.roomFactor,
    insurerProportionateShare: ctx.insurerProportionateShare,
    coveredRoomRent: ctx.coveredRoomRent,
    baseInsurerLiability: ctx.baseInsurerLiability,
    deductible: ctx.deductibleApplied,
    copayPercentage: ctx.copayPercentage,
    copayAmount: ctx.copayApplied,
    postCopayPay: ctx.postCopayPay,
    procedureSubLimit: ctx.subLimitApplied,
    finalInsurerPay: ctx.finalInsurerPay,
    outOfPocket: ctx.patientOutOfPocket,
  };

  const roomCost = scenario.roomRate * scenario.stayDays;

  return {
    calculationId,
    policyId,
    status: ctx.status,
    engineVersion: ENGINE_VERSION,
    calculatedAt: new Date().toISOString(),
    scenario: {
      procedureCode: scenario.procedureCode,
      procedureName: scenario.procedureName,
      roomCategory: scenario.roomCategory,
      stayDays: scenario.stayDays,
      city: scenario.city,
    },
    hospital: {
      totalBill: scenario.totalBill,
      roomRate: scenario.roomRate,
      stayDays: scenario.stayDays,
      roomCost,
      proportionateCosts: scenario.proportionateCosts,
      nonProportionateCosts: scenario.nonProportionateCosts,
      otherCosts: scenario.otherCosts,
    },
    result: resultObj,
    breakdown: ctx.breakdown,
    calculationTrace: ctx.trace,
    citations: ctx.citations,
    confidence,
    warnings: ctx.warnings,
    unknowns: ctx.unknowns,
  };
}

function determineConfidence(ctx: CalculationContext): CategoricalConfidence {
  let policyExtraction: 'HIGH' | 'MEDIUM' | 'LOW' = 'HIGH';
  let costMatching: 'HIGH' | 'MEDIUM' | 'LOW' = 'HIGH';
  let calculation: 'HIGH' | 'MEDIUM' | 'LOW' = 'HIGH';
  const reasons: string[] = [];

  // Check extraction confidence
  if (!ctx.policy.roomRentRule || ctx.policy.roomRentRule.type === 'UNKNOWN') {
    policyExtraction = 'LOW';
    reasons.push('Room rent rule could not be extracted with confidence.');
  } else if (!ctx.policy.roomRentRule.source) {
    policyExtraction = 'MEDIUM';
    reasons.push('Room rent rule lacks precise page citation.');
  }

  if (!ctx.policy.sumInsured?.value) {
    if (ctx.policy.roomRentRule?.type === 'PERCENTAGE_OF_SUM_INSURED') {
      policyExtraction = 'LOW';
      reasons.push('Sum Insured is unknown but required for percentage room rent calculation.');
    }
  }

  // Cost matching
  if (!ctx.scenario.totalBill || ctx.scenario.totalBill <= 0) {
    costMatching = 'LOW';
    reasons.push('Hospital bill scenario contains invalid or missing pricing.');
  }

  // Calculation
  if (ctx.status === 'INCOMPLETE') {
    calculation = 'LOW';
    reasons.push('Calculation is incomplete due to missing required policy terms.');
  } else if (ctx.unknowns.length > 0) {
    calculation = 'MEDIUM';
    reasons.push('Some optional clauses could not be verified.');
  }

  // Overall confidence is minimum of the three
  let overall: 'HIGH' | 'MEDIUM' | 'LOW' = 'HIGH';
  if (policyExtraction === 'LOW' || costMatching === 'LOW' || calculation === 'LOW') {
    overall = 'LOW';
  } else if (policyExtraction === 'MEDIUM' || costMatching === 'MEDIUM' || calculation === 'MEDIUM') {
    overall = 'MEDIUM';
  }

  return {
    overall,
    policyExtraction,
    costMatching,
    calculation,
    reasons,
  };
}
