from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union

class EstimateRequest(BaseModel):
    policy_id: str
    procedure: Optional[str] = None
    treatment: Optional[str] = None
    city: str
    room_category: str = "Standard"
    condition: Optional[str] = None
    scenario: Optional[Dict[str, Any]] = None

    def get_effective_procedure(self) -> str:
        return self.procedure or self.treatment or "Appendectomy"

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
    page: Union[int, str]
    clause: Optional[str] = "N/A"
    source_text: str
    section: Optional[str] = None

class EstimateResponse(BaseModel):
    policy_id: str
    procedure: str
    city: str
    room_category: str
    treatment_cost_range: CostRange
    eligible_amount_range: CostRange
    estimated_coverage_range: CostRange
    estimated_oop_range: CostRange
    applied_rules: List[AppliedRuleSchema] = []
    citations: List[CitationSchema] = []
    confidence: str
    confidence_reason: Optional[str] = "Evidence grounded"
    data_source: str
    data_type: str = "synthetic"
    status: Optional[str] = "calculated"

    # Phase 9 structured breakdown fields
    treatment_cost: Optional[CostRange] = None
    applicable_sublimit: Optional[float] = None
    eligible_amount: Optional[CostRange] = None
    copay_percent: Optional[float] = None
    copay_amount: Optional[CostRange] = None
    insurance_contribution: Optional[CostRange] = None
    patient_payable: Optional[CostRange] = None
    rules_applied: Optional[List[AppliedRuleSchema]] = None
    evidence: Optional[List[CitationSchema]] = None
    coverage_checks: Optional[Dict[str, Any]] = None

class TreatmentsResponse(BaseModel):
    procedures: List[str]
    cities: List[str]
    room_categories: List[str]
