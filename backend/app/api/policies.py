from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, status

from app.services.policy_service import PolicyService
from app.schemas.policy import (
    PolicyUploadResponse,
    PolicyDetailResponse,
    PolicySummaryResponse,
    PolicyPageSchema,
    PolicyAskRequest,
    PolicyAskResponse
)

router = APIRouter(prefix="/policies", tags=["Policies"])

@router.post("/upload", response_model=PolicyUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_policy(file: UploadFile = File(...)):
    """
    POST /api/policies/upload
    Accepts an insurance policy PDF, extracts page-by-page text preserving page numbers,
    and stores processed metadata in SQLite.
    """
    return PolicyService.upload_and_process_policy(file)

@router.get("", response_model=List[PolicySummaryResponse])
def list_policies():
    """
    GET /api/policies
    Lists all uploaded policy documents with metadata summary.
    """
    return PolicyService.get_all_policies()

@router.get("/{policy_id}", response_model=PolicyDetailResponse)
def get_policy_detail(policy_id: str):
    """
    GET /api/policies/{policy_id}
    Retrieves policy metadata and all preserved page-by-page extracted text chunks.
    """
    policy = PolicyService.get_policy(policy_id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy with ID {policy_id} not found."
        )
    return policy

@router.get("/{policy_id}/pages/{page_number}", response_model=PolicyPageSchema)
def get_policy_page(policy_id: str, page_number: int):
    """
    GET /api/policies/{policy_id}/pages/{page_number}
    Retrieves the preserved text content of a specific page number.
    """
    policy = PolicyService.get_policy(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    page = next((p for p in policy.get("pages", []) if p["page_number"] == page_number), None)
    if not page:
        raise HTTPException(
            status_code=404,
            detail=f"Page {page_number} not found in policy (total pages: {policy.get('page_count')})."
        )
    return page

@router.get("/canonical/current")
def get_current_canonical_policy():
    """
    GET /api/policies/canonical/current
    Returns the current canonical policy JSON extracted and exported from the most recent policy.
    """
    data = PolicyService.get_canonical_json()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No canonical policy JSON available yet. Please upload a policy first."
        )
    return data

@router.get("/{policy_id}/canonical")
def get_policy_canonical(policy_id: str):
    """
    GET /api/policies/{policy_id}/canonical
    Retrieves the canonical structured JSON representation for a specific policy ID.
    """
    data = PolicyService.get_canonical_json(policy_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy with ID '{policy_id}' not found."
        )
    return data

@router.post("/{policy_id}/ask", response_model=PolicyAskResponse)
def ask_policy(policy_id: str, request: PolicyAskRequest):
    """
    POST /api/policies/{policy_id}/ask
    Answers policy questions grounded in extracted policy document text and preserved page citations.
    """
    result = PolicyService.answer_policy_query(
        policy_id, 
        request.query, 
        request.conversation_id, 
        request.history
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy with ID '{policy_id}' not found."
        )
    return result
