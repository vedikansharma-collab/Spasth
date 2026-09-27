import { prisma } from '../../common/database/prisma.js';
import { storageService } from '../../common/storage/storage.service.js';
import { getDocumentParser } from '../documents/parser.factory.js';
import { getPolicyExtractor } from '../extraction/extractor.factory.js';
import { logger } from '../../common/logging/logger.js';
import { AppError, ErrorCodes } from '../../common/errors/app-error.js';
import { ExtractedPolicy, PolicyStatus } from '@policy-estimator/types';

export class PolicyService {
  async uploadAndProcessPolicy(fileBuffer: Buffer, fileName: string): Promise<string> {
    const startTime = Date.now();
    const sanitizedName = storageService.sanitizeFilename(fileName);
    const storageKey = `policies/${Date.now()}_${sanitizedName}`;

    // 1. Store original PDF
    await storageService.save(storageKey, fileBuffer);

    // 2. Create initial record in database
    const policy = await prisma.policy.create({
      data: {
        fileName: sanitizedName,
        filePath: storageKey,
        status: 'UPLOADED',
        extractionVersion: '1.0.0',
      },
    });

    const policyId = policy.id;
    logger.info('Policy uploaded, starting background processing pipeline', {
      event: 'policy_upload_started',
      policyId,
    });

    // 3. Run processing pipeline
    this.runProcessingPipeline(policyId, fileBuffer, sanitizedName).catch((err) => {
      logger.error('Unhandled pipeline failure', {
        event: 'policy_pipeline_fatal',
        policyId,
        error: err.message,
      });
    });

    return policyId;
  }

  private async runProcessingPipeline(policyId: string, fileBuffer: Buffer, fileName: string): Promise<void> {
    try {
      // Step A: PARSING
      await this.updateStatus(policyId, 'PARSING');
      const parser = getDocumentParser();
      const parsedDoc = await parser.parse(fileBuffer, fileName);

      // Step B: EXTRACTING
      await this.updateStatus(policyId, 'EXTRACTING');
      const extractor = getPolicyExtractor();
      const extractedPolicy: ExtractedPolicy = await extractor.extract(parsedDoc);

      // Step C: VALIDATING & PERSISTING
      await this.updateStatus(policyId, 'VALIDATING');
      await this.persistExtractedPolicy(policyId, extractedPolicy, parsedDoc);

      // Step D: READY
      await this.updateStatus(policyId, 'READY');
      logger.info('Policy processing pipeline completed successfully', {
        event: 'policy_pipeline_completed',
        policyId,
      });
    } catch (err: any) {
      logger.error('Policy processing pipeline failed', {
        event: 'policy_pipeline_failed',
        policyId,
        error: err.message,
      });

      await prisma.policy.update({
        where: { id: policyId },
        data: {
          status: 'FAILED',
          errorMessage: err.message || 'Processing pipeline error',
        },
      });
    }
  }

  private async updateStatus(policyId: string, status: PolicyStatus): Promise<void> {
    await prisma.policy.update({
      where: { id: policyId },
      data: { status },
    });
  }

