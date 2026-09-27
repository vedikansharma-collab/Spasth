import fs from 'fs';
import path from 'path';
import { FileStorage } from '@policy-estimator/types';
import { config } from '../../config/config.js';
import { AppError, ErrorCodes } from '../errors/app-error.js';

export class LocalFileStorage implements FileStorage {
  private basePath: string;

  constructor(basePath: string = config.storage.basePath) {
    this.basePath = basePath;
    this.ensureDirectoryExists(this.basePath);
    this.ensureDirectoryExists(path.join(this.basePath, 'policies'));
    this.ensureDirectoryExists(path.join(this.basePath, 'parsed'));
  }

  private ensureDirectoryExists(dir: string): void {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  }

  public sanitizeFilename(fileName: string): string {
    return fileName.replace(/[^a-zA-Z0-9._-]/g, '_');
  }

  async save(key: string, data: Buffer): Promise<string> {
    const fullPath = path.join(this.basePath, key);
    const parentDir = path.dirname(fullPath);
    this.ensureDirectoryExists(parentDir);

    await fs.promises.writeFile(fullPath, data);
    return key;
  }

  async get(key: string): Promise<Buffer> {
    const fullPath = path.join(this.basePath, key);
    if (!fs.existsSync(fullPath)) {
      throw new AppError(ErrorCodes.FILE_NOT_FOUND, `File not found at key: ${key}`, 404);
    }
    return await fs.promises.readFile(fullPath);
  }

  async delete(key: string): Promise<void> {
    const fullPath = path.join(this.basePath, key);
    if (fs.existsSync(fullPath)) {
      await fs.promises.unlink(fullPath);
    }
  }

  getAbsolutePath(key: string): string {
    return path.join(this.basePath, key);
  }
}

export const storageService = new LocalFileStorage();
