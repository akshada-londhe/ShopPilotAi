"""FastAPI router for user authentication."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, field_validator

from app import auth_users

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Request / Response models ─────────────────────────────────────────────────
class SignUpRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty.")
        return v

    @field_validator("password")
    @classmethod
    def password_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        return v


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    user_id: str
    name: str
    email: str
    token: str


class MeResponse(BaseModel):
    user_id: str
    name: str
    email: str
    created_at: str | None = None


# ── Routes ────────────────────────────────────────────────────────────────────
@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(body: SignUpRequest) -> AuthResponse:
    """Create a new user account and return a JWT."""
    try:
        result = auth_users.create_user(body.name, str(body.email), body.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create account. Please try again.",
        ) from exc
    return AuthResponse(**result)


@router.post("/signin", response_model=AuthResponse)
def signin(body: SignInRequest) -> AuthResponse:
    """Verify credentials and return a JWT."""
    try:
        result = auth_users.authenticate_user(str(body.email), body.password)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sign in failed. Please try again.",
        ) from exc
    return AuthResponse(**result)


@router.get("/me", response_model=MeResponse)
def me(request: Request) -> MeResponse:
    """Return the authenticated user's profile from their JWT."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header.",
        )
    token = auth_header.removeprefix("Bearer ").strip()
    user = auth_users.get_user_by_token(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )
    return MeResponse(**user)
