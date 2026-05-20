# routes_auth.py - Authentication endpoints.
# Phase 4.5
#
# Endpoints:
#   POST /auth/register  — create account, return JWT
#   POST /auth/login     — verify credentials, return JWT

from fastapi import APIRouter, HTTPException, status

from app.auth.password import hash_password, verify_password
from app.auth.auth_handler import create_token
from app.db.users import create_user, get_user_by_username
from app.models.auth_models import RegisterRequest, LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest):
    """
    Register a new user account.

    - Checks username is not already taken
    - Hashes the password with bcrypt
    - Stores user in Supabase
    - Returns a JWT token (user is logged in immediately after registering)
    """
    # Check username availability
    existing = get_user_by_username(request.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken. Please choose a different one.",
        )

    # Hash password — never store plain text
    password_hash = hash_password(request.password)

    # Insert user into DB
    try:
        user = create_user(request.username, password_hash)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {e}",
        )

    # Return JWT so user is immediately authenticated
    token = create_token(user["id"])
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):
    """
    Login with username and password.

    - Fetches user from Supabase
    - Verifies password against stored bcrypt hash
    - Returns a JWT token on success
    """
    user = get_user_by_username(request.username)

    # Use the same error for both "user not found" and "wrong password"
    # to avoid leaking which usernames exist
    if not user or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    token = create_token(user["id"])
    return {"access_token": token, "token_type": "bearer"}
