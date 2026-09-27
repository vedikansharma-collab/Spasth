import { PolicyExtractionProvider } from '@policy-estimator/types';
import { config } from '../../config/config.js';
import { MockPolicyExtractor } from './mock-extractor.js';
import { OpenAIPolicyExtractor } from './openai-extractor.js';

export function getPolicyExtractor(): PolicyExtractionProvider {
  if (config.demoMode || !config.ai.openaiApiKey) {
    return new MockPolicyExtractor();
  }
  return new OpenAIPolicyExtractor(config.ai.openaiApiKey, config.ai.openaiModel, config.ai.openaiBaseUrl);
}
