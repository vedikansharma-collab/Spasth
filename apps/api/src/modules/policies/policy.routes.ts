import { FastifyInstance, FastifyPluginAsync } from 'fastify';
import { policyService } from './policy.service.js';
import { AppError, ErrorCodes } from '../../common/errors/app-error.js';

export const policyRoutes: FastifyPluginAsync = async (server: FastifyInstance) => {
  // POST /api/policies/upload
  server.post('/upload', async (request, reply) => {
    const data = await request.file();
    if (!data) {
      throw new AppError(ErrorCodes.INVALID_FILE_TYPE, 'No file uploaded', 400);
    }

    if (!data.filename.toLowerCase().endsWith('.pdf') && data.mimetype !== 'application/pdf') {
      throw new AppError(ErrorCodes.INVALID_FILE_TYPE, 'Only PDF documents are accepted', 400);
    }

    const buffer = await data.toBuffer();
    if (buffer.length > 25 * 1024 * 1024) {
      throw new AppError(ErrorCodes.FILE_TOO_LARGE, 'PDF exceeds maximum size limit of 25MB', 400);
    }

    const policyId = await policyService.uploadAndProcessPolicy(buffer, data.filename);
    return reply.status(202).send({
      policyId,
      status: 'UPLOADING',
      message: 'Policy upload received; processing pipeline started.',
    });
  });

  // GET /api/policies/latest
  server.get('/latest', async (request, reply) => {
    const policy = await policyService.getLatestOrSamplePolicy();
    if (!policy) {
      throw new AppError(ErrorCodes.POLICY_NOT_FOUND, 'No policy found. Please upload a policy or run seed.', 404);
    }
    return reply.send(policy);
  });

  // GET /api/policies/:id
  server.get('/:id', async (request, reply) => {
    const { id } = request.params as { id: string };
    const policy = await policyService.getPolicyById(id);
    return reply.send(policy);
  });

  // GET /api/policies/:id/status
  server.get('/:id/status', async (request, reply) => {
    const { id } = request.params as { id: string };
    const status = await policyService.getPolicyStatus(id);
    return reply.send(status);
  });

  // GET /api/policies/:id/rules
  server.get('/:id/rules', async (request, reply) => {
    const { id } = request.params as { id: string };
    const rules = await policyService.getPolicyRules(id);
    return reply.send(rules);
  });

  // GET /api/policies/:id/citations
  server.get('/:id/citations', async (request, reply) => {
    const { id } = request.params as { id: string };
    const citations = await policyService.getPolicyCitations(id);
    return reply.send(citations);
  });
};
