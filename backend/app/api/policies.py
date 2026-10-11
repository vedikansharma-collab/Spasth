from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.core.auth import get_current_user, get_current_user_optional, verify_policy_access
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
def upload_policy(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    POST /api/policies/upload
    Requires authentication. Accepts an insurance policy PDF, extracts page-by-page text,
    stores policy with owner_id = current_user.id and is_public = False.
    """
    return PolicyService.upload_and_process_policy(
        file,
        owner_id=current_user.id,
        is_public=False
    )

@router.get("", response_model=List[PolicySummaryResponse])
def list_policies(current_user: Optional[User] = Depends(get_current_user_optional)):
    """
    GET /api/policies
    Lists policies accessible to caller.
    If authenticated: caller's own private policies + public demo policies (or all if admin).
    If unauthenticated: only public demo policies.
    """
    return PolicyService.get_all_policies(user=current_user)

@router.get("/{policy_id}", response_model=PolicyDetailResponse)
def get_policy_detail(
    policy_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    GET /api/policies/{policy_id}
    Retrieves policy metadata and pages. Enforces ownership authorization check.
    """
    # 1. Authorization check: public or owned by current_user
    verify_policy_access(policy_id, current_user, db)

    # 2. Fetch policy details
    policy = PolicyService.get_policy(policy_id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy with ID {policy_id} not found."
        )
    return policy

@router.get("/{policy_id}/pages/{page_number}", response_model=PolicyPageSchema)
def get_policy_page(
    policy_id: str,
    page_number: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    GET /api/policies/{policy_id}/pages/{page_number}
    Retrieves preserved text of a specific page number. Enforces authorization.
    """
    verify_policy_access(policy_id, current_user, db)

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
def get_current_canonical_policy(current_user: Optional[User] = Depends(get_current_user_optional)):
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
def get_policy_canonical(
    policy_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    GET /api/policies/{policy_id}/canonical
    Retrieves canonical structured JSON. Enforces authorization.
    """
    verify_policy_access(policy_id, current_user, db)

    data = PolicyService.get_canonical_json(policy_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy with ID '{policy_id}' not found."
        )
    return data

@router.post("/{policy_id}/ask", response_model=PolicyAskResponse)
def ask_policy(
    policy_id: str,
    request: PolicyAskRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    POST /api/policies/{policy_id}/ask
    Answers policy questions grounded in extracted policy document text and citations.
    CRITICAL SECURITY: Verifies policy access authorization BEFORE initiating pgvector search or Gemini query.
    """
    # 1. Authorization Boundary Check
    verify_policy_access(policy_id, current_user, db)

    # 2. RAG Retrieval & Answer Generation (Retrieval Boundary is also policy_id isolated)
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
