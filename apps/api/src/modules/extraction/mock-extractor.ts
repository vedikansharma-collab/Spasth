import fs from 'fs';
import path from 'path';
import { PolicyExtractionProvider, ExtractedPolicy, ParsedDocument } from '@policy-estimator/types';
import { PolicyExtractionSchema } from '@policy-estimator/schemas';
import { logger } from '../../common/logging/logger.js';
import { AppError, ErrorCodes } from '../../common/errors/app-error.js';

export class MockPolicyExtractor implements PolicyExtractionProvider {
  async extract(document: ParsedDocument): Promise<ExtractedPolicy> {
    logger.info('Extracting policy rules using MockPolicyExtractor', {
      event: 'policy_extraction_started',
    });

    const samplePath = path.resolve(process.cwd(), '../../data/sample-policy.json');
    const localSamplePath = path.resolve(process.cwd(), 'data/sample-policy.json');

    let rawJson: string;
    if (fs.existsSync(samplePath)) {
      rawJson = fs.readFileSync(samplePath, 'utf-8');
    } else if (fs.existsSync(localSamplePath)) {
      rawJson = fs.readFileSync(localSamplePath, 'utf-8');
    } else {
      throw new AppError(ErrorCodes.EXTRACTION_FAILURE, 'Sample policy data file not found', 500);
    }

    const parsedJson = JSON.parse(rawJson);

    // Validate with Zod schema
    const validationResult = PolicyExtractionSchema.safeParse(parsedJson);
    if (!validationResult.success) {
      logger.error('Policy schema validation failed in mock extractor', {
        event: 'policy_schema_validation_failed',
        error: validationResult.error.message,
      });
      throw new AppError(
        ErrorCodes.SCHEMA_VALIDATION_ERROR,
        'Extracted policy failed strict schema validation',
        500,
        validationResult.error.format()
      );
    }

    const data = validationResult.data;

    // Convert snake_case extraction schema to domain ExtractedPolicy
    const extracted: ExtractedPolicy = {
      policyMetadata: {
        insurerName: data.policy_metadata?.insurer_name ?? null,
        policyName: data.policy_metadata?.policy_name ?? null,
        policyNumber: data.policy_metadata?.policy_number ?? null,
      },
      sumInsured: {
        value: data.sum_insured.value,
        currency: data.sum_insured.currency || 'INR',
        source: data.sum_insured.source
          ? {
              page: data.sum_insured.source.page,
              text: data.sum_insured.source.text,
              boundingBox: data.sum_insured.source.bounding_box ?? null,
            }
          : null,
      },
      roomRentRule: {
        type: data.room_rent_rule.type,
        percentage: data.room_rent_rule.percentage ?? null,
        fixedAmount: data.room_rent_rule.fixed_amount ?? null,
        perDay: data.room_rent_rule.per_day ?? null,
        source: data.room_rent_rule.source
          ? {
              page: data.room_rent_rule.source.page,
              text: data.room_rent_rule.source.text,
              boundingBox: data.room_rent_rule.source.bounding_box ?? null,
            }
          : null,
        description: data.room_rent_rule.description,
      },
      copay: {
        percentage: data.copay.percentage,
        applies: data.copay.applies,
        conditions: data.copay.conditions ?? null,
        source: data.copay.source
          ? {
              page: data.copay.source.page,
              text: data.copay.source.text,
              boundingBox: data.copay.source.bounding_box ?? null,
            }
          : null,
      },
      subLimits: (data.sub_limits || []).map((sl) => ({
        procedureCode: sl.procedure_code ?? null,
        procedureName: sl.procedure_name,
        amount: sl.amount ?? null,
        percentageOfSumInsured: sl.percentage_of_sum_insured ?? null,
        applies: sl.applies,
        description: sl.description,
        source: sl.source
          ? {
              page: sl.source.page,
              text: sl.source.text,
              boundingBox: sl.source.bounding_box ?? null,
            }
          : null,
      })),
      deductibles: (data.deductibles || []).map((d) => ({
        amount: d.amount ?? null,
        applies: d.applies,
        scope: d.scope ?? undefined,
        source: d.source
          ? {
              page: d.source.page,
              text: d.source.text,
              boundingBox: d.source.bounding_box ?? null,
            }
          : null,
      })),
      exclusions: (data.exclusions || []).map((e) => ({
        name: e.name,
        code: e.code ?? undefined,
        description: e.description,
        isPermanent: e.is_permanent,
        source: e.source
          ? {
              page: e.source.page,
              text: e.source.text,
              boundingBox: e.source.bounding_box ?? null,
            }
          : null,
      })),
      waitingPeriods: (data.waiting_periods || []).map((w) => ({
        condition: w.condition,
        durationMonths: w.duration_months ?? null,
        source: w.source
          ? {
              page: w.source.page,
              text: w.source.text,
              boundingBox: w.source.bounding_box ?? null,
            }
          : null,
      })),
      unknownRules: data.unknown_rules || [],
    };

    logger.info('Policy extraction completed successfully with validated schema', {
      event: 'policy_extraction_completed',
      details: {
        insurer: extracted.policyMetadata.insurerName,
        sumInsured: extracted.sumInsured.value,
        roomRentType: extracted.roomRentRule.type,
      },
    });

    return extracted;
  }
}
