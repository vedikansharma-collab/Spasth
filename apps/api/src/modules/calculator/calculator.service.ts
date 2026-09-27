import { prisma } from '../../common/database/prisma.js';
import { costRepository } from '../costs/cost.repository.js';
import { calculateTreatmentCost, ENGINE_VERSION } from '@policy-estimator/calculation-engine';
import {
  ExtractedPolicy,
  HospitalCostScenario,
  CalculationResponse,
  RoomCategory,
  TreatmentScenarioInput,
} from '@policy-estimator/types';
import { AppError, ErrorCodes } from '../../common/errors/app-error.js';
import { logger } from '../../common/logging/logger.js';

export class CalculatorService {
  async calculate(
    policyId: string,
    scenarioInput: TreatmentScenarioInput,
    isRecalculation: boolean = false
  ): Promise<CalculationResponse> {
    const startTime = Date.now();

    // 1. Fetch Policy Record
    const policyRecord = await prisma.policy.findUnique({
      where: { id: policyId },
      include: {
        rules: true,
        citations: true,
      },
    });

    if (!policyRecord) {
      throw new AppError(ErrorCodes.POLICY_NOT_FOUND, `Policy not found with ID: ${policyId}`, 404);
    }

    if (policyRecord.status !== 'READY') {
      throw new AppError(
        ErrorCodes.CALCULATION_ERROR,
        `Policy processing is not READY (current status: ${policyRecord.status}). Please wait until parsing is complete.`,
        400
      );
    }

    // 2. Reconstruct ExtractedPolicy from DB
    const extractedPolicy = this.reconstructExtractedPolicy(policyRecord);

    // 3. Fetch Procedure and Hospital Cost Scenario
    const procedure = await costRepository.getProcedureByCode(scenarioInput.procedureCode);
    if (!procedure) {
      throw new AppError(
        ErrorCodes.PROCEDURE_NOT_FOUND,
        `Procedure not found with code: ${scenarioInput.procedureCode}`,
        404
      );
    }

    let scenario = await costRepository.findScenario(
      scenarioInput.procedureCode,
      scenarioInput.roomCategory,
      scenarioInput.city
    );

    if (!scenario) {
      throw new AppError(
        ErrorCodes.COST_DATA_NOT_FOUND,
        `No benchmark cost data found for procedure ${scenarioInput.procedureCode} in room category ${scenarioInput.roomCategory}`,
        404
      );
    }

    // If custom stay duration or room rate was passed, adjust scenario deterministically
    if (scenarioInput.stayDays && scenarioInput.stayDays !== scenario.stayDays) {
      const stayDays = scenarioInput.stayDays;
      const roomCost = scenario.roomRate * stayDays;
      const totalBill = roomCost + scenario.proportionateCosts + scenario.nonProportionateCosts + (scenario.otherCosts || 0);
      scenario = {
        ...scenario,
        stayDays,
        totalBill,
      };
    }

    if (scenarioInput.customRoomRate && scenarioInput.customRoomRate > 0) {
      const roomRate = scenarioInput.customRoomRate;
      const roomCost = roomRate * scenario.stayDays;
      const totalBill = roomCost + scenario.proportionateCosts + scenario.nonProportionateCosts + (scenario.otherCosts || 0);
      scenario = {
        ...scenario,
        roomRate,
        totalBill,
      };
    }

    // 4. Run Deterministic Calculation Engine (Zero LLM, Pure Math)
    const calculationResult = calculateTreatmentCost(
      extractedPolicy,
      scenario,
      procedure,
      undefined,
      policyId
    );

    // 5. Persist Calculation Record in DB (async, do not block response)
    prisma.calculation
      .create({
        data: {
          id: calculationResult.calculationId,
          policyId,
          procedureId: procedure.id,
          scenarioJson: scenario as any,
          inputJson: scenarioInput as any,
          resultJson: calculationResult.result as any,
          calculationTraceJson: calculationResult.calculationTrace as any,
          engineVersion: ENGINE_VERSION,
        },
      })
      .catch((err) => {
        logger.error('Failed to persist calculation log', {
          event: 'calculation_log_error',
          calculationId: calculationResult.calculationId,
          error: err.message,
        });
      });

    logger.info(isRecalculation ? 'Scenario recalculation completed' : 'Initial calculation completed', {
      event: isRecalculation ? 'scenario_recalculated' : 'calculation_completed',
      policyId,
      calculationId: calculationResult.calculationId,
      durationMs: Date.now() - startTime,
      status: calculationResult.status,
      details: {
        procedure: scenarioInput.procedureCode,
        room: scenarioInput.roomCategory,
        oop: calculationResult.result.outOfPocket,
        insurerPay: calculationResult.result.finalInsurerPay,
      },
    });

    return calculationResult;
  }

