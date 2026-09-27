import { z } from 'zod';

export const ProcedureSchema = z.object({
  id: z.string().optional(),
  code: z.string().min(1),
  name: z.string().min(1),
  category: z.string().min(1),
  description: z.string().nullable().optional(),
});

export type ProcedureData = z.infer<typeof ProcedureSchema>;
