import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User
from app.models.policy import Policy
from app.core.security import decode_access_token

logger = logging.getLogger(__name__)

security_bearer = HTTPBearer(auto_error=False)

def get_current_user_optional(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Extracts and validates JWT Bearer token if present.
    Returns User if authenticated, None if no Authorization header provided.
    Raises 401 if an invalid or expired token is provided.
    """
    if not auth or not auth.credentials:
        return None
    token = auth.credentials
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing user identity subject (sub)",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User identity in token no longer exists",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"JWT token decoding/validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(
    user: Optional[User] = Depends(get_current_user_optional)
) -> User:
    """
    Enforces authentication. Requires a valid JWT token.
    Raises 401 if unauthenticated.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def verify_policy_access(
    policy_id: str,
    user: Optional[User],
    db: Session
) -> Policy:
    """
    Core Authorization Engine:
    - Verifies whether policy exists (404 if missing).
    - Checks whether policy is public (permitted to all).
    - Checks whether user is authenticated (401 if private and unauthenticated).
    - Checks ownership: user must be owner or admin (403 if unauthorized).
    """
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy with ID '{policy_id}' not found."
        )

    # 1. Public Policy Check
    if policy.is_public:
        return policy

    # 2. Private Policy: User must be authenticated
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access this policy",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Ownership / Role Authorization Check
    if user.role == "admin" or (policy.owner_id and policy.owner_id == user.id):
        return policy

    # 4. Denied: Authenticated, but not owner and not admin
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied: You do not have permission to view or query this private policy."
    )