  async getCalculationById(id: string) {
    const calc = await prisma.calculation.findUnique({
      where: { id },
      include: {
        policy: {
          include: {
            rules: true,
            citations: true,
          },
        },
        procedure: true,
      },
    });

    if (!calc) {
      throw new AppError(ErrorCodes.CALCULATION_ERROR, `Calculation not found with id: ${id}`, 404);
    }

    return calc;
  }

  private reconstructExtractedPolicy(policyRecord: any): ExtractedPolicy {
    // If parsedDocumentJson has extractedPolicy, use it directly
    const parsedJson = policyRecord.parsedDocumentJson as any;
    if (parsedJson?.extractedPolicy) {
      return parsedJson.extractedPolicy;
    }

    // Otherwise reconstruct from policyRule table
    const rules = policyRecord.rules || [];
    const sumInsuredRule = rules.find((r: any) => r.ruleType === 'SUM_INSURED');
    const roomRentRule = rules.find((r: any) => r.ruleType === 'ROOM_RENT_CAP');
    const copayRule = rules.find((r: any) => r.ruleType === 'COPAY');
    const subLimits = rules.filter((r: any) => r.ruleType === 'PROCEDURE_SUBLIMIT');
    const deductibles = rules.filter((r: any) => r.ruleType === 'DEDUCTIBLE');
    const exclusions = rules.filter((r: any) => r.ruleType === 'EXCLUSION');
    const waitingPeriods = rules.filter((r: any) => r.ruleType === 'WAITING_PERIOD');

    return {
      policyMetadata: {
        insurerName: policyRecord.insurerName,
        policyName: policyRecord.policyName,
      },
      sumInsured: {
        value: sumInsuredRule?.value ?? 500000,
        currency: sumInsuredRule?.unit || 'INR',
        source: sumInsuredRule?.sourceText
          ? {
              page: sumInsuredRule.sourcePage ?? 1,
              text: sumInsuredRule.sourceText,
              boundingBox: (sumInsuredRule.boundingBox as any) ?? null,
            }
          : null,
      },
      roomRentRule: {
        type: roomRentRule ? (roomRentRule.unit === '%' ? 'PERCENTAGE_OF_SUM_INSURED' : 'FIXED_AMOUNT_PER_DAY') : 'PERCENTAGE_OF_SUM_INSURED',
        percentage: roomRentRule?.unit === '%' ? roomRentRule.value : 1.0,
        fixedAmount: roomRentRule?.unit === 'INR' ? roomRentRule.value : null,
        perDay: true,
        source: roomRentRule?.sourceText
          ? {
              page: roomRentRule.sourcePage ?? 12,
              text: roomRentRule.sourceText,
              boundingBox: (roomRentRule.boundingBox as any) ?? null,
            }
          : null,
      },
      copay: {
        percentage: copayRule?.value ?? 10.0,
        applies: true,
        source: copayRule?.sourceText
          ? {
              page: copayRule.sourcePage ?? 18,
              text: copayRule.sourceText,
              boundingBox: (copayRule.boundingBox as any) ?? null,
            }
          : null,
      },
      subLimits: subLimits.map((sl: any) => ({
        procedureName: sl.ruleName.replace('Sub-limit: ', ''),
        amount: sl.value,
        applies: true,
        source: sl.sourceText
          ? {
              page: sl.sourcePage ?? 24,
              text: sl.sourceText,
              boundingBox: (sl.boundingBox as any) ?? null,
            }
          : null,
      })),
      deductibles: deductibles.map((d: any) => ({
        amount: d.value,
        applies: true,
        source: d.sourceText
          ? {
              page: d.sourcePage ?? 1,
              text: d.sourceText,
              boundingBox: (d.boundingBox as any) ?? null,
            }
          : null,
      })),
      exclusions: exclusions.map((e: any) => ({
        name: e.ruleName.replace('Exclusion: ', ''),
        isPermanent: true,
        source: e.sourceText
          ? {
              page: e.sourcePage ?? 1,
              text: e.sourceText,
              boundingBox: (e.boundingBox as any) ?? null,
            }
          : null,
      })),
      waitingPeriods: waitingPeriods.map((w: any) => ({
        condition: w.ruleName.replace('Waiting Period: ', ''),
        durationMonths: w.value,
        source: w.sourceText
          ? {
              page: w.sourcePage ?? 1,
              text: w.sourceText,
              boundingBox: (w.boundingBox as any) ?? null,
            }
          : null,
      })),
      unknownRules: [],
    };
  }
}

export const calculatorService = new CalculatorService();
