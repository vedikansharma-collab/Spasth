import { FastifyInstance, FastifyPluginAsync } from 'fastify';
import { prisma } from '../../common/database/prisma.js';

export const citationRoutes: FastifyPluginAsync = async (server: FastifyInstance) => {
  // GET /api/citations/:id
  server.get('/:id', async (request, reply) => {
    const { id } = request.params as { id: string };
    const citation = await prisma.citation.findUnique({
      where: { id },
      include: { policyRule: true, policy: true },
    });
    if (!citation) {
      return reply.status(404).send({ error: 'Citation not found' });
    }
    return reply.send(citation);
  });
};
