from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class EstimateRequest(BaseModel):
    policy_id: str
    procedure: str
    city: str
    room_category: str = "Standard"
    condition: Optional[str] = None

class CostRange(BaseModel):
    min: float
    max: float

class AppliedRuleSchema(BaseModel):
    rule_name: str
    description: str
    impact: str

class CitationSchema(BaseModel):
    rule: str
    details: str
    page: int
    clause: str
    source_text: str

class EstimateResponse(BaseModel):
    policy_id: str
    procedure: str
    city: str
    room_category: str
    treatment_cost_range: CostRange
    eligible_amount_range: CostRange
    estimated_coverage_range: CostRange
    estimated_oop_range: CostRange
    applied_rules: List[AppliedRuleSchema]
    citations: List[CitationSchema]
    confidence: str
    confidence_reason: Optional[str] = "Evidence grounded"
    data_source: str
    data_type: str
    status: Optional[str] = "SUCCESS"

class TreatmentsResponse(BaseModel):
    procedures: List[str]
    cities: List[str]
    room_categories: List[str]
