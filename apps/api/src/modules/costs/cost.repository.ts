import { CostRepository, HospitalCostScenario, Procedure, RoomCategory } from '@policy-estimator/types';
import { prisma } from '../../common/database/prisma.js';
import { logger } from '../../common/logging/logger.js';

export class PrismaCostRepository implements CostRepository {
  async findScenario(
    procedureCode: string,
    roomCategory: RoomCategory,
    city: string = 'National Average'
  ): Promise<HospitalCostScenario | null> {
    const procedure = await prisma.procedure.findUnique({
      where: { code: procedureCode },
      include: {
        hospitalCosts: {
          where: {
            roomCategory,
          },
        },
      },
    });

    if (!procedure || procedure.hospitalCosts.length === 0) {
      return null;
    }

    const cost = procedure.hospitalCosts[0];
    return {
      id: cost.id,
      procedureCode: procedure.code,
      procedureName: procedure.name,
      city: cost.city,
      roomCategory: cost.roomCategory as RoomCategory,
      roomRate: cost.roomRate,
      stayDays: cost.stayDays,
      proportionateCosts: cost.proportionateCosts,
      nonProportionateCosts: cost.nonProportionateCosts,
      otherCosts: cost.otherCosts,
      totalBill: cost.totalBill,
      currency: cost.currency,
      source: cost.source ?? undefined,
    };
  }

  async listProcedures(): Promise<Procedure[]> {
    const procedures = await prisma.procedure.findMany({
      orderBy: { name: 'asc' },
    });
    return procedures.map(p => ({
      id: p.id,
      code: p.code,
      name: p.name,
      category: p.category,
      description: p.description,
    }));
  }

  async getProcedureByCode(code: string): Promise<Procedure | null> {
    const procedure = await prisma.procedure.findUnique({
      where: { code },
    });
    if (!procedure) return null;
    return {
      id: procedure.id,
      code: procedure.code,
      name: procedure.name,
      category: procedure.category,
      description: procedure.description,
    };
  }

  async listCostsForProcedure(procedureCode: string): Promise<HospitalCostScenario[]> {
    const procedure = await prisma.procedure.findUnique({
      where: { code: procedureCode },
      include: {
        hospitalCosts: true,
      },
    });

    if (!procedure) return [];

    return procedure.hospitalCosts.map(cost => ({
      id: cost.id,
      procedureCode: procedure.code,
      procedureName: procedure.name,
      city: cost.city,
      roomCategory: cost.roomCategory as RoomCategory,
      roomRate: cost.roomRate,
      stayDays: cost.stayDays,
      proportionateCosts: cost.proportionateCosts,
      nonProportionateCosts: cost.nonProportionateCosts,
      otherCosts: cost.otherCosts,
      totalBill: cost.totalBill,
      currency: cost.currency,
      source: cost.source ?? undefined,
    }));
  }
}

export const costRepository = new PrismaCostRepository();
