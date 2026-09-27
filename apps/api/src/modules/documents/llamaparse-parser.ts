import { DocumentParser, ParsedDocument } from '@policy-estimator/types';
import { logger } from '../../common/logging/logger.js';
import { AppError, ErrorCodes } from '../../common/errors/app-error.js';
import { MockDocumentParser } from './mock-parser.js';

export class LlamaParseDocumentParser implements DocumentParser {
  private apiKey: string;
  private fallbackParser: MockDocumentParser;

  constructor(apiKey: string) {
    this.apiKey = apiKey;
    this.fallbackParser = new MockDocumentParser();
  }

  async parse(fileBuffer: Buffer, fileName: string): Promise<ParsedDocument> {
    if (!this.apiKey) {
      logger.warn('LLAMAPARSE_API_KEY is not set. Falling back to layout-aware mock parser.', {
        event: 'llamaparse_fallback',
      });
      return this.fallbackParser.parse(fileBuffer, fileName);
    }

    try {
      logger.info('Calling LlamaParse API for document layout parsing', {
        event: 'llamaparse_request',
        details: { fileName, fileSize: fileBuffer.length },
      });

      // LlamaParse REST API integration endpoint
      // https://api.cloud.llamaindex.ai/api/parsing/upload
      const formData = new FormData();
      formData.append('file', new Blob([fileBuffer]), fileName);

      const uploadRes = await fetch('https://api.cloud.llamaindex.ai/api/parsing/upload', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${this.apiKey}`,
        },
        body: formData,
      });

      if (!uploadRes.ok) {
        throw new Error(`LlamaParse upload failed: ${uploadRes.status} ${uploadRes.statusText}`);
      }

      const uploadData = await uploadRes.json() as { id: string };
      const jobId = uploadData.id;

      // Poll for job completion
      let status = 'PENDING';
      let attempts = 0;
      while (status !== 'SUCCESS' && attempts < 30) {
        await new Promise((r) => setTimeout(r, 2000));
        const statusRes = await fetch(`https://api.cloud.llamaindex.ai/api/parsing/job/${jobId}`, {
          headers: { Authorization: `Bearer ${this.apiKey}` },
        });
        const statusData = await statusRes.json() as { status: string };
        status = statusData.status;
        attempts++;
      }

      if (status !== 'SUCCESS') {
        throw new Error(`LlamaParse job did not succeed in time (status: ${status})`);
      }

      const resultRes = await fetch(`https://api.cloud.llamaindex.ai/api/parsing/job/${jobId}/result/markdown`, {
        headers: { Authorization: `Bearer ${this.apiKey}` },
      });
      const markdown = await resultRes.text();

      return {
        pages: [
          {
            pageNumber: 1,
            blocks: [{ text: markdown, type: 'paragraph' }],
            rawText: markdown,
          },
        ],
        rawMarkdown: markdown,
      };
    } catch (err: any) {
      logger.error('LlamaParse parsing failed; falling back to mock parser', {
        event: 'llamaparse_error',
        error: err.message,
      });
      return this.fallbackParser.parse(fileBuffer, fileName);
    }
  }
}
