// Core Domain Types for Policy-Linked Treatment Cost Estimation System

export type PolicyStatus = 
  | 'UPLOADING'
  | 'UPLOADED'
  | 'PARSING'
  | 'EXTRACTING'
  | 'VALIDATING'
  | 'READY'
  | 'FAILED';

export type CalculationStatus = 
  | 'CALCULATED'
  | 'INCOMPLETE'
  | 'INVALID'
  | 'ERROR';

export type ConfidenceLevel = 'HIGH' | 'MEDIUM' | 'LOW';

export type RuleType = 
  | 'SUM_INSURED'
  | 'ROOM_RENT_CAP'
  | 'COPAY'
  | 'PROCEDURE_SUBLIMIT'
  | 'DEDUCTIBLE'
  | 'EXCLUSION'
  | 'WAITING_PERIOD'
  | 'OTHER';

export type RoomRentRuleType = 
  | 'PERCENTAGE_OF_SUM_INSURED'
  | 'FIXED_AMOUNT_PER_DAY'
  | 'FIXED_AMOUNT_PER_HOSPITALIZATION'
  | 'NO_LIMIT'
  | 'UNKNOWN';

export type RoomCategory = 
  | 'GENERAL'
  | 'TWIN_SHARING'
  | 'SINGLE_PRIVATE'
  | 'DELUXE';

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface RuleSource {
  page: number;
  text: string;
  boundingBox: BoundingBox | null;
}

export interface PolicyMetadata {
  insurerName: string | null;
  policyName: string | null;
  policyNumber?: string | null;
  validFrom?: string | null;
  validTo?: string | null;
}

export interface SumInsuredRule {
  value: number | null;
  currency: string;
  source: RuleSource | null;
}

export interface RoomRentRule {
  type: RoomRentRuleType;
  percentage: number | null;
  fixedAmount: number | null;
  perDay: boolean | null;
  source: RuleSource | null;
  description?: string;
}

export interface CopayRule {
  percentage: number | null;
  applies: boolean | null;
  conditions?: string | null;
  source: RuleSource | null;
}

export interface SubLimitRule {
  procedureCode?: string | null;
  procedureName: string;
  amount: number | null;
  percentageOfSumInsured?: number | null;
  applies: boolean;
  source: RuleSource | null;
  description?: string;
}

export interface DeductibleRule {
  amount: number | null;
  applies: boolean;
  scope?: 'PER_CLAIM' | 'ANNUAL' | string;
  source: RuleSource | null;
}

export interface ExclusionRule {
  name: string;
  code?: string;
  description?: string;
  isPermanent: boolean;
  source: RuleSource | null;
}

export interface WaitingPeriodRule {
  condition: string;
  durationMonths: number | null;
  source: RuleSource | null;
}

export interface UnknownRule {
  category: string;
  reason: string;
  notes?: string;
}

export interface ExtractedPolicy {
  policyMetadata: PolicyMetadata;
  sumInsured: SumInsuredRule;
  roomRentRule: RoomRentRule;
  copay: CopayRule;
  subLimits: SubLimitRule[];
  deductibles: DeductibleRule[];
  exclusions: ExclusionRule[];
  waitingPeriods: WaitingPeriodRule[];
  unknownRules: UnknownRule[];
}

export interface DocumentBlock {
  id?: string;
  text: string;
  type: 'paragraph' | 'heading' | 'table' | 'list';
  boundingBox?: BoundingBox;
}

export interface DocumentPage {
  pageNumber: number;
  blocks: DocumentBlock[];
  rawText?: string;
}

export interface ParsedDocument {
  pages: DocumentPage[];
  rawMarkdown?: string;
  metadata?: {
    totalPages: number;
    title?: string;
    producer?: string;
  };
}

export interface Procedure {
  id: string;
  code: string;
  name: string;
  category: string;
  description?: string | null;
}

export interface HospitalCostScenario {
  id?: string;
  procedureCode: string;
  procedureName: string;
  city: string;
  roomCategory: RoomCategory;
  roomRate: number;
  stayDays: number;
  proportionateCosts: number;
  nonProportionateCosts: number;
  otherCosts: number;
  totalBill: number;
  currency: string;
  source?: string;
}

export interface TreatmentScenarioInput {
  procedureCode: string;
  roomCategory: RoomCategory;
  stayDays?: number;
  city?: string;
  customRoomRate?: number;
}

export interface CalculationTraceStep {
  step: string;
  title: string;
  formula: string;
  inputs: Record<string, any>;
  result: any;
  notes?: string;
}

export interface CitationReference {
  id?: string;
  ruleType: RuleType;
  ruleName: string;
  page: number;
  sourceText: string;
  boundingBox: BoundingBox | null;
}

export interface CategoricalConfidence {
  overall: ConfidenceLevel;
  policyExtraction: ConfidenceLevel;
  costMatching: ConfidenceLevel;
  calculation: ConfidenceLevel;
  reasons: string[];
}

export interface CalculationResult {
  allowedRoomRent: number;
  roomFactor: number;
  insurerProportionateShare: number;
  coveredRoomRent: number;
  baseInsurerLiability: number;
  deductible: number;
  copayPercentage: number;
  copayAmount: number;
  postCopayPay: number;
  procedureSubLimit: number | null;
  finalInsurerPay: number;
  outOfPocket: number;
}

export interface CostBreakdownItem {
  name: string;
  category: 'ROOM' | 'PROPORTIONATE' | 'NON_PROPORTIONATE' | 'OTHER' | 'ADJUSTMENT';
  hospitalBilled: number;
  insurerCovered: number;
  patientLiability: number;
  adjustmentReason?: string;
}

export interface CalculationResponse {
  calculationId: string;
  policyId: string;
  status: CalculationStatus;
  engineVersion: string;
  calculatedAt: string;
  scenario: {
    procedureCode: string;
    procedureName: string;
    roomCategory: RoomCategory;
    stayDays: number;
    city: string;
  };
  hospital: {
    totalBill: number;
    roomRate: number;
    stayDays: number;
    roomCost: number;
    proportionateCosts: number;
    nonProportionateCosts: number;
    otherCosts: number;
  };
  result: CalculationResult;
  breakdown: CostBreakdownItem[];
  calculationTrace: CalculationTraceStep[];
  citations: CitationReference[];
  confidence: CategoricalConfidence;
  warnings: string[];
  unknowns: string[];
}

// Provider Abstraction Interfaces
export interface DocumentParser {
  parse(fileBuffer: Buffer, fileName: string): Promise<ParsedDocument>;
}

export interface PolicyExtractionProvider {
  extract(document: ParsedDocument): Promise<ExtractedPolicy>;
}

export interface FileStorage {
  save(key: string, data: Buffer, contentType?: string): Promise<string>;
  get(key: string): Promise<Buffer>;
  delete(key: string): Promise<void>;
  getUrl?(key: string): string;
}

export interface CostRepository {
  findScenario(procedureCode: string, roomCategory: RoomCategory, city?: string): Promise<HospitalCostScenario | null>;
  listProcedures(): Promise<Procedure[]>;
  getProcedureByCode(code: string): Promise<Procedure | null>;
  listCostsForProcedure(procedureCode: string): Promise<HospitalCostScenario[]>;
}
