# auth_bearer.py - FastAPI dependency that reads and validates the Bearer token.

#
# Usage in any protected route:
#   @router.post("/chat")
#   def chat(request: ChatRequest, user_id: str = Depends(get_current_user)):
#       ...

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.auth.auth_handler import decode_token

# FastAPI's built-in Bearer token extractor
# Reads the "Authorization: Bearer <token>" header automatically
_bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> str:
    """
    FastAPI dependency — extracts and validates the JWT from the request header.

    Returns
    -------
    str  The user_id from the token payload.

    Raises
    ------
    HTTP 401  If the token is missing, expired, or invalid.
    """
    try:
        user_id = decode_token(credentials.credentials)
        return user_id
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
