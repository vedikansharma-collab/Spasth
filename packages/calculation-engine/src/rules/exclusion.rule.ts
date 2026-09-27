import { CalculationContext } from '../calculation-context.js';

export function checkExclusionsAndWaitingPeriods(ctx: CalculationContext): void {
  const { policy, scenario } = ctx;
  const procedureName = scenario.procedureName.toLowerCase();

  // Check permanent exclusions
  const matchingExclusion = policy.exclusions?.find(ex => {
    const exName = ex.name.toLowerCase();
    return procedureName.includes(exName) || exName.includes(procedureName);
  });

  if (matchingExclusion) {
    ctx.warnings.push(
      `NOTICE: Treatment "${scenario.procedureName}" appears in the policy exclusion list ("${matchingExclusion.name}"). Verify whether this specific condition is permanently excluded.`
    );
    if (matchingExclusion.source) {
      ctx.citations.push({
        ruleType: 'EXCLUSION',
        ruleName: `Exclusion: ${matchingExclusion.name}`,
        page: matchingExclusion.source.page,
        sourceText: matchingExclusion.source.text,
        boundingBox: matchingExclusion.source.boundingBox,
      });
    }
  }

  // Check waiting periods
  const matchingWaitingPeriod = policy.waitingPeriods?.find(wp => {
    const cond = wp.condition.toLowerCase();
    return procedureName.includes(cond) || cond.includes(procedureName) ||
      (procedureName.includes('hernia') && cond.includes('hernia')) ||
      (procedureName.includes('knee') && cond.includes('joint')) ||
      (procedureName.includes('cataract') && cond.includes('cataract')) ||
      (procedureName.includes('stone') && cond.includes('calculi'));
  });

  if (matchingWaitingPeriod) {
    ctx.warnings.push(
      `NOTICE: A waiting period of ${matchingWaitingPeriod.durationMonths ?? 'specified'} months applies to "${matchingWaitingPeriod.condition}". Verify that the policy tenure satisfies this duration.`
    );
    if (matchingWaitingPeriod.source) {
      ctx.citations.push({
        ruleType: 'WAITING_PERIOD',
        ruleName: `Waiting Period: ${matchingWaitingPeriod.condition}`,
        page: matchingWaitingPeriod.source.page,
        sourceText: matchingWaitingPeriod.source.text,
        boundingBox: matchingWaitingPeriod.source.boundingBox,
      });
    }
  }
}
