import { FastifyInstance, FastifyPluginAsync } from 'fastify';
import { prisma } from '../../common/database/prisma.js';
import { config } from '../../config/config.js';
import { ENGINE_VERSION } from '@policy-estimator/calculation-engine';

export const healthRoutes: FastifyPluginAsync = async (server: FastifyInstance) => {
  server.get('/', async (request, reply) => {
    let dbStatus = 'HEALTHY';
    try {
      await prisma.$queryRaw`SELECT 1`;
    } catch (err: any) {
      dbStatus = `DISCONNECTED: ${err.message}`;
    }

    return reply.send({
      status: 'UP',
      timestamp: new Date().toISOString(),
      engineVersion: ENGINE_VERSION,
      demoMode: config.demoMode,
      environment: config.env,
      database: dbStatus,
      services: {
        pdfParser: config.demoMode || !config.parser.llamaparseApiKey ? 'MOCK_PARSER' : 'LLAMAPARSE',
        llmExtractor: config.demoMode || !config.ai.openaiApiKey ? 'MOCK_EXTRACTOR' : 'OPENAI',
        storage: config.storage.provider,
      },
    });
  });
};
