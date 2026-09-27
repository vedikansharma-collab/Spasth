import { z } from 'zod';

export const RoomCategorySchema = z.enum([
  'GENERAL',
  'TWIN_SHARING',
  'SINGLE_PRIVATE',
  'DELUXE',
]);

export const HospitalCostScenarioSchema = z.object({
  id: z.string().optional(),
  procedureCode: z.string().min(1),
  procedureName: z.string().min(1),
  city: z.string().default('National Average'),
  roomCategory: RoomCategorySchema,
  roomRate: z.number().nonnegative(),
  stayDays: z.number().int().positive().default(1),
  proportionateCosts: z.number().nonnegative(),
  nonProportionateCosts: z.number().nonnegative(),
  otherCosts: z.number().nonnegative().default(0),
  totalBill: z.number().positive(),
  currency: z.string().default('INR'),
  source: z.string().optional(),
});

export type HospitalCostScenarioData = z.infer<typeof HospitalCostScenarioSchema>;
