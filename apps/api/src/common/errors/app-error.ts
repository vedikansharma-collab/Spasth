export class AppError extends Error {
  public readonly errorCode: string;
  public readonly statusCode: number;
  public readonly details?: any;

  constructor(errorCode: string, message: string, statusCode: number = 400, details?: any) {
    super(message);
    this.name = 'AppError';
    this.errorCode = errorCode;
    this.statusCode = statusCode;
    this.details = details;
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export const ErrorCodes = {
  INVALID_FILE_TYPE: 'INVALID_FILE_TYPE',
  FILE_TOO_LARGE: 'FILE_TOO_LARGE',
  FILE_NOT_FOUND: 'FILE_NOT_FOUND',
  POLICY_NOT_FOUND: 'POLICY_NOT_FOUND',
  PROCEDURE_NOT_FOUND: 'PROCEDURE_NOT_FOUND',
  COST_DATA_NOT_FOUND: 'COST_DATA_NOT_FOUND',
  CALCULATION_ERROR: 'CALCULATION_ERROR',
  PARSER_FAILURE: 'PARSER_FAILURE',
  EXTRACTION_FAILURE: 'EXTRACTION_FAILURE',
  SCHEMA_VALIDATION_ERROR: 'SCHEMA_VALIDATION_ERROR',
  INTERNAL_SERVER_ERROR: 'INTERNAL_SERVER_ERROR',
} as const;
