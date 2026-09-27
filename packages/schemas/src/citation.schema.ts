import { z } from 'zod';
import { BoundingBoxSchema } from './policy.schema.js';

export const CitationSchema = z.object({
  id: z.string().optional(),
  policyId: z.string().optional(),
  policyRuleId: z.string().optional(),
  pageNumber: z.number().int().positive(),
  sourceText: z.string().min(1),
  boundingBox: BoundingBoxSchema.nullable().optional(),
});

export type CitationData = z.infer<typeof CitationSchema>;
