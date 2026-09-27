import { CalculationContext } from '../calculation-context.js';

export function applyCopayRule(ctx: CalculationContext): void {
  const { policy, postDeductiblePay } = ctx;
  const copayRule = policy.copay;

  let copayPercentage = 0;
  let copayAmount = 0;
  let postCopay = postDeductiblePay;

  if (copayRule && copayRule.applies && (copayRule.percentage ?? 0) > 0) {
    copayPercentage = copayRule.percentage!;
    copayAmount = Math.round((postDeductiblePay * copayPercentage) / 100);
    postCopay = Math.max(0, postDeductiblePay - copayAmount);

    if (copayRule.source) {
      ctx.citations.push({
        ruleType: 'COPAY',
        ruleName: 'Co-Payment Clause',
        page: copayRule.source.page,
        sourceText: copayRule.source.text,
        boundingBox: copayRule.source.boundingBox,
      });
    }

    ctx.trace.push({
      step: 'COPAY',
      title: 'Step 7: Co-payment Application',
      formula: `PostDeductible (₹${postDeductiblePay}) × (1 - ${copayPercentage}% / 100) = ₹${postCopay}`,
      inputs: {
        postDeductiblePay,
        copayPercentage,
        copayAmount,
      },
      result: postCopay,
      notes: `Policy mandates a ${copayPercentage}% co-pay. Insurer covers ₹${postCopay.toLocaleString('en-IN')}; patient co-pays ₹${copayAmount.toLocaleString('en-IN')}.`,
    });
  } else {
    ctx.trace.push({
      step: 'COPAY',
      title: 'Step 7: Co-payment Check',
      formula: 'No co-pay applies or percentage is 0%. PostCopay = PostDeductible',
      inputs: { postDeductiblePay },
      result: postCopay,
      notes: 'No co-payment required under this policy clause.',
    });
  }

  ctx.copayPercentage = copayPercentage;
  ctx.copayApplied = copayAmount;
  ctx.postCopayPay = postCopay;
}
