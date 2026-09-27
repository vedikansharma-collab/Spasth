import { CalculationContext } from '../calculation-context.js';

export function applyRoomRentRule(ctx: CalculationContext): void {
  const { policy, scenario } = ctx;
  const roomRule = policy.roomRentRule;
  const sumInsured = policy.sumInsured?.value;
  const actualRoomRate = scenario.roomRate;
  const stayDays = scenario.stayDays;

  // Add citation if available
  if (roomRule?.source) {
    ctx.citations.push({
      ruleType: 'ROOM_RENT_CAP',
      ruleName: 'Room Rent Restriction',
      page: roomRule.source.page,
      sourceText: roomRule.source.text,
      boundingBox: roomRule.source.boundingBox,
    });
  }

  // STEP 1 — ALLOWED ROOM RENT
  let allowedRoomRent: number | null = null;
  let formulaDesc = '';
  const step1Inputs: Record<string, any> = {
    ruleType: roomRule?.type,
    actualRoomRate,
    stayDays,
  };

  switch (roomRule?.type) {
    case 'PERCENTAGE_OF_SUM_INSURED': {
      const percentage = roomRule.percentage ?? 0;
      step1Inputs.sumInsured = sumInsured;
      step1Inputs.percentage = percentage;

      if (!sumInsured || sumInsured <= 0) {
        ctx.status = 'INCOMPLETE';
        ctx.unknowns.push('Sum Insured value is missing or invalid for percentage-based room rent calculation.');
        ctx.warnings.push('Policy defines room rent as percentage of Sum Insured, but Sum Insured is unknown.');
        ctx.confidence.calculation = 'LOW';
        ctx.confidence.reasons.push('Cannot calculate allowed room rent without Sum Insured.');
        return;
      }

      allowedRoomRent = Math.round((sumInsured * percentage) / 100);
      formulaDesc = `SumInsured (${sumInsured}) × Percentage (${percentage}%) / 100 = ₹${allowedRoomRent}/day`;
      break;
    }

    case 'FIXED_AMOUNT_PER_DAY': {
      const fixedAmount = roomRule.fixedAmount ?? 0;
      step1Inputs.fixedAmount = fixedAmount;

      if (fixedAmount <= 0) {
        ctx.status = 'INCOMPLETE';
        ctx.unknowns.push('Fixed daily room rent amount is missing or invalid.');
        ctx.warnings.push('Room rent rule is FIXED_AMOUNT_PER_DAY but no amount was found.');
        ctx.confidence.calculation = 'LOW';
        return;
      }

      allowedRoomRent = fixedAmount;
      formulaDesc = `Fixed Amount per Day = ₹${allowedRoomRent}/day`;
      break;
    }

    case 'FIXED_AMOUNT_PER_HOSPITALIZATION': {
      const fixedAmount = roomRule.fixedAmount ?? 0;
      step1Inputs.fixedAmount = fixedAmount;
      allowedRoomRent = stayDays > 0 ? Math.round(fixedAmount / stayDays) : fixedAmount;
      formulaDesc = `Fixed Amount (₹${fixedAmount}) / Stay Duration (${stayDays} days) = ₹${allowedRoomRent}/day`;
      break;
    }

    case 'NO_LIMIT': {
      allowedRoomRent = actualRoomRate;
      formulaDesc = `No limit applied. Allowed room rent equals actual hospital room rate (₹${actualRoomRate}/day)`;
      break;
    }

    case 'UNKNOWN':
    default: {
      ctx.status = 'INCOMPLETE';
      ctx.unknowns.push('Room rent restriction could not be determined from the uploaded policy document.');
      ctx.warnings.push('Room rent rule is UNKNOWN. Calculation cannot proceed deterministically without guessing.');
      ctx.confidence.calculation = 'LOW';
      ctx.confidence.policyExtraction = 'LOW';
      ctx.confidence.reasons.push('Room rent cap is unspecified or ambiguous in policy text.');

      ctx.trace.push({
        step: 'ALLOWED_ROOM_RENT',
        title: 'Step 1: Allowed Room Rent',
        formula: 'Rule type is UNKNOWN - calculation paused',
        inputs: step1Inputs,
        result: 'UNKNOWN',
        notes: 'Cannot determine allowed room rent without guessing. Returning INCOMPLETE status as per strict policy.',
      });
      return;
    }
  }

  ctx.allowedRoomRent = allowedRoomRent;

  ctx.trace.push({
    step: 'ALLOWED_ROOM_RENT',
    title: 'Step 1: Allowed Room Rent Determination',
    formula: formulaDesc,
    inputs: step1Inputs,
    result: allowedRoomRent,
    notes: `Policy allows up to ₹${allowedRoomRent.toLocaleString('en-IN')}/day for room accommodation.`,
  });

  // STEP 2 — ROOM FACTOR
  let roomFactor = 1;
  let factorFormula = '';

  if (actualRoomRate > allowedRoomRent && allowedRoomRent > 0) {
    // Room cap was breached
    roomFactor = Math.min(1, Math.round((allowedRoomRent / actualRoomRate) * 10000) / 10000);
    factorFormula = `min(1, AllowedRoomRent (${allowedRoomRent}) / ActualRoomRate (${actualRoomRate}))`;
    ctx.warnings.push(
      `Selected room rate (₹${actualRoomRate.toLocaleString('en-IN')}/day) exceeds policy allowed limit of ₹${allowedRoomRent.toLocaleString('en-IN')}/day. Room factor penalty of ${roomFactor} applies to proportionate hospital costs.`
    );
  } else {
    roomFactor = 1;
    factorFormula = actualRoomRate <= allowedRoomRent
      ? `Room rate ₹${actualRoomRate}/day is within allowed ₹${allowedRoomRent}/day. Room factor = 1.0`
      : 'No room restriction applies. Room factor = 1.0';
  }

  ctx.roomFactor = roomFactor;

  ctx.trace.push({
    step: 'ROOM_FACTOR',
    title: 'Step 2: Room Factor Calculation',
    formula: factorFormula,
    inputs: {
      allowedRoomRent,
      actualRoomRate,
    },
    result: roomFactor,
    notes: roomFactor < 1
      ? `Proportionate deduction factor is ${roomFactor} (or ${(roomFactor * 100).toFixed(2)}%).`
      : 'No proportionate penalty applied to doctor fees, surgery, or nursing.',
  });

  // STEP 3 — PROPORTIONATE COSTS
  const proportionateCosts = scenario.proportionateCosts;
  const insurerProportionateShare = Math.round(proportionateCosts * roomFactor);
  ctx.insurerProportionateShare = insurerProportionateShare;

  ctx.trace.push({
    step: 'PROPORTIONATE_COSTS',
    title: 'Step 3: Proportionate Costs Adjustment',
    formula: `Hospital Proportionate Costs (₹${proportionateCosts}) × Room Factor (${roomFactor})`,
    inputs: {
      hospitalProportionateCosts: proportionateCosts,
      roomFactor,
    },
    result: insurerProportionateShare,
    notes: roomFactor < 1
      ? `Insurer pays ₹${insurerProportionateShare.toLocaleString('en-IN')} of ₹${proportionateCosts.toLocaleString('en-IN')} proportionate charges. Patient pays remainder ₹${(proportionateCosts - insurerProportionateShare).toLocaleString('en-IN')}.`
      : `Full proportionate charges of ₹${proportionateCosts.toLocaleString('en-IN')} covered before co-pay/sub-limits.`,
  });

  // STEP 4 — COVERED ROOM RENT
  const totalBilledRoomCost = actualRoomRate * stayDays;
  const coveredDailyRate = Math.min(allowedRoomRent, actualRoomRate);
  const coveredRoomRent = coveredDailyRate * stayDays;
  ctx.coveredRoomRent = coveredRoomRent;

  ctx.trace.push({
    step: 'COVERED_ROOM_RENT',
    title: 'Step 4: Covered Room Rent Calculation',
    formula: `min(AllowedRoomRent (${allowedRoomRent}), ActualRoomRate (${actualRoomRate})) × StayDuration (${stayDays} days)`,
    inputs: {
      allowedRoomRent,
      actualRoomRate,
      stayDays,
      totalBilledRoomCost,
    },
    result: coveredRoomRent,
    notes: `Out of billed room charges ₹${totalBilledRoomCost.toLocaleString('en-IN')}, policy covers ₹${coveredRoomRent.toLocaleString('en-IN')}.`,
  });

  // Record breakdown items
  ctx.breakdown.push({
    name: `Room Rent (${scenario.roomCategory.replace('_', ' ')} - ${stayDays} days @ ₹${actualRoomRate}/day)`,
    category: 'ROOM',
    hospitalBilled: totalBilledRoomCost,
    insurerCovered: coveredRoomRent,
    patientLiability: totalBilledRoomCost - coveredRoomRent,
    adjustmentReason: roomFactor < 1 ? `Capped at ₹${allowedRoomRent}/day by policy` : undefined,
  });

  ctx.breakdown.push({
    name: 'Proportionate Costs (Surgeon, Anaesthetist, Nursing, OT)',
    category: 'PROPORTIONATE',
    hospitalBilled: proportionateCosts,
    insurerCovered: insurerProportionateShare,
    patientLiability: proportionateCosts - insurerProportionateShare,
    adjustmentReason: roomFactor < 1 ? `Reduced by Room Factor (${(roomFactor * 100).toFixed(1)}%)` : undefined,
  });
}
