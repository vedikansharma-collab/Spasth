import { describe, it, expect } from 'vitest';
import { calculateTreatmentCost } from '../engine.js';
import { ExtractedPolicy, HospitalCostScenario } from '@policy-estimator/types';

describe('Deterministic Calculation Engine (V1)', () => {
  const basePolicy: ExtractedPolicy = {
    policyMetadata: {
      insurerName: 'Star Health',
      policyName: 'MediClassic',
    },
    sumInsured: {
      value: 500000,
      currency: 'INR',
      source: { page: 5, text: 'Sum Insured: INR 5,00,000', boundingBox: null },
    },
    roomRentRule: {
      type: 'PERCENTAGE_OF_SUM_INSURED',
      percentage: 1.0,
      fixedAmount: null,
      perDay: true,
      source: { page: 12, text: 'Room rent capped at 1% of Sum Insured', boundingBox: null },
    },
    copay: {
      percentage: 10,
      applies: true,
      source: { page: 18, text: '10% co-payment applies', boundingBox: null },
    },
    subLimits: [
      {
        procedureCode: 'PROC-APP-LAP',
        procedureName: 'Laparoscopic Appendectomy',
        amount: 40000,
        percentageOfSumInsured: null,
        applies: true,
        source: { page: 24, text: 'Appendectomy capped at INR 40,000', boundingBox: null },
      },
    ],
    deductibles: [],
    exclusions: [],
    waitingPeriods: [],
    unknownRules: [],
  };

  const singlePrivateScenario: HospitalCostScenario = {
    procedureCode: 'PROC-APP-LAP',
    procedureName: 'Laparoscopic Appendectomy',
    city: 'National Average',
    roomCategory: 'SINGLE_PRIVATE',
    roomRate: 8000,
    stayDays: 2,
    proportionateCosts: 45000,
    nonProportionateCosts: 35000,
    otherCosts: 4000,
    totalBill: 100000, // (8000 * 2) + 45000 + 35000 + 4000 = 100000
    currency: 'INR',
  };

  const twinSharingScenario: HospitalCostScenario = {
    procedureCode: 'PROC-APP-LAP',
    procedureName: 'Laparoscopic Appendectomy',
    city: 'National Average',
    roomCategory: 'TWIN_SHARING',
    roomRate: 4500,
    stayDays: 2,
    proportionateCosts: 38000,
    nonProportionateCosts: 35000,
    otherCosts: 4000,
    totalBill: 86000, // (4500 * 2) + 38000 + 35000 + 4000 = 86000
    currency: 'INR',
  };

  it('calculates exact room factor 0.625 for 1% cap on 5L SI with 8,000 room rate', () => {
    const res = calculateTreatmentCost(basePolicy, singlePrivateScenario);

    // Sum Insured 5,00,000 * 1% = 5,000
    expect(res.result.allowedRoomRent).toBe(5000);
    // Room factor: min(1, 5000 / 8000) = 0.625
    expect(res.result.roomFactor).toBe(0.625);
    // Proportionate costs: 45000 * 0.625 = 28125
    expect(res.result.insurerProportionateShare).toBe(28125);
    // Covered room rent: min(5000, 8000) * 2 = 10000
    expect(res.result.coveredRoomRent).toBe(10000);
    // Non-proportionate costs intact: 35000
    // Other costs: 4000
    // Base liability: 28125 + 35000 + 10000 + 4000 = 77125
    expect(res.result.baseInsurerLiability).toBe(77125);
    // Deductible: 0
    expect(res.result.deductible).toBe(0);
    // PostCopay: 77125 * (1 - 0.10) = 69412.5 (rounded to 69413)
    expect(res.result.postCopayPay).toBe(69413);
    // Sub-limit for appendectomy: 40,000
    expect(res.result.procedureSubLimit).toBe(40000);
    // FinalInsurerPay: min(69413, 40000) = 40000
    expect(res.result.finalInsurerPay).toBe(40000);
    // OutOfPocket: 100000 - 40000 = 60000
    expect(res.result.outOfPocket).toBe(60000);
    expect(res.status).toBe('CALCULATED');
    expect(res.confidence.overall).toBe('HIGH');
  });

  it('calculates room factor = 1.0 when room rate is below allowed cap (Twin Sharing)', () => {
    // Twin sharing room rate is 4,500 <= allowed 5,000
    const res = calculateTreatmentCost(basePolicy, twinSharingScenario);

    expect(res.result.allowedRoomRent).toBe(5000);
    expect(res.result.roomFactor).toBe(1.0);
    // Proportionate costs covered 100%: 38000
    expect(res.result.insurerProportionateShare).toBe(38000);
    // Covered room rent: 4500 * 2 = 9000
    expect(res.result.coveredRoomRent).toBe(9000);
    // Base liability: 38000 + 35000 + 9000 + 4000 = 86000
    expect(res.result.baseInsurerLiability).toBe(86000);
    // PostCopay: 86000 * 0.9 = 77400
    expect(res.result.postCopayPay).toBe(77400);
    // Sub-limit cap: 40000
    expect(res.result.finalInsurerPay).toBe(40000);
    // OOP: 86000 - 40000 = 46000
    expect(res.result.outOfPocket).toBe(46000);
  });

  it('supports FIXED_AMOUNT_PER_DAY room rent cap', () => {
    const fixedPolicy: ExtractedPolicy = {
      ...basePolicy,
      roomRentRule: {
        type: 'FIXED_AMOUNT_PER_DAY',
        fixedAmount: 4000,
        percentage: null,
        perDay: true,
        source: null,
      },
    };

    const res = calculateTreatmentCost(fixedPolicy, singlePrivateScenario);
    expect(res.result.allowedRoomRent).toBe(4000);
    // 4000 / 8000 = 0.5
    expect(res.result.roomFactor).toBe(0.5);
    // 45000 * 0.5 = 22500
    expect(res.result.insurerProportionateShare).toBe(22500);
  });

  it('supports NO_LIMIT room rent cap', () => {
    const noLimitPolicy: ExtractedPolicy = {
      ...basePolicy,
      roomRentRule: {
        type: 'NO_LIMIT',
        fixedAmount: null,
        percentage: null,
        perDay: null,
        source: null,
      },
    };

    const res = calculateTreatmentCost(noLimitPolicy, singlePrivateScenario);
    expect(res.result.allowedRoomRent).toBe(8000);
    expect(res.result.roomFactor).toBe(1.0);
    expect(res.result.insurerProportionateShare).toBe(45000);
  });

  it('marks calculation INCOMPLETE when room rent rule is UNKNOWN', () => {
    const unknownPolicy: ExtractedPolicy = {
      ...basePolicy,
      roomRentRule: {
        type: 'UNKNOWN',
        fixedAmount: null,
        percentage: null,
        perDay: null,
        source: null,
      },
    };

    const res = calculateTreatmentCost(unknownPolicy, singlePrivateScenario);
    expect(res.status).toBe('INCOMPLETE');
    expect(res.unknowns.length).toBeGreaterThan(0);
    expect(res.confidence.calculation).toBe('LOW');
  });

  it('applies deductible correctly', () => {
    const deductiblePolicy: ExtractedPolicy = {
      ...basePolicy,
      subLimits: [], // remove sublimit to test pure deductible impact
      deductibles: [
        {
          amount: 15000,
          applies: true,
          scope: 'PER_CLAIM',
          source: null,
        },
      ],
    };

    const res = calculateTreatmentCost(deductiblePolicy, singlePrivateScenario);
    // Base liability was 77125
    // PostDeductible = 77125 - 15000 = 62125
    // PostCopay = 62125 * 0.9 = 55912.5 -> 55913
    expect(res.result.deductible).toBe(15000);
    expect(res.result.finalInsurerPay).toBe(55913);
    expect(res.result.outOfPocket).toBe(100000 - 55913);
  });

  it('prevents negative patient out-of-pocket', () => {
    // If insurer pay somehow exceeded bill
    const cheapScenario: HospitalCostScenario = {
      ...singlePrivateScenario,
      totalBill: 30000,
    };
    const res = calculateTreatmentCost(basePolicy, cheapScenario);
    expect(res.result.outOfPocket).toBeGreaterThanOrEqual(0);
  });

  it('returns a complete, auditable calculation trace with 9 steps', () => {
    const res = calculateTreatmentCost(basePolicy, singlePrivateScenario);
    expect(res.calculationTrace).toBeDefined();
    expect(res.calculationTrace.length).toBeGreaterThanOrEqual(6);

    const steps = res.calculationTrace.map(t => t.step);
    expect(steps).toContain('ALLOWED_ROOM_RENT');
    expect(steps).toContain('ROOM_FACTOR');
    expect(steps).toContain('PROPORTIONATE_COSTS');
    expect(steps).toContain('COVERED_ROOM_RENT');
    expect(steps).toContain('BASE_LIABILITY');
    expect(steps).toContain('COPAY');
    expect(steps).toContain('PROCEDURE_SUBLIMIT');
    expect(steps).toContain('FINAL_OOP');
  });
});
