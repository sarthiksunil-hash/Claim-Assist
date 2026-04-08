"""
UserRepository — unified data access for auth operations.
Picks Supabase or SQLite at init time. All helpers use a single `_sb`
reference instead of calling get_supabase() 9+ times.

This eliminates the DRY violation described in Issue 5.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session
from app.database.db import get_supabase, User, OTPRecord, PasswordResetToken


class UserRepository:
    """Unified data access for auth operations."""

    def __init__(self, db: Session):
        self.db = db
        self._sb = get_supabase()  # Single check — None if unavailable
        self.use_supabase = self._sb is not None

    # ────────────────────────────────────────────────────────
    # USER CRUD
    # ────────────────────────────────────────────────────────

    def find_user(self, email: str) -> Optional[Dict[str, Any]]:
        """Find a user by email. Returns dict (Supabase) or None."""
        if self._sb:
            try:
                result = self._sb.table("users").select("*").eq("email", email).execute()
                if result.data and len(result.data) > 0:
                    return result.data[0]
            except Exception as e:
                print(f"[UserRepo] Supabase find_user error: {e}")

        # SQLite fallback
        user = self.db.query(User).filter(User.email == email).first()
        if user:
            return {
                "email": user.email,
                "password_hash": user.password_hash,
                "full_name": user.full_name,
                "is_verified": user.is_verified,
                "last_login": str(user.last_login) if user.last_login else None,
                "_source": "sqlite",
            }
        return None

    def create_user(self, email: str, password_hash: str, full_name: str) -> Optional[Dict]:
        """Create a user. Writes to Supabase + SQLite for sync."""
        created = None
        if self._sb:
            try:
                result = self._sb.table("users").insert({
                    "email": email,
                    "password_hash": password_hash,
                    "full_name": full_name,
                    "is_verified": False,
                    "created_at": datetime.utcnow().isoformat(),
                }).execute()
                if result.data:
                    created = result.data[0]
                    print(f"[UserRepo] User created in Supabase: {email}")
            except Exception as e:
                print(f"[UserRepo] Supabase create_user error: {e}")

        # Always sync to SQLite
        try:
            local = self.db.query(User).filter(User.email == email).first()
            if not local:
                local = User(
                    email=email,
                    password_hash=password_hash,
                    full_name=full_name,
                    is_verified=False,
                )
                self.db.add(local)
                self.db.commit()
        except Exception as e:
            print(f"[UserRepo] SQLite sync error (non-fatal): {e}")
            self.db.rollback()

        return created or {"email": email, "full_name": full_name, "_source": "sqlite"}

    def update_user(self, email: str, updates: dict) -> bool:
        """Update user fields in both Supabase and SQLite."""
        if self._sb:
            try:
                self._sb.table("users").update(updates).eq("email", email).execute()
            except Exception as e:
                print(f"[UserRepo] Supabase update_user error: {e}")

        # SQLite sync
        try:
            user = self.db.query(User).filter(User.email == email).first()
            if user:
                for key, val in updates.items():
                    if hasattr(user, key):
                        setattr(user, key, val)
                self.db.commit()
        except Exception as e:
            print(f"[UserRepo] SQLite update error: {e}")
            self.db.rollback()
        return True

    # ────────────────────────────────────────────────────────
    # OTP
    # ────────────────────────────────────────────────────────

    def store_otp(self, email: str, otp_code: str) -> bool:
        """Store an OTP for email verification."""
        expires = datetime.utcnow() + timedelta(minutes=10)

        if self._sb:
            try:
                self._sb.table("otp_records").delete().eq("email", email).execute()
                self._sb.table("otp_records").insert({
                    "email": email,
                    "otp_code": otp_code,
                    "created_at": datetime.utcnow().isoformat(),
                    "expires_at": expires.isoformat(),
                }).execute()
            except Exception as e:
                print(f"[UserRepo] Supabase store_otp error: {e}")

        # SQLite sync
        try:
            self.db.query(OTPRecord).filter(OTPRecord.email == email).delete()
            otp_rec = OTPRecord(
                email=email,
                otp_code=otp_code,
                expires_at=expires,
            )
            self.db.add(otp_rec)
            self.db.commit()
        except Exception as e:
            print(f"[UserRepo] SQLite OTP store error: {e}")
            self.db.rollback()

        return True

    def verify_otp(self, email: str, otp: str) -> Optional[str]:
        """
        Verify OTP. Returns:
          - "valid"   if OTP matches and is not expired
          - "expired" if OTP matches but is expired
          - None      if OTP not found
        """
        # Try Supabase first
        if self._sb:
            try:
                result = self._sb.table("otp_records").select("*") \
                    .eq("email", email).eq("otp_code", otp).execute()
                if result.data and len(result.data) > 0:
                    record = result.data[0]
                    expires_str = record["expires_at"].replace("Z", "+00:00")
                    expires_at = datetime.fromisoformat(expires_str)
                    if expires_at.tzinfo is None:
                        expires_at = expires_at.replace(tzinfo=timezone.utc)
                    if expires_at < datetime.now(timezone.utc):
                        self.delete_otps(email)
                        return "expired"
                    return "valid"
            except Exception as e:
                print(f"[UserRepo] Supabase verify_otp error: {e}")

        # SQLite fallback
        otp_record = (
            self.db.query(OTPRecord)
            .filter(OTPRecord.email == email, OTPRecord.otp_code == otp)
            .first()
        )
        if not otp_record:
            return None
        if otp_record.expires_at < datetime.utcnow():
            self.db.delete(otp_record)
            self.db.commit()
            return "expired"
        return "valid"

    def delete_otps(self, email: str):
        """Delete all OTPs for an email."""
        if self._sb:
            try:
                self._sb.table("otp_records").delete().eq("email", email).execute()
            except Exception:
                pass
        try:
            self.db.query(OTPRecord).filter(OTPRecord.email == email).delete()
            self.db.commit()
        except Exception:
            self.db.rollback()

    # ────────────────────────────────────────────────────────
    # PASSWORD RESET TOKENS
    # ────────────────────────────────────────────────────────

    def store_reset_token(self, email: str, token: str) -> bool:
        """Store a password reset token."""
        expires = datetime.utcnow() + timedelta(minutes=30)

        if self._sb:
            try:
                self._sb.table("password_reset_tokens").delete().eq("email", email).execute()
                self._sb.table("password_reset_tokens").insert({
                    "email": email,
                    "token": token,
                    "created_at": datetime.utcnow().isoformat(),
                    "expires_at": expires.isoformat(),
                    "used": False,
                }).execute()
            except Exception as e:
                print(f"[UserRepo] Supabase store_reset_token error: {e}")

        # SQLite sync
        try:
            self.db.query(PasswordResetToken).filter(
                PasswordResetToken.email == email
            ).delete()
            reset_token = PasswordResetToken(
                email=email,
                token=token,
                expires_at=expires,
            )
            self.db.add(reset_token)
            self.db.commit()
        except Exception as e:
            print(f"[UserRepo] SQLite reset token store error: {e}")
            self.db.rollback()
        return True

    def find_reset_token(self, token: str) -> Optional[Dict]:
        """Find a valid (unused) reset token."""
        if self._sb:
            try:
                result = self._sb.table("password_reset_tokens").select("*") \
                    .eq("token", token).eq("used", False).execute()
                if result.data and len(result.data) > 0:
                    record = result.data[0]
                    expires_str = record["expires_at"].replace("Z", "+00:00")
                    expires_at = datetime.fromisoformat(expires_str)
                    if expires_at.tzinfo is None:
                        expires_at = expires_at.replace(tzinfo=timezone.utc)
                    if expires_at < datetime.now(timezone.utc):
                        return {"email": record["email"], "_expired": True}
                    return record
            except Exception as e:
                print(f"[UserRepo] Supabase find_reset_token error: {e}")

        # SQLite fallback
        token_rec = (
            self.db.query(PasswordResetToken)
            .filter(PasswordResetToken.token == token, PasswordResetToken.used == False)
            .first()
        )
        if not token_rec:
            return None
        if token_rec.expires_at < datetime.utcnow():
            token_rec.used = True
            self.db.commit()
            return {"email": token_rec.email, "_expired": True}
        return {"email": token_rec.email, "token": token_rec.token}

    def consume_reset_token(self, email: str):
        """Mark all reset tokens as used / delete them."""
        if self._sb:
            try:
                self._sb.table("password_reset_tokens").delete().eq("email", email).execute()
            except Exception:
                pass
        try:
            self.db.query(PasswordResetToken).filter(
                PasswordResetToken.email == email
            ).delete()
            self.db.commit()
        except Exception:
            self.db.rollback()
