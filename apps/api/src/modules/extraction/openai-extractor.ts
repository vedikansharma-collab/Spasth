import { PolicyExtractionProvider, ExtractedPolicy, ParsedDocument } from '@policy-estimator/types';
import { PolicyExtractionSchema } from '@policy-estimator/schemas';
import { logger } from '../../common/logging/logger.js';
import { MockPolicyExtractor } from './mock-extractor.js';

export class OpenAIPolicyExtractor implements PolicyExtractionProvider {
  private apiKey: string;
  private model: string;
  private baseUrl: string;
  private fallbackExtractor: MockPolicyExtractor;

  constructor(apiKey: string, model: string = 'gpt-4o-mini', baseUrl: string = 'https://api.openai.com/v1') {
    this.apiKey = apiKey;
    this.model = model;
    this.baseUrl = baseUrl;
    this.fallbackExtractor = new MockPolicyExtractor();
  }

  async extract(document: ParsedDocument): Promise<ExtractedPolicy> {
    if (!this.apiKey) {
      logger.warn('OPENAI_API_KEY is not configured. Falling back to MockPolicyExtractor.', {
        event: 'openai_extractor_fallback',
      });
      return this.fallbackExtractor.extract(document);
    }

    try {
      const documentContext = document.rawMarkdown || 
        document.pages.map(p => `--- PAGE ${p.pageNumber} ---\n${p.blocks.map(b => b.text).join('\n')}`).join('\n\n');

      const systemPrompt = `You are a document extraction engine.
Extract only information explicitly stated in the supplied insurance policy.
Do not calculate financial outcomes.
Do not infer missing values.
Do not use outside knowledge.
Do not guess.
For every extracted rule provide page number and source text.
If a rule is absent or ambiguous, return null or mark it unknown.
Return only the validated JSON strictly adhering to the schema.`;

      const response = await fetch(`${this.baseUrl}/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${this.apiKey}`,
        },
        body: JSON.stringify({
          model: this.model,
          response_format: { type: 'json_object' },
          messages: [
            { role: 'system', content: systemPrompt },
            { role: 'user', content: `Extract the policy facts from this insurance policy document:\n\n${documentContext.substring(0, 100000)}` },
          ],
          temperature: 0,
        }),
      });

      if (!response.ok) {
        throw new Error(`OpenAI API error: ${response.status} ${response.statusText}`);
      }

      const resData = await response.json() as any;
      const content = resData.choices?.[0]?.message?.content;
      if (!content) {
        throw new Error('Empty response from OpenAI');
      }

      const parsedJson = JSON.parse(content);
      const validation = PolicyExtractionSchema.safeParse(parsedJson);
      if (!validation.success) {
        logger.error('OpenAI JSON failed schema validation', {
          event: 'openai_schema_mismatch',
          error: validation.error.message,
        });
        return this.fallbackExtractor.extract(document);
      }

      // Convert to ExtractedPolicy
      const data = validation.data;
      return {
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
    } catch (err: any) {
      logger.error('Error during OpenAI extraction; falling back to mock extractor', {
        event: 'openai_extraction_error',
        error: err.message,
      });
      return this.fallbackExtractor.extract(document);
    }
  }
}
