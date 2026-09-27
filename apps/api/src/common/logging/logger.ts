export interface LogPayload {
  event: string;
  policyId?: string;
  calculationId?: string;
  durationMs?: number;
  status?: string;
  details?: Record<string, any>;
  error?: string;
}

export const logger = {
  info(message: string, payload?: LogPayload) {
    console.log(JSON.stringify({
      timestamp: new Date().toISOString(),
      level: 'INFO',
      message,
      ...payload,
    }));
  },

  warn(message: string, payload?: LogPayload) {
    console.warn(JSON.stringify({
      timestamp: new Date().toISOString(),
      level: 'WARN',
      message,
      ...payload,
    }));
  },

  error(message: string, payload?: LogPayload) {
    console.error(JSON.stringify({
      timestamp: new Date().toISOString(),
      level: 'ERROR',
      message,
      ...payload,
    }));
  },
};
