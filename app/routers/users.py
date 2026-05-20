"""User authentication and management endpoints."""

import re
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.auth import jwt_handler, password as password_lib
from app.auth.dependencies import CurrentUser, get_current_user
from app.config import settings
from app.database.connection import get_db
from app.database.crud import create_user, delete_summary, get_user_by_email

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    """Request model for user registration."""

    email: EmailStr
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    """Request model for user login."""

    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Response model for successful login."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """Response model for user info."""

    id: int
    email: str
    is_active: bool


def validate_password(password: str) -> tuple[bool, str]:
    """Validate password requirements."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"

    return True, ""


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
) -> UserResponse:
    """Register a new user account."""
    # Validate password
    valid, error_msg = validate_password(request.password)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_msg,
        )

    # Check if user already exists
    existing_user = get_user_by_email(db, request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    # Hash password and create user
    hashed_password = password_lib.hash_password(request.password)
    user = create_user(db, request.email, hashed_password)

    return UserResponse(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
) -> LoginResponse:
    """Authenticate user and return JWT token."""
    # Get user
    user = get_user_by_email(db, request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    # Verify password
    if not password_lib.verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Create access token
    access_token = jwt_handler.create_access_token(
        data={"user_id": user.id, "email": user.email},
        expires_delta=timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: CurrentUser = Depends(get_current_user),
) -> UserResponse:
    """Get current user info."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        is_active=current_user.is_active,
    )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete the current user account."""
    from app.database.crud import get_user_by_id

    user = get_user_by_id(db, current_user.id)
    if user:
        # Delete all user summaries first
        delete_summary(db, request_id="", user_id=user.id)
        # Then delete user (this would need additional logic in crud)
        db.delete(user)
        db.commit()