  private async persistExtractedPolicy(
    policyId: string,
    extracted: ExtractedPolicy,
    parsedDoc: any
  ): Promise<void> {
    // Update top-level policy metadata
    await prisma.policy.update({
      where: { id: policyId },
      data: {
        insurerName: extracted.policyMetadata.insurerName || 'Unknown Insurer',
        policyName: extracted.policyMetadata.policyName || 'Standard Policy',
        rawMarkdown: parsedDoc.rawMarkdown || null,
        parsedDocumentJson: {
          extractedPolicy: extracted,
          metadata: parsedDoc.metadata,
        },
      },
    });

    // Clean previous rules if any
    await prisma.citation.deleteMany({ where: { policyId } });
    await prisma.policyRule.deleteMany({ where: { policyId } });

    // 1. Sum Insured
    if (extracted.sumInsured) {
      const rule = await prisma.policyRule.create({
        data: {
          policyId,
          ruleType: 'SUM_INSURED',
          ruleName: 'Sum Insured',
          value: extracted.sumInsured.value,
          unit: extracted.sumInsured.currency || 'INR',
          description: `Total Sum Insured coverage amount: ₹${extracted.sumInsured.value?.toLocaleString('en-IN')}`,
          sourcePage: extracted.sumInsured.source?.page ?? null,
          sourceText: extracted.sumInsured.source?.text ?? null,
          boundingBox: extracted.sumInsured.source?.boundingBox ?? undefined,
          confidenceLevel: extracted.sumInsured.value ? 'HIGH' : 'LOW',
        },
      });

      if (extracted.sumInsured.source) {
        await prisma.citation.create({
          data: {
            policyId,
            policyRuleId: rule.id,
            pageNumber: extracted.sumInsured.source.page,
            sourceText: extracted.sumInsured.source.text,
            boundingBox: extracted.sumInsured.source.boundingBox ?? undefined,
          },
        });
      }
    }

    // 2. Room Rent Cap
    if (extracted.roomRentRule) {
      const rr = extracted.roomRentRule;
      const rule = await prisma.policyRule.create({
        data: {
          policyId,
          ruleType: 'ROOM_RENT_CAP',
          ruleName: 'Room Rent Restriction',
          value: rr.type === 'PERCENTAGE_OF_SUM_INSURED' ? rr.percentage : rr.fixedAmount,
          unit: rr.type === 'PERCENTAGE_OF_SUM_INSURED' ? '%' : 'INR',
          description: rr.description || `Room rent rule: ${rr.type}`,
          sourcePage: rr.source?.page ?? null,
          sourceText: rr.source?.text ?? null,
          boundingBox: rr.source?.boundingBox ?? undefined,
          confidenceLevel: rr.type !== 'UNKNOWN' ? 'HIGH' : 'LOW',
        },
      });

      if (rr.source) {
        await prisma.citation.create({
          data: {
            policyId,
            policyRuleId: rule.id,
            pageNumber: rr.source.page,
            sourceText: rr.source.text,
            boundingBox: rr.source.boundingBox ?? undefined,
          },
        });
      }
    }

    // 3. Co-Pay
    if (extracted.copay) {
      const copay = extracted.copay;
      const rule = await prisma.policyRule.create({
        data: {
          policyId,
          ruleType: 'COPAY',
          ruleName: 'Co-Payment Clause',
          value: copay.percentage,
          unit: '%',
          description: copay.applies ? `${copay.percentage}% co-pay applicable.` : 'No co-pay applicable.',
          sourcePage: copay.source?.page ?? null,
          sourceText: copay.source?.text ?? null,
          boundingBox: copay.source?.boundingBox ?? undefined,
          confidenceLevel: 'HIGH',
        },
      });

      if (copay.source) {
        await prisma.citation.create({
          data: {
            policyId,
            policyRuleId: rule.id,
            pageNumber: copay.source.page,
            sourceText: copay.source.text,
            boundingBox: copay.source.boundingBox ?? undefined,
          },
        });
      }
    }

    // 4. Sub-limits
    for (const sl of extracted.subLimits || []) {
      const rule = await prisma.policyRule.create({
        data: {
          policyId,
          ruleType: 'PROCEDURE_SUBLIMIT',
          ruleName: `Sub-limit: ${sl.procedureName}`,
          value: sl.amount,
          unit: 'INR',
          description: sl.description || `Sub-limit for ${sl.procedureName}`,
          sourcePage: sl.source?.page ?? null,
          sourceText: sl.source?.text ?? null,
          boundingBox: sl.source?.boundingBox ?? undefined,
          confidenceLevel: 'HIGH',
        },
      });

      if (sl.source) {
        await prisma.citation.create({
          data: {
            policyId,
            policyRuleId: rule.id,
            pageNumber: sl.source.page,
            sourceText: sl.source.text,
            boundingBox: sl.source.boundingBox ?? undefined,
          },
        });
      }
    }

    // 5. Exclusions
    for (const ex of extracted.exclusions || []) {
      const rule = await prisma.policyRule.create({
        data: {
          policyId,
          ruleType: 'EXCLUSION',
          ruleName: `Exclusion: ${ex.name}`,
          value: null,
          unit: null,
          description: ex.description || ex.name,
          sourcePage: ex.source?.page ?? null,
          sourceText: ex.source?.text ?? null,
          boundingBox: ex.source?.boundingBox ?? undefined,
          confidenceLevel: 'HIGH',
        },
      });

      if (ex.source) {
        await prisma.citation.create({
          data: {
            policyId,
            policyRuleId: rule.id,
            pageNumber: ex.source.page,
            sourceText: ex.source.text,
            boundingBox: ex.source.boundingBox ?? undefined,
          },
        });
      }
    }

    // 6. Waiting Periods
    for (const wp of extracted.waitingPeriods || []) {
      const rule = await prisma.policyRule.create({
        data: {
          policyId,
          ruleType: 'WAITING_PERIOD',
          ruleName: `Waiting Period: ${wp.condition}`,
          value: wp.durationMonths,
          unit: 'MONTHS',
          description: `${wp.durationMonths} months waiting period for ${wp.condition}`,
          sourcePage: wp.source?.page ?? null,
          sourceText: wp.source?.text ?? null,
          boundingBox: wp.source?.boundingBox ?? undefined,
          confidenceLevel: 'HIGH',
        },
      });

      if (wp.source) {
        await prisma.citation.create({
          data: {
            policyId,
            policyRuleId: rule.id,
            pageNumber: wp.source.page,
            sourceText: wp.source.text,
            boundingBox: wp.source.boundingBox ?? undefined,
          },
        });
      }
    }
  }

  async getPolicyById(id: string) {
    const policy = await prisma.policy.findUnique({
      where: { id },
      include: {
        rules: true,
        citations: true,
      },
    });

    if (!policy) {
      throw new AppError(ErrorCodes.POLICY_NOT_FOUND, `Policy not found with id: ${id}`, 404);
    }

    return policy;
  }

  async getPolicyStatus(id: string) {
    const policy = await prisma.policy.findUnique({
      where: { id },
      select: {
        id: true,
        status: true,
        errorMessage: true,
        updatedAt: true,
      },
    });

    if (!policy) {
      throw new AppError(ErrorCodes.POLICY_NOT_FOUND, `Policy not found with id: ${id}`, 404);
    }

    return policy;
  }

  async getPolicyRules(id: string) {
    const rules = await prisma.policyRule.findMany({
      where: { policyId: id },
      include: { citations: true },
    });
    return rules;
  }

  async getPolicyCitations(id: string) {
    const citations = await prisma.citation.findMany({
      where: { policyId: id },
      include: { policyRule: true },
    });
    return citations;
  }

  async getLatestOrSamplePolicy() {
    let policy = await prisma.policy.findFirst({
      where: { status: 'READY' },
      orderBy: { createdAt: 'desc' },
      include: { rules: true, citations: true },
    });
    return policy;
  }
}

export const policyService = new PolicyService();
