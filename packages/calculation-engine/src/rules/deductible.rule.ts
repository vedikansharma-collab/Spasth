import { CalculationContext } from '../calculation-context.js';

export function applyBaseLiabilityAndDeductible(ctx: CalculationContext): void {
  const { scenario, policy } = ctx;
  const nonProportionateCosts = scenario.nonProportionateCosts;
  const otherCosts = scenario.otherCosts ?? 0;

  // STEP 5 — BASE LIABILITY
  const baseInsurerLiability = 
    ctx.insurerProportionateShare +
    nonProportionateCosts +
    ctx.coveredRoomRent +
    otherCosts;

  ctx.baseInsurerLiability = baseInsurerLiability;

  ctx.trace.push({
    step: 'BASE_LIABILITY',
    title: 'Step 5: Base Insurer Liability Aggregation',
    formula: 'InsurerProportionateShare + NonProportionateCosts + CoveredRoomRent + OtherCosts',
    inputs: {
      insurerProportionateShare: ctx.insurerProportionateShare,
      nonProportionateCosts,
      coveredRoomRent: ctx.coveredRoomRent,
      otherCosts,
    },
    result: baseInsurerLiability,
    notes: 'Sum of all eligible medical expense shares before applying deductibles, co-pays, or procedure sub-limits.',
  });

  // Record non-proportionate & other costs in breakdown
  ctx.breakdown.push({
    name: 'Non-Proportionate Costs (Implants, Devices, Consumables)',
    category: 'NON_PROPORTIONATE',
    hospitalBilled: nonProportionateCosts,
    insurerCovered: nonProportionateCosts,
    patientLiability: 0,
    adjustmentReason: 'Fixed medical costs unaffected by room rent factor',
  });

  if (otherCosts > 0) {
    ctx.breakdown.push({
      name: 'Other Hospital Charges (Diagnostics, Medicines)',
      category: 'OTHER',
      hospitalBilled: otherCosts,
      insurerCovered: otherCosts,
      patientLiability: 0,
    });
  }

  // STEP 6 — DEDUCTIBLE
  const activeDeductible = policy.deductibles?.find(d => d.applies && (d.amount ?? 0) > 0);
  let deductibleAmount = 0;
  let postDeductible = baseInsurerLiability;

  if (activeDeductible && activeDeductible.amount) {
    deductibleAmount = activeDeductible.amount;
    postDeductible = Math.max(0, baseInsurerLiability - deductibleAmount);

    if (activeDeductible.source) {
      ctx.citations.push({
        ruleType: 'DEDUCTIBLE',
        ruleName: 'Policy Deductible',
        page: activeDeductible.source.page,
        sourceText: activeDeductible.source.text,
        boundingBox: activeDeductible.source.boundingBox,
      });
    }

    ctx.trace.push({
      step: 'DEDUCTIBLE',
      title: 'Step 6: Policy Deductible Deduction',
      formula: `max(0, BaseInsurerLiability (₹${baseInsurerLiability}) - Deductible (₹${deductibleAmount}))`,
      inputs: {
        baseInsurerLiability,
        deductibleAmount,
      },
      result: postDeductible,
      notes: `Patient bears first ₹${deductibleAmount.toLocaleString('en-IN')} as compulsory deductible.`,
    });
  } else {
    ctx.trace.push({
      step: 'DEDUCTIBLE',
      title: 'Step 6: Policy Deductible',
      formula: 'No deductible configured or applies. PostDeductible = BaseInsurerLiability',
      inputs: { baseInsurerLiability },
      result: postDeductible,
      notes: 'No deductible applies to this policy claim.',
    });
  }

  ctx.deductibleApplied = deductibleAmount;
  ctx.postDeductiblePay = postDeductible;
}
