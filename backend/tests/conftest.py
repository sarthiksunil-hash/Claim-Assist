"""
Shared pytest fixtures for ClaimAssist AI test suite.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
import io
import os
import sys

# Ensure backend root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── Patch Supabase and heavy deps before app import ──
# This prevents actual DB/Groq/Ollama calls during tests
_mock_supabase = MagicMock()
_mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
_mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = []
_mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [{"id": 1}]
_mock_supabase.table.return_value.delete.return_value.eq.return_value.execute.return_value.data = []
_mock_supabase.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value.data = []


@pytest.fixture(scope="session", autouse=True)
def patch_supabase():
    """Patch Supabase client for all tests — no real DB calls."""
    with patch("app.database.db.supabase", _mock_supabase):
        with patch("app.database.db.get_supabase", return_value=_mock_supabase):
            with patch("app.database.supabase_repo._sb", return_value=_mock_supabase):
                yield _mock_supabase


@pytest.fixture(scope="session")
def client():
    """FastAPI test client (shared across session)."""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def user_a_headers():
    """Headers for test user A — includes both JWT and X-User-Email for compat."""
    from app.database.jwt_utils import create_access_token
    token = create_access_token("user_a@test.com", "User A")
    return {
        "X-User-Email": "user_a@test.com",
        "Authorization": f"Bearer {token}",
    }


@pytest.fixture
def user_b_headers():
    """Headers for test user B — includes both JWT and X-User-Email for compat."""
    from app.database.jwt_utils import create_access_token
    token = create_access_token("user_b@test.com", "User B")
    return {
        "X-User-Email": "user_b@test.com",
        "Authorization": f"Bearer {token}",
    }


@pytest.fixture
def sample_pdf_bytes():
    """Minimal valid-looking text content masquerading as a PDF for upload tests."""
    return b"%PDF-1.4 fake pdf Patient Name: John Doe Insurer: Test Insurance Claim Amount: Rs. 200000"


@pytest.fixture
def sample_txt_bytes():
    return b"Patient Name: John Doe\nInsurer: Star Health Insurance\nClaim Amount: Rs. 150000\nDenial Reason: Pre-existing condition"


@pytest.fixture
def sample_pipeline_request():
    return {
        "patient_name": "Test Patient",
        "insurer_name": "Test Insurer",
        "claim_amount": 100000,
        "denial_reason": "Pre-existing condition exclusion",
        "document_types": ["policy", "medical_report", "denial_letter"],
    }
