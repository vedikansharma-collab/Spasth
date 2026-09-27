import { z } from 'zod';
import { RoomCategorySchema } from './cost.schema.js';

export const CalculationInputSchema = z.object({
  policyId: z.string().min(1),
  procedureCode: z.string().min(1),
  roomCategory: RoomCategorySchema,
  stayDays: z.number().int().positive().optional(),
  city: z.string().optional(),
  customRoomRate: z.number().positive().optional(),
});

export const RecalculateInputSchema = z.object({
  policyId: z.string().min(1),
  procedureCode: z.string().min(1),
  roomCategory: RoomCategorySchema,
  stayDays: z.number().int().positive().optional(),
  city: z.string().optional(),
  customRoomRate: z.number().positive().optional(),
});

export const CalculationResultItemSchema = z.object({
  allowedRoomRent: z.number(),
  roomFactor: z.number(),
  insurerProportionateShare: z.number(),
  coveredRoomRent: z.number(),
  baseInsurerLiability: z.number(),
  deductible: z.number(),
  copayPercentage: z.number(),
  copayAmount: z.number(),
  postCopayPay: z.number(),
  procedureSubLimit: z.number().nullable(),
  finalInsurerPay: z.number(),
  outOfPocket: z.number(),
});

export type CalculationInputData = z.infer<typeof CalculationInputSchema>;
export type RecalculateInputData = z.infer<typeof RecalculateInputSchema>;
