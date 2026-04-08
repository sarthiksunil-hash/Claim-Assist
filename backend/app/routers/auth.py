"""
Authentication Router - Signup, Login, OTP Verification, Password Reset
Uses UserRepository for unified Supabase/SQLite data access (Issue 5 DRY fix).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import hashlib
import random
import secrets
import os
import traceback

from app.database.db import get_db
from app.database.user_repo import UserRepository
from app.database.jwt_utils import create_access_token
from app.services.email_service import send_otp_email, send_password_reset_email

router = APIRouter()

FRONTEND_URL = os.getenv("CORS_ORIGINS", "http://localhost:3000")


# ──── Pydantic Schemas ────────────────────────────────────────

class SignupRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password (min 6 chars)")
    full_name: str = Field(..., description="User's full name")

class LoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")

class OTPVerifyRequest(BaseModel):
    email: str = Field(..., description="User email address")
    otp: str = Field(..., description="6-digit OTP code")

class ResendOTPRequest(BaseModel):
    email: str = Field(..., description="User email address")

class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., description="Registered email address")

class ResetPasswordRequest(BaseModel):
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=6, description="New password (min 6 chars)")

class AuthResponse(BaseModel):
    success: bool
    message: str
    user: Optional[dict] = None
    requires_otp: bool = False
    token: Optional[str] = None


# ──── Utility Functions ───────────────────────────────────────

def hash_password(password: str) -> str:
    salt = "claimassist_salt_2026"
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

def generate_otp() -> str:
    return str(random.randint(100000, 999999))


def _send_otp_email_safe(email: str, otp_code: str, user_name: str):
    """Send OTP email, logging errors but not failing."""
    try:
        send_otp_email(to_email=email, otp_code=otp_code, user_name=user_name)
    except Exception as e:
        print(f"[AUTH] Email send failed (non-fatal): {e}")
    print(f"[AUTH] OTP for {email}: {otp_code}")


# ═══════════════════════════════════════════════════════════════
#  AUTH ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.post("/signup", response_model=AuthResponse)
async def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    try:
        repo = UserRepository(db)
        pw_hash = hash_password(request.password)

        existing = repo.find_user(request.email)
        if existing:
            if existing.get("is_verified"):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An account with this email already exists. Please login instead."
                )
            else:
                # Unverified — update and resend OTP
                repo.update_user(request.email, {
                    "full_name": request.full_name,
                    "password_hash": pw_hash,
                })
                otp = generate_otp()
                repo.store_otp(request.email, otp)
                _send_otp_email_safe(request.email, otp, request.full_name)
                return AuthResponse(
                    success=True,
                    message=f"A verification code has been sent to {request.email}.",
                    requires_otp=True,
                    user={"email": request.email, "full_name": request.full_name}
                )

        repo.create_user(request.email, pw_hash, request.full_name)
        otp = generate_otp()
        repo.store_otp(request.email, otp)
        _send_otp_email_safe(request.email, otp, request.full_name)

        return AuthResponse(
            success=True,
            message=f"Account created! A verification code has been sent to {request.email}.",
            requires_otp=True,
            user={"email": request.email, "full_name": request.full_name}
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"[AUTH] Signup error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")


@router.post("/verify-otp", response_model=AuthResponse)
async def verify_otp_endpoint(request: OTPVerifyRequest, db: Session = Depends(get_db)):
    """Verify OTP."""
    repo = UserRepository(db)

    result = repo.verify_otp(request.email, request.otp)

    if result == "expired":
        raise HTTPException(status_code=400, detail="OTP has expired. Please request a new one.")
    if result is None:
        raise HTTPException(status_code=400, detail="Invalid OTP. Please check and try again.")

    # OTP is valid — mark user as verified
    repo.update_user(request.email, {"is_verified": True})
    repo.delete_otps(request.email)

    user = repo.find_user(request.email)
    full_name = user.get("full_name", "") if user else ""
    token = create_access_token(request.email, full_name)
    return AuthResponse(
        success=True,
        message="Email verified successfully! You can now login.",
        user={"email": request.email, "full_name": full_name},
        token=token,
    )


@router.post("/resend-otp", response_model=AuthResponse)
async def resend_otp_endpoint(request: ResendOTPRequest, db: Session = Depends(get_db)):
    """Resend OTP."""
    repo = UserRepository(db)

    user = repo.find_user(request.email)
    if not user:
        raise HTTPException(status_code=404, detail="No account found with this email.")
    if user.get("is_verified"):
        raise HTTPException(status_code=400, detail="Account already verified. Please login.")

    otp = generate_otp()
    repo.store_otp(request.email, otp)
    _send_otp_email_safe(request.email, otp, user.get("full_name", ""))

    return AuthResponse(
        success=True,
        message=f"A new verification code has been sent to {request.email}.",
        requires_otp=True,
    )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login with email and password."""
    try:
        repo = UserRepository(db)
        pw_hash = hash_password(request.password)

        user = repo.find_user(request.email)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="No account found with this email. Please sign up first."
            )

        if not user.get("is_verified"):
            otp = generate_otp()
            repo.store_otp(request.email, otp)
            _send_otp_email_safe(request.email, otp, user.get("full_name", ""))
            return AuthResponse(
                success=False,
                message="Email not verified. A verification code has been sent.",
                requires_otp=True,
                user={"email": request.email, "full_name": user.get("full_name", "")}
            )

        if user.get("password_hash") != pw_hash:
            raise HTTPException(status_code=401, detail="Incorrect password. Please try again.")

        repo.update_user(request.email, {"last_login": datetime.utcnow().isoformat()})

        token = create_access_token(request.email, user.get("full_name", ""))
        print(f"[AUTH] Login successful: {request.email}")
        return AuthResponse(
            success=True,
            message="Login successful! Welcome back.",
            user={
                "email": user["email"],
                "full_name": user.get("full_name", ""),
                "last_login": user.get("last_login", str(datetime.utcnow())),
            },
            token=token,
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"[AUTH] Login error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


# ──── Forgot Password / Reset Password ───────────────────────

@router.post("/forgot-password", response_model=AuthResponse)
async def forgot_password_endpoint(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Send password reset link."""
    repo = UserRepository(db)

    user = repo.find_user(request.email)
    if user:
        token = secrets.token_urlsafe(48)
        repo.store_reset_token(request.email, token)

        reset_link = f"{FRONTEND_URL}/login?reset_token={token}"
        send_password_reset_email(
            to_email=request.email,
            reset_link=reset_link,
            user_name=user.get("full_name", ""),
        )
        print(f"[AUTH] Password reset link sent to {request.email}")

    # Always return success (don't leak whether email exists)
    return AuthResponse(
        success=True,
        message="If an account with this email exists, a password reset link has been sent.",
    )


@router.post("/reset-password", response_model=AuthResponse)
async def reset_password_endpoint(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using token."""
    repo = UserRepository(db)

    token_data = repo.find_reset_token(request.token)
    if not token_data:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link.")
    if token_data.get("_expired"):
        raise HTTPException(status_code=400, detail="Reset link expired. Please request a new one.")

    token_email = token_data["email"]
    new_hash = hash_password(request.new_password)

    repo.update_user(token_email, {"password_hash": new_hash, "is_verified": True})
    repo.consume_reset_token(token_email)

    return AuthResponse(
        success=True,
        message="Password reset successfully! You can now login with your new password.",
    )
