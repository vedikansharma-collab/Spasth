import dotenv from 'dotenv';
import path from 'path';

// Load .env from project root if available
dotenv.config({ path: path.resolve(process.cwd(), '../../.env') });
dotenv.config();

export const config = {
  env: process.env.NODE_ENV || 'development',
  port: parseInt(process.env.PORT || '4000', 10),
  host: process.env.HOST || '0.0.0.0',
  demoMode: process.env.DEMO_MODE !== 'false', // Default to true for zero-friction demo
  
  database: {
    url: process.env.DATABASE_URL || 'postgresql://postgres:postgres@localhost:5432/policy_estimator',
  },

  storage: {
    provider: process.env.STORAGE_PROVIDER || 'local',
    basePath: path.resolve(process.cwd(), process.env.STORAGE_PATH || '../../storage'),
    maxFileSize: 25 * 1024 * 1024, // 25 MB
  },

  cors: {
    origin: process.env.CORS_ORIGIN || 'http://localhost:3000',
  },

  ai: {
    openaiApiKey: process.env.OPENAI_API_KEY || '',
    openaiModel: process.env.OPENAI_MODEL || 'gpt-4o-mini',
    openaiBaseUrl: process.env.OPENAI_BASE_URL || 'https://api.openai.com/v1',
  },

  parser: {
    llamaparseApiKey: process.env.LLAMAPARSE_API_KEY || '',
  },
};
