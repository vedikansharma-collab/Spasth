import { FastifyInstance, FastifyPluginAsync } from 'fastify';
import { calculatorService } from './calculator.service.js';
import { CalculationInputSchema, RecalculateInputSchema } from '@policy-estimator/schemas';
import { AppError, ErrorCodes } from '../../common/errors/app-error.js';

export const calculatorRoutes: FastifyPluginAsync = async (server: FastifyInstance) => {
  // POST /api/calculations
  server.post('/', async (request, reply) => {
    const parseResult = CalculationInputSchema.safeParse(request.body);
    if (!parseResult.success) {
      throw new AppError(
        ErrorCodes.SCHEMA_VALIDATION_ERROR,
        'Invalid calculation input data',
        400,
        parseResult.error.format()
      );
    }

    const { policyId, procedureCode, roomCategory, stayDays, city, customRoomRate } = parseResult.data;
    const result = await calculatorService.calculate(
      policyId,
      {
        procedureCode,
        roomCategory,
        stayDays,
        city,
        customRoomRate,
      },
      false
    );

    return reply.status(200).send(result);
  });

  // POST /api/calculations/recalculate
  server.post('/recalculate', async (request, reply) => {
    const parseResult = RecalculateInputSchema.safeParse(request.body);
    if (!parseResult.success) {
      throw new AppError(
        ErrorCodes.SCHEMA_VALIDATION_ERROR,
        'Invalid recalculate input data',
        400,
        parseResult.error.format()
      );
    }

    const { policyId, procedureCode, roomCategory, stayDays, city, customRoomRate } = parseResult.data;
    const result = await calculatorService.calculate(
      policyId,
      {
        procedureCode,
        roomCategory,
        stayDays,
        city,
        customRoomRate,
      },
      true // Mark as recalculation (pure deterministic engine execution)
    );

    return reply.status(200).send(result);
  });

  // GET /api/calculations/:id
  server.get('/:id', async (request, reply) => {
    const { id } = request.params as { id: string };
    const calculation = await calculatorService.getCalculationById(id);
    return reply.send(calculation);
  });
};
