import { z } from 'zod';

export const BoundingBoxSchema = z.object({
  x: z.number(),
  y: z.number(),
  width: z.number(),
  height: z.number(),
});

export const RuleSourceSchema = z.object({
  page: z.number().int().positive(),
  text: z.string().min(1),
  bounding_box: BoundingBoxSchema.nullable().optional(),
});

export const PolicyMetadataSchema = z.object({
  insurer_name: z.string().nullable().optional(),
  policy_name: z.string().nullable().optional(),
  policy_number: z.string().nullable().optional(),
});

export const SumInsuredRuleSchema = z.object({
  value: z.number().positive().nullable(),
  currency: z.string().default('INR'),
  source: RuleSourceSchema.nullable().optional(),
});

export const RoomRentRuleTypeSchema = z.enum([
  'PERCENTAGE_OF_SUM_INSURED',
  'FIXED_AMOUNT_PER_DAY',
  'FIXED_AMOUNT_PER_HOSPITALIZATION',
  'NO_LIMIT',
  'UNKNOWN',
]);

export const RoomRentRuleSchema = z.object({
  type: RoomRentRuleTypeSchema,
  percentage: z.number().min(0).max(100).nullable().optional(),
  fixed_amount: z.number().positive().nullable().optional(),
  per_day: z.boolean().nullable().optional(),
  source: RuleSourceSchema.nullable().optional(),
  description: z.string().optional(),
});

export const CopayRuleSchema = z.object({
  percentage: z.number().min(0).max(100).nullable(),
  applies: z.boolean().nullable(),
  source: RuleSourceSchema.nullable().optional(),
  conditions: z.string().nullable().optional(),
});

export const SubLimitItemSchema = z.object({
  procedure_code: z.string().nullable().optional(),
  procedure_name: z.string(),
  amount: z.number().positive().nullable().optional(),
  percentage_of_sum_insured: z.number().min(0).max(100).nullable().optional(),
  applies: z.boolean().default(true),
  source: RuleSourceSchema.nullable().optional(),
  description: z.string().optional(),
});

export const DeductibleItemSchema = z.object({
  amount: z.number().positive().nullable(),
  applies: z.boolean().default(true),
  scope: z.string().nullable().optional(),
  source: RuleSourceSchema.nullable().optional(),
});

export const ExclusionItemSchema = z.object({
  name: z.string(),
  code: z.string().nullable().optional(),
  description: z.string().optional(),
  is_permanent: z.boolean().default(true),
  source: RuleSourceSchema.nullable().optional(),
});

export const WaitingPeriodItemSchema = z.object({
  condition: z.string(),
  duration_months: z.number().int().nonnegative().nullable(),
  source: RuleSourceSchema.nullable().optional(),
});

export const UnknownRuleItemSchema = z.object({
  category: z.string(),
  reason: z.string(),
  notes: z.string().optional(),
});

// Full extraction schema (snake_case from LLM, mapped to domain models)
export const PolicyExtractionSchema = z.object({
  policy_metadata: PolicyMetadataSchema,
  sum_insured: SumInsuredRuleSchema,
  room_rent_rule: RoomRentRuleSchema,
  copay: CopayRuleSchema,
  sub_limits: z.array(SubLimitItemSchema).default([]),
  deductibles: z.array(DeductibleItemSchema).default([]),
  exclusions: z.array(ExclusionItemSchema).default([]),
  waiting_periods: z.array(WaitingPeriodItemSchema).default([]),
  unknown_rules: z.array(UnknownRuleItemSchema).default([]),
});

export type PolicyExtractionData = z.infer<typeof PolicyExtractionSchema>;
