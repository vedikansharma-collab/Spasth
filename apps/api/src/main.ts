import Fastify from 'fastify';
import cors from '@fastify/cors';
import multipart from '@fastify/multipart';
import rateLimit from '@fastify/rate-limit';
import fastifyStatic from '@fastify/static';
import path from 'path';
import { config } from './config/config.js';
import { logger } from './common/logging/logger.js';
import { AppError } from './common/errors/app-error.js';
import { policyRoutes } from './modules/policies/policy.routes.js';
import { procedureRoutes } from './modules/procedures/procedure.routes.js';
import { calculatorRoutes } from './modules/calculator/calculator.routes.js';
import { citationRoutes } from './modules/citations/citation.routes.js';
import { healthRoutes } from './modules/health/health.routes.js';

export async function buildServer() {
  const server = Fastify({
    logger: false, // Using structured custom JSON logger
    bodyLimit: 30 * 1024 * 1024,
  });

  // CORS
  await server.register(cors, {
    origin: (origin, cb) => {
      // Allow local development and specified origin
      cb(null, true);
    },
    credentials: true,
  });

  // Multipart for PDF uploads
  await server.register(multipart, {
    limits: {
      fileSize: config.storage.maxFileSize,
      files: 1,
    },
  });

  // Rate Limiting
  await server.register(rateLimit, {
    max: 200,
    timeWindow: '1 minute',
  });

  // Static files for policy PDFs
  await server.register(fastifyStatic, {
    root: path.resolve(config.storage.basePath),
    prefix: '/storage/',
  });

  // Global Error Handler
  server.setErrorHandler((error, request, reply) => {
    if (error instanceof AppError) {
      logger.warn('Application error', {
        event: 'app_error',
        status: error.errorCode,
        details: { message: error.message, details: error.details },
      });
      return reply.status(error.statusCode).send({
        errorCode: error.errorCode,
        message: error.message,
        details: error.details,
      });
    }

    logger.error('Unhandled server error', {
      event: 'internal_server_error',
      error: error.message,
      details: { stack: process.env.NODE_ENV === 'development' ? error.stack : undefined },
    });

    return reply.status(error.statusCode || 500).send({
      errorCode: 'INTERNAL_SERVER_ERROR',
      message: error.message || 'An unexpected error occurred',
    });
  });

  // Register Modules
  await server.register(healthRoutes, { prefix: '/api/health' });
  await server.register(policyRoutes, { prefix: '/api/policies' });
  await server.register(procedureRoutes, { prefix: '/api/procedures' });
  await server.register(calculatorRoutes, { prefix: '/api/calculations' });
  await server.register(citationRoutes, { prefix: '/api/citations' });

  return server;
}

async function start() {
  try {
    const server = await buildServer();
    await server.listen({ port: config.port, host: config.host });
    console.log(`
=============================================================
  POLICY-LINKED TREATMENT COST ESTIMATION SYSTEM (API)
=============================================================
  Status:           ONLINE
  Port:             ${config.port}
  Host:             ${config.host}
  Environment:      ${config.env}
  Demo Mode:        ${config.demoMode ? 'ENABLED (Zero-Key Demo Active)' : 'DISABLED'}
  Storage Path:     ${config.storage.basePath}
  PostgreSQL DB:    ${config.database.url.split('@')[1] || 'localhost:5432'}
  Health Check:     http://localhost:${config.port}/api/health
=============================================================
    `);
  } catch (err) {
    console.error('Fatal error starting API server:', err);
    process.exit(1);
  }
}

// Start if run directly
if (process.argv[1]?.endsWith('main.ts') || process.argv[1]?.endsWith('main.js')) {
  start();
}
