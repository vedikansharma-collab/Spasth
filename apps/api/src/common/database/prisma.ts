import { PrismaClient } from '@prisma/client';
import { logger } from '../logging/logger.js';

let prismaInstance: PrismaClient | null = null;

export function getPrismaClient(): PrismaClient {
  if (!prismaInstance) {
    prismaInstance = new PrismaClient({
      log: process.env.NODE_ENV === 'development' ? ['warn', 'error'] : ['error'],
    });

    prismaInstance.$connect().catch((err) => {
      logger.error('Failed to connect to PostgreSQL database', {
        event: 'database_connection_error',
        error: err.message,
      });
    });
  }

  return prismaInstance;
}

export const prisma = getPrismaClient();
