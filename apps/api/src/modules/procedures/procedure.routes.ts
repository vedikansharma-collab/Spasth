import { FastifyInstance, FastifyPluginAsync } from 'fastify';
import { costRepository } from '../costs/cost.repository.js';
import { AppError, ErrorCodes } from '../../common/errors/app-error.js';

export const procedureRoutes: FastifyPluginAsync = async (server: FastifyInstance) => {
  // GET /api/procedures
  server.get('/', async (request, reply) => {
    const procedures = await costRepository.listProcedures();
    return reply.send(procedures);
  });

  // GET /api/procedures/:id
  server.get('/:id', async (request, reply) => {
    const { id } = request.params as { id: string };
    const procedure = await costRepository.getProcedureByCode(id);
    if (!procedure) {
      throw new AppError(ErrorCodes.PROCEDURE_NOT_FOUND, `Procedure not found with code: ${id}`, 404);
    }
    return reply.send(procedure);
  });

  // GET /api/procedures/:id/costs
  server.get('/:id/costs', async (request, reply) => {
    const { id } = request.params as { id: string };
    const costs = await costRepository.listCostsForProcedure(id);
    return reply.send(costs);
  });
};
