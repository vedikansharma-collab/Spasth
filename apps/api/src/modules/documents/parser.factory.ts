import { DocumentParser } from '@policy-estimator/types';
import { config } from '../../config/config.js';
import { MockDocumentParser } from './mock-parser.js';
import { LlamaParseDocumentParser } from './llamaparse-parser.js';

export function getDocumentParser(): DocumentParser {
  if (config.demoMode || !config.parser.llamaparseApiKey) {
    return new MockDocumentParser();
  }
  return new LlamaParseDocumentParser(config.parser.llamaparseApiKey);
}
