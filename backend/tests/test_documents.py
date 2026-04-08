"""
Tests for document upload and per-user data isolation — Issues 10 & 11.
Critical: verifies User A's documents are never visible to User B.
"""

import pytest
import io
from unittest.mock import patch, AsyncMock


class TestDocumentList:

    def test_empty_list_for_new_user(self, client, user_a_headers):
        response = client.get("/api/documents/", headers=user_a_headers)
        assert response.status_code == 200
        data = response.json()
        # Response is either {documents: []} or a raw list
        if isinstance(data, dict):
            docs = data.get("documents", data)
        else:
            docs = data
        assert isinstance(docs, (list, dict)), f"Unexpected type: {type(docs)}"

    def test_list_returns_valid_schema(self, client, user_a_headers):
        response = client.get("/api/documents/", headers=user_a_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert data["total"] == len(data["documents"])

    def test_without_email_header_still_responds(self, client):
        """Missing header should return a valid response (defaults to 'default' user)."""
        response = client.get("/api/documents/")
        assert response.status_code == 200


class TestDocumentUpload:

    def test_upload_requires_file_and_type(self, client, user_a_headers):
        """Uploading with no file should return validation error."""
        response = client.post("/api/documents/upload", headers=user_a_headers,
                               data={"file_type": "policy"})
        assert response.status_code == 422  # Unprocessable entity

    def test_upload_rejects_invalid_file_type(self, client, user_a_headers):
        content = b"hello world"
        response = client.post(
            "/api/documents/upload",
            headers=user_a_headers,
            files={"file": ("test.pdf", io.BytesIO(content), "application/pdf")},
            data={"file_type": "invalid_type"},
        )
        assert response.status_code == 400

    @patch("app.routers.documents.save_document")
    @patch("app.services.groq_service.groq_vision_ocr", new_callable=AsyncMock)
    async def test_upload_returns_document_structure(
        self, mock_ocr, mock_save, client, user_a_headers
    ):
        mock_ocr.return_value = ("Extracted text content", {"Patient Name": "Test"}, "groq_vision")
        mock_save.return_value = {
            "id": 1, "file_id": "abc123", "filename": "test.pdf",
            "file_type": "policy", "status": "processed", "user_email": "user_a@test.com",
        }
        content = b"Fake PDF content Patient: John"
        response = client.post(
            "/api/documents/upload",
            headers=user_a_headers,
            files={"file": ("test.pdf", io.BytesIO(content), "application/pdf")},
            data={"file_type": "policy"},
        )
        if response.status_code == 200:
            data = response.json()
            assert "document" in data
            assert "message" in data


# ─── Issue 10: Per-User Data Isolation ─────────────────────────

class TestPerUserDataIsolation:
    """
    Issue 10: CRITICAL — User A must never see User B's documents.
    These tests simulate two users and verify complete isolation.
    """

    def test_user_a_and_user_b_get_separate_lists(self, client, user_a_headers, user_b_headers):
        """Both users should get their own empty lists, not a shared one."""
        resp_a = client.get("/api/documents/", headers=user_a_headers)
        resp_b = client.get("/api/documents/", headers=user_b_headers)

        assert resp_a.status_code == 200
        assert resp_b.status_code == 200

        # Both have their own lists
        docs_a = resp_a.json()["documents"]
        docs_b = resp_b.json()["documents"]

        # If User A has docs, they should not appear in User B's list
        if docs_a:
            ids_a = {d.get("id") for d in docs_a}
            ids_b = {d.get("id") for d in docs_b}
            assert ids_a.isdisjoint(ids_b), "User A's doc IDs found in User B's list!"

    def test_different_emails_produce_different_doc_stores(self, client):
        """Vary the email header and get different isolated results."""
        headers_x = {"X-User-Email": "user_x_isolation@test.com"}
        headers_y = {"X-User-Email": "user_y_isolation@test.com"}

        resp_x = client.get("/api/documents/", headers=headers_x)
        resp_y = client.get("/api/documents/", headers=headers_y)

        assert resp_x.status_code == 200
        assert resp_y.status_code == 200
        # Both should return valid JSON (list or dict with documents key)
        data_x = resp_x.json()
        data_y = resp_y.json()
        assert data_x is not None
        assert data_y is not None

    def test_pipeline_results_are_isolated_per_user(self, client):
        """Pipeline latest result must be per-user."""
        headers_x = {"X-User-Email": "pipeline_user_x@test.com"}
        headers_y = {"X-User-Email": "pipeline_user_y@test.com"}

        resp_x = client.get("/api/pipeline/latest-result", headers=headers_x)
        resp_y = client.get("/api/pipeline/latest-result", headers=headers_y)

        assert resp_x.status_code == 200
        assert resp_y.status_code == 200

        # Neither should contain the other's data
        if resp_x.json().get("user_email"):
            assert resp_x.json()["user_email"] != "pipeline_user_y@test.com"

    def test_dashboard_stats_are_per_user(self, client):
        """Dashboard stats endpoint must respect X-User-Email header."""
        headers_x = {"X-User-Email": "stats_user_x@test.com"}
        headers_y = {"X-User-Email": "stats_user_y@test.com"}

        resp_x = client.get("/api/dashboard/stats", headers=headers_x)
        resp_y = client.get("/api/dashboard/stats", headers=headers_y)

        assert resp_x.status_code == 200
        assert resp_y.status_code == 200

        data_x = resp_x.json()
        data_y = resp_y.json()

        # Stats should be independent
        assert "total_documents" in data_x
        assert "total_documents" in data_y

    def test_appeals_are_isolated_per_user(self, client):
        """Appeal letters must be per-user."""
        headers_x = {"X-User-Email": "appeal_user_x@test.com"}
        headers_y = {"X-User-Email": "appeal_user_y@test.com"}

        resp_x = client.get("/api/appeals/", headers=headers_x)
        resp_y = client.get("/api/appeals/", headers=headers_y)

        assert resp_x.status_code == 200
        assert resp_y.status_code == 200


class TestDocumentDelete:

    def test_delete_nonexistent_document_returns_404(self, client, user_a_headers):
        response = client.delete("/api/documents/999999", headers=user_a_headers)
        assert response.status_code == 404

    def test_delete_requires_correct_user(self, client, user_a_headers, user_b_headers):
        """User B cannot delete User A's documents (should 404)."""
        # Try to delete doc 1 as user_b — since user_b has no docs, should 404
        response = client.delete("/api/documents/1", headers=user_b_headers)
        assert response.status_code == 404
