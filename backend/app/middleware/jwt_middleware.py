"""
JWT Authentication Middleware — Issue 4 fix.
Extracts user email from JWT token in the Authorization header.
Falls back to X-User-Email header for backward compatibility.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from fastapi.responses import JSONResponse
from app.database.jwt_utils import decode_access_token

# Routes that do NOT require authentication
PUBLIC_PREFIXES = [
    "/api/auth/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/uploads/",
]


class JWTMiddleware(BaseHTTPMiddleware):
    """
    Middleware that:
    1. Checks for Authorization: Bearer <token>
    2. Decodes it, extracts email → sets request.state.user_email
    3. Falls back to X-User-Email header if no JWT (backward compat)
    4. Skips auth for public routes
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip auth for public routes
        if any(path.startswith(prefix) for prefix in PUBLIC_PREFIXES):
            # Still extract user email if available (for /api/auth endpoints that need it)
            self._extract_user_email(request)
            return await call_next(request)

        # Extract user email from JWT or header
        email = self._extract_user_email(request)

        # For non-public routes, we still allow requests through
        # (the individual endpoints can check request.state.user_email)
        # This keeps backward compatibility during the transition
        response = await call_next(request)
        return response

    def _extract_user_email(self, request: Request) -> str:
        """Extract user email from JWT token or X-User-Email header."""
        email = "default"

        # Priority 1: JWT Bearer token
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            payload = decode_access_token(token)
            if payload and "sub" in payload:
                email = payload["sub"]
                request.state.user_email = email
                return email

        # Priority 2: X-User-Email header (backward compat)
        x_email = request.headers.get("x-user-email", "")
        if x_email:
            email = x_email

        request.state.user_email = email
        return email
