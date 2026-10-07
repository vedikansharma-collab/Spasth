from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Any

class PolicyPageSchema(BaseModel):
    page_number: int
    char_count: int
    word_count: int
    content: str

    class Config:
        from_attributes = True

class PolicyUploadResponse(BaseModel):
    policy_id: str
    original_filename: str
    file_size_bytes: int
    page_count: int
    extraction_status: str
    uploaded_at: datetime
    message: str

    class Config:
        from_attributes = True

class PolicyDetailResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_size_bytes: int
    page_count: int
    uploaded_at: datetime
    extraction_status: str
    error_message: Optional[str] = None
    pages: List[PolicyPageSchema] = []
    rules: List[Dict[str, Any]] = []

    class Config:
        from_attributes = True

class PolicySummaryResponse(BaseModel):
    id: str
    original_filename: str
    file_size_bytes: int
    page_count: int
    uploaded_at: datetime
    extraction_status: str

    class Config:
        from_attributes = True
