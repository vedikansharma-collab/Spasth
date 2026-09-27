import {
  ExtractedPolicy,
  HospitalCostScenario,
  Procedure,
  CalculationResponse,
} from '@policy-estimator/types';
import { createCalculationContext } from './calculation-context.js';
import { applyRoomRentRule } from './rules/room-rent.rule.js';
import { applyBaseLiabilityAndDeductible } from './rules/deductible.rule.js';
import { applyCopayRule } from './rules/copay.rule.js';
import { applySublimitRule } from './rules/sublimit.rule.js';
import { checkExclusionsAndWaitingPeriods } from './rules/exclusion.rule.js';
import { finalizeCalculationResult, ENGINE_VERSION } from './calculation-result.js';

export { ENGINE_VERSION };

/**
 * Pure, deterministic treatment cost calculation engine.
 * 
 * Rules:
 * - Pure and side-effect free
 * - Independent of React
 * - Independent of LLM
 * - Independent of Database
 * - Reproducible and auditable
 */
export function calculateTreatmentCost(
  policy: ExtractedPolicy,
  hospitalScenario: HospitalCostScenario,
  procedure?: Procedure | null,
  calculationId?: string,
  policyId?: string
): CalculationResponse {
  // Validate basic inputs
  if (!policy) {
    throw new Error('Policy data is required for calculation');
  }
  if (!hospitalScenario) {
    throw new Error('Hospital cost scenario is required for calculation');
  }

  // Initialize context
  const ctx = createCalculationContext(policy, hospitalScenario, procedure);

  // STEP 1-4: Room Rent, Room Factor, Proportionate Costs, Covered Room Rent
  applyRoomRentRule(ctx);

  // If room rent was unknown or incomplete, we stop calculation deterministically
  if (ctx.status === 'INCOMPLETE') {
    return finalizeCalculationResult(ctx, calculationId, policyId);
  }

  // STEP 5-6: Base Liability and Deductible
  applyBaseLiabilityAndDeductible(ctx);

  // STEP 7: Co-pay
  applyCopayRule(ctx);

  // STEP 8: Procedure Sub-Limit
  applySublimitRule(ctx);

  // Advisory: Exclusions and Waiting Periods
  checkExclusionsAndWaitingPeriods(ctx);

  // STEP 9: Final OOP & Result
  return finalizeCalculationResult(ctx, calculationId, policyId);
}
