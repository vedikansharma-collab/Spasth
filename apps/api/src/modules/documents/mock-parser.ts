import fs from 'fs';
import path from 'path';
import { DocumentParser, ParsedDocument, DocumentPage, DocumentBlock } from '@policy-estimator/types';
import { logger } from '../../common/logging/logger.js';

export class MockDocumentParser implements DocumentParser {
  async parse(fileBuffer: Buffer, fileName: string): Promise<ParsedDocument> {
    logger.info('Parsing document using MockDocumentParser', { event: 'document_parse_started', details: { fileName } });

    // Load reference sample policy markdown
    const mdPath = path.resolve(process.cwd(), '../../data/sample-policy-markdown.md');
    const localMdPath = path.resolve(process.cwd(), 'data/sample-policy-markdown.md');
    
    let rawMarkdown = '';
    if (fs.existsSync(mdPath)) {
      rawMarkdown = fs.readFileSync(mdPath, 'utf-8');
    } else if (fs.existsSync(localMdPath)) {
      rawMarkdown = fs.readFileSync(localMdPath, 'utf-8');
    } else {
      rawMarkdown = `# Policy Document: ${fileName}\n\n<!-- PAGE: 1 -->\nBasic policy schedule.\n\n<!-- PAGE: 5 -->\nSum Insured: INR 5,00,000\n\n<!-- PAGE: 12 -->\nRoom rent capped at 1% of Sum Insured per day.`;
    }

    // Split markdown into pages by <!-- PAGE: X --> markers
    const pageSegments = rawMarkdown.split(/<!--\s*PAGE:\s*(\d+)\s*-->/gi);
    const pages: DocumentPage[] = [];

    // The split results in [pre-text, pageNum1, text1, pageNum2, text2, ...]
    if (pageSegments.length > 1) {
      for (let i = 1; i < pageSegments.length; i += 2) {
        const pageNumber = parseInt(pageSegments[i], 10);
        const pageText = pageSegments[i + 1]?.trim() || '';
        const lines = pageText.split('\n').filter(l => l.trim().length > 0);

        const blocks: DocumentBlock[] = [];
        let yOffset = 100;

        for (const line of lines) {
          let type: 'paragraph' | 'heading' | 'table' | 'list' = 'paragraph';
          if (line.startsWith('#')) {
            type = 'heading';
          } else if (line.startsWith('- ') || line.startsWith('* ') || /^\d+\./.test(line)) {
            type = 'list';
          } else if (line.includes('|')) {
            type = 'table';
          }

          blocks.push({
            text: line.replace(/^#+\s*/, ''),
            type,
            boundingBox: {
              x: 72,
              y: yOffset,
              width: 480,
              height: type === 'heading' ? 30 : 20,
            },
          });
          yOffset += type === 'heading' ? 36 : 24;
        }

        pages.push({
          pageNumber,
          blocks,
          rawText: pageText,
        });
      }
    } else {
      // Fallback single page
      pages.push({
        pageNumber: 1,
        blocks: [
          {
            text: rawMarkdown,
            type: 'paragraph',
            boundingBox: { x: 72, y: 100, width: 480, height: 200 },
          },
        ],
        rawText: rawMarkdown,
      });
    }

    logger.info('Document parsed successfully into structured pages', {
      event: 'document_parse_completed',
      details: { totalPages: pages.length },
    });

    return {
      pages,
      rawMarkdown,
      metadata: {
        totalPages: pages.length,
        title: fileName,
      },
    };
  }
}
