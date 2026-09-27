import { CalculationContext } from '../calculation-context.js';

export function applySublimitRule(ctx: CalculationContext): void {
  const { policy, scenario, postCopayPay } = ctx;
  const procedureCode = scenario.procedureCode;
  const procedureName = scenario.procedureName.toLowerCase();

  // Find matching sub-limit by code or fuzzy name match
  const matchingSublimit = policy.subLimits?.find(sl => {
    if (!sl.applies) return false;
    if (sl.procedureCode && sl.procedureCode.toUpperCase() === procedureCode.toUpperCase()) {
      return true;
    }
    const slName = sl.procedureName.toLowerCase();
    return procedureName.includes(slName) || slName.includes(procedureName) ||
      (slName.includes('append') && procedureName.includes('append')) ||
      (slName.includes('cataract') && procedureName.includes('cataract')) ||
      (slName.includes('knee') && procedureName.includes('knee')) ||
      (slName.includes('hernia') && procedureName.includes('hernia')) ||
      (slName.includes('angio') && procedureName.includes('angio'));
  });

  let subLimitCap: number | null = null;
  let finalInsurerPay = postCopayPay;

  if (matchingSublimit) {
    if (matchingSublimit.amount && matchingSublimit.amount > 0) {
      subLimitCap = matchingSublimit.amount;
    } else if (matchingSublimit.percentageOfSumInsured && policy.sumInsured?.value) {
      subLimitCap = Math.round((policy.sumInsured.value * matchingSublimit.percentageOfSumInsured) / 100);
    }

    if (matchingSublimit.source) {
      ctx.citations.push({
        ruleType: 'PROCEDURE_SUBLIMIT',
        ruleName: `Sub-limit for ${matchingSublimit.procedureName}`,
        page: matchingSublimit.source.page,
        sourceText: matchingSublimit.source.text,
        boundingBox: matchingSublimit.source.boundingBox,
      });
    }
  }

  if (subLimitCap !== null) {
    finalInsurerPay = Math.min(postCopayPay, subLimitCap);
    const subLimitExceeded = postCopayPay > subLimitCap;

    if (subLimitExceeded) {
      ctx.warnings.push(
        `Procedure specific sub-limit of ₹${subLimitCap.toLocaleString('en-IN')} was reached for ${scenario.procedureName}. Insurer payout capped from ₹${postCopayPay.toLocaleString('en-IN')} to ₹${subLimitCap.toLocaleString('en-IN')}.`
      );
    }

    ctx.trace.push({
      step: 'PROCEDURE_SUBLIMIT',
      title: 'Step 8: Procedure Sub-limit Cap',
      formula: `min(PostCopay (₹${postCopayPay}), ProcedureSubLimit (₹${subLimitCap})) = ₹${finalInsurerPay}`,
      inputs: {
        postCopayPay,
        subLimitCap,
        procedureName: scenario.procedureName,
      },
      result: finalInsurerPay,
      notes: subLimitExceeded
        ? `Policy caps total payout for this treatment at ₹${subLimitCap.toLocaleString('en-IN')}.`
        : `Claim amount is within the ₹${subLimitCap.toLocaleString('en-IN')} procedure limit.`,
    });
  } else {
    ctx.trace.push({
      step: 'PROCEDURE_SUBLIMIT',
      title: 'Step 8: Procedure Sub-limit Check',
      formula: 'No specific procedure sub-limit applies. FinalInsurerPay = PostCopay',
      inputs: { postCopayPay, procedureName: scenario.procedureName },
      result: finalInsurerPay,
      notes: `No special capping clause applies to ${scenario.procedureName}.`,
    });
  }

  ctx.subLimitApplied = subLimitCap;
  ctx.finalInsurerPay = finalInsurerPay;
}
