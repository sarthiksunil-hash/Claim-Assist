"""
Supabase Repository Layer
All read/write operations for documents, claims, appeals, and chat
go through this module instead of using in-memory dicts.

Falls back gracefully to LOCAL SQLITE when Supabase is unavailable.
Data now persists across server restarts even without Supabase (Issue 3 fix).
"""

import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any

from app.database.db import (
    get_supabase, SessionLocal,
    Document, ClaimAnalysis, AppealLetter, ChatMessage,
)


def _sb():
    """Get Supabase client, or None if unavailable."""
    return get_supabase()


def _get_db():
    """Get a fresh SQLite session (caller must close)."""
    return SessionLocal()


# ══════════════════════════════════════════════════════════════
#  DOCUMENT REPOSITORY
# ══════════════════════════════════════════════════════════════

def _doc_row_to_dict(row: Document) -> Dict:
    """Convert a SQLAlchemy Document row to a dict matching the API shape."""
    meta = row.metadata_json
    if isinstance(meta, str):
        try:
            meta = json.loads(meta)
        except Exception:
            meta = {}
    return {
        "id":             row.id,
        "file_id":        row.file_id or "",
        "user_email":     row.user_email,
        "filename":       row.filename,
        "file_type":      row.file_type,
        "file_path":      row.file_path,
        "file_size":      row.file_size or 0,
        "upload_date":    row.upload_date.isoformat() if row.upload_date else "",
        "status":         row.status or "uploaded",
        "ocr_source":     row.ocr_source or "none",
        "extracted_text": row.extracted_text or "",
        "metadata":       meta if isinstance(meta, dict) else {},
        "rag_indexed":    row.rag_indexed or False,
        "rag_chunks":     row.rag_chunks or 0,
    }


def get_user_documents(user_email: str) -> List[Dict]:
    """Get all documents for a user."""
    sb = _sb()
    if sb:
        try:
            res = sb.table("documents").select("*") \
                .eq("user_email", user_email) \
                .order("upload_date", desc=False) \
                .execute()
            docs = res.data or []
            for d in docs:
                if isinstance(d.get("metadata"), str):
                    try:
                        d["metadata"] = json.loads(d["metadata"])
                    except Exception:
                        d["metadata"] = {}
            if docs:
                return docs
        except Exception as e:
            print(f"[Repo] get_user_documents Supabase error: {e}")

    # SQLite fallback
    db = _get_db()
    try:
        rows = db.query(Document).filter(
            Document.user_email == user_email
        ).order_by(Document.upload_date).all()
        return [_doc_row_to_dict(r) for r in rows]
    finally:
        db.close()


def save_document(doc: Dict) -> Dict:
    """Insert a new document record. Returns the saved doc with db id."""
    sb = _sb()
    user_email = doc.get("user_email", "default")
    saved_to_supabase = False

    if sb:
        try:
            meta = doc.get("metadata", {})
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except Exception:
                    meta = {}
            payload = {
                "file_id":        doc.get("file_id", ""),
                "user_email":     user_email,
                "filename":       doc.get("filename", ""),
                "file_type":      doc.get("file_type", ""),
                "file_path":      doc.get("file_path", ""),
                "file_size":      doc.get("file_size", 0),
                "status":         doc.get("status", "uploaded"),
                "ocr_source":     doc.get("ocr_source", "none"),
                "extracted_text": doc.get("extracted_text", ""),
                "metadata":       meta,
                "rag_indexed":    doc.get("rag_indexed", False),
                "rag_chunks":     doc.get("rag_chunks", 0),
                "upload_date":    doc.get("upload_date", datetime.utcnow().isoformat()),
            }
            res = sb.table("documents").insert(payload).execute()
            if res.data:
                saved = res.data[0]
                doc["id"] = saved["id"]
                saved_to_supabase = True
        except Exception as e:
            print(f"[Repo] save_document Supabase error: {e}")

    # Always persist to SQLite too (sync + fallback)
    db = _get_db()
    try:
        meta = doc.get("metadata", {})
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except Exception:
                meta = {}
        row = Document(
            file_id=doc.get("file_id", ""),
            user_email=user_email,
            filename=doc.get("filename", ""),
            file_type=doc.get("file_type", ""),
            file_path=doc.get("file_path", ""),
            file_size=doc.get("file_size", 0),
            status=doc.get("status", "uploaded"),
            ocr_source=doc.get("ocr_source", "none"),
            extracted_text=doc.get("extracted_text", ""),
            metadata_json=meta,
            rag_indexed=doc.get("rag_indexed", False),
            rag_chunks=doc.get("rag_chunks", 0),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        if "id" not in doc or not doc["id"]:
            doc["id"] = row.id
    except Exception as e:
        print(f"[Repo] save_document SQLite error: {e}")
        db.rollback()
    finally:
        db.close()

    return doc


def update_document(file_id: str, user_email: str, updates: Dict) -> bool:
    """Update document fields (e.g. after OCR or RAG indexing)."""
    sb = _sb()
    if sb:
        try:
            payload = {}
            for key in ["extracted_text", "rag_indexed", "rag_chunks", "status", "ocr_source"]:
                if key in updates:
                    payload[key] = updates[key]
            if "metadata" in updates:
                meta = updates["metadata"]
                if isinstance(meta, str):
                    try:
                        meta = json.loads(meta)
                    except Exception:
                        meta = {}
                payload["metadata"] = meta
            if payload:
                sb.table("documents").update(payload) \
                    .eq("file_id", file_id) \
                    .eq("user_email", user_email) \
                    .execute()
        except Exception as e:
            print(f"[Repo] update_document Supabase error: {e}")

    # SQLite sync
    db = _get_db()
    try:
        row = db.query(Document).filter(
            Document.file_id == file_id,
            Document.user_email == user_email,
        ).first()
        if row:
            if "extracted_text" in updates:
                row.extracted_text = updates["extracted_text"]
            if "metadata" in updates:
                meta = updates["metadata"]
                if isinstance(meta, str):
                    try:
                        meta = json.loads(meta)
                    except Exception:
                        meta = {}
                row.metadata_json = meta
            if "rag_indexed" in updates:
                row.rag_indexed = updates["rag_indexed"]
            if "rag_chunks" in updates:
                row.rag_chunks = updates["rag_chunks"]
            if "status" in updates:
                row.status = updates["status"]
            if "ocr_source" in updates:
                row.ocr_source = updates["ocr_source"]
            db.commit()
            return True
    except Exception as e:
        print(f"[Repo] update_document SQLite error: {e}")
        db.rollback()
    finally:
        db.close()
    return False


def delete_document_record(doc_id: int, user_email: str) -> bool:
    """Delete a document record from the store."""
    sb = _sb()
    if sb:
        try:
            sb.table("documents").delete() \
                .eq("id", doc_id) \
                .eq("user_email", user_email) \
                .execute()
        except Exception as e:
            print(f"[Repo] delete_document Supabase error: {e}")

    # SQLite
    db = _get_db()
    try:
        row = db.query(Document).filter(
            Document.id == doc_id,
            Document.user_email == user_email,
        ).first()
        if row:
            db.delete(row)
            db.commit()
            return True
    except Exception as e:
        print(f"[Repo] delete_document SQLite error: {e}")
        db.rollback()
    finally:
        db.close()
    return False


# ══════════════════════════════════════════════════════════════
#  CLAIM ANALYSIS REPOSITORY
# ══════════════════════════════════════════════════════════════

def _claim_row_to_dict(row: ClaimAnalysis) -> Dict:
    """Convert a SQLAlchemy ClaimAnalysis row to a dict."""
    def _parse_json(val):
        if isinstance(val, str):
            try:
                return json.loads(val)
            except Exception:
                return {}
        return val if val is not None else {}

    return {
        "id":                    row.id,
        "claim_id":              row.claim_id or "",
        "user_email":            row.user_email,
        "patient_name":          row.patient_name or "",
        "insurer_name":          row.insurer_name or "",
        "claim_amount":          row.claim_amount or 0,
        "denial_reason":         row.denial_reason or "",
        "analyzed_at":           row.analyzed_at.isoformat() if row.analyzed_at else "",
        "status":                row.status or "pending",
        "discrepancies":         _parse_json(row.discrepancies),
        "policy_alignment_score": row.policy_alignment_score or 0,
        "medical_necessity_score": row.medical_necessity_score or 0,
        "appeal_strength":       _parse_json(row.appeal_strength),
        "pipeline_results":      _parse_json(row.pipeline_results),
        "recommendation":        row.recommendation or "",
    }


def get_user_claims(user_email: str) -> List[Dict]:
    """Get all claim analyses for a user."""
    sb = _sb()
    if sb:
        try:
            res = sb.table("claim_analyses").select("*") \
                .eq("user_email", user_email) \
                .order("analyzed_at", desc=True) \
                .execute()
            claims = res.data or []
            for c in claims:
                for jfield in ["appeal_strength", "discrepancies", "pipeline_results"]:
                    if isinstance(c.get(jfield), str):
                        try:
                            c[jfield] = json.loads(c[jfield])
                        except Exception:
                            c[jfield] = {}
            if claims:
                return claims
        except Exception as e:
            print(f"[Repo] get_user_claims Supabase error: {e}")

    # SQLite fallback
    db = _get_db()
    try:
        rows = db.query(ClaimAnalysis).filter(
            ClaimAnalysis.user_email == user_email
        ).order_by(ClaimAnalysis.analyzed_at.desc()).all()
        return [_claim_row_to_dict(r) for r in rows]
    finally:
        db.close()


def get_claim_by_id(claim_id: str, user_email: str) -> Optional[Dict]:
    """Get a specific claim by claim_id."""
    sb = _sb()
    if sb:
        try:
            res = sb.table("claim_analyses").select("*") \
                .eq("claim_id", claim_id) \
                .eq("user_email", user_email) \
                .limit(1) \
                .execute()
            if res.data:
                claim = res.data[0]
                for jfield in ["appeal_strength", "discrepancies", "pipeline_results"]:
                    if isinstance(claim.get(jfield), str):
                        try:
                            claim[jfield] = json.loads(claim[jfield])
                        except Exception:
                            claim[jfield] = {}
                return claim
        except Exception as e:
            print(f"[Repo] get_claim_by_id Supabase error: {e}")

    # SQLite fallback
    db = _get_db()
    try:
        row = db.query(ClaimAnalysis).filter(
            ClaimAnalysis.claim_id == claim_id,
            ClaimAnalysis.user_email == user_email,
        ).first()
        if row:
            return _claim_row_to_dict(row)
    finally:
        db.close()
    return None


def save_claim(claim: Dict) -> Dict:
    """Insert a new claim analysis record."""
    sb = _sb()
    user_email = claim.get("user_email", "default")

    def _ensure_dict(val):
        if isinstance(val, str):
            try:
                return json.loads(val)
            except Exception:
                return {}
        return val if val is not None else {}

    def _ensure_list(val):
        if isinstance(val, str):
            try:
                return json.loads(val)
            except Exception:
                return []
        return val if val is not None else []

    if sb:
        try:
            payload = {
                "claim_id":               claim.get("claim_id", ""),
                "user_email":             user_email,
                "patient_name":           claim.get("patient_name", ""),
                "insurer_name":           claim.get("insurer_name", ""),
                "claim_amount":           claim.get("claim_amount", 0),
                "denial_reason":          claim.get("denial_reason", ""),
                "status":                 claim.get("status", "completed"),
                "policy_alignment_score": claim.get("policy_alignment_score", 0),
                "medical_necessity_score": claim.get("medical_necessity_score", 0),
                "appeal_strength":        _ensure_dict(claim.get("appeal_strength", {})),
                "discrepancies":          _ensure_list(claim.get("discrepancies", [])),
                "pipeline_results":       _ensure_dict(claim.get("pipeline_results", {})),
                "recommendation":         claim.get("recommendation", ""),
                "analyzed_at":            datetime.utcnow().isoformat(),
            }
            res = sb.table("claim_analyses").insert(payload).execute()
            if res.data:
                claim["db_id"] = res.data[0]["id"]
        except Exception as e:
            print(f"[Repo] save_claim Supabase error: {e}")

    # SQLite persist
    db = _get_db()
    try:
        row = ClaimAnalysis(
            claim_id=claim.get("claim_id", ""),
            user_email=user_email,
            patient_name=claim.get("patient_name", ""),
            insurer_name=claim.get("insurer_name", ""),
            claim_amount=claim.get("claim_amount", 0),
            denial_reason=claim.get("denial_reason", ""),
            status=claim.get("status", "completed"),
            policy_alignment_score=claim.get("policy_alignment_score", 0),
            medical_necessity_score=claim.get("medical_necessity_score", 0),
            appeal_strength=_ensure_dict(claim.get("appeal_strength", {})),
            discrepancies=_ensure_list(claim.get("discrepancies", [])),
            pipeline_results=_ensure_dict(claim.get("pipeline_results", {})),
            recommendation=claim.get("recommendation", ""),
        )
        db.add(row)
        db.commit()
    except Exception as e:
        print(f"[Repo] save_claim SQLite error: {e}")
        db.rollback()
    finally:
        db.close()

    return claim


# ══════════════════════════════════════════════════════════════
#  APPEAL LETTER REPOSITORY
# ══════════════════════════════════════════════════════════════

def _appeal_row_to_dict(row: AppealLetter) -> Dict:
    """Convert a SQLAlchemy AppealLetter row to a dict."""
    def _parse_json_list(val):
        if isinstance(val, str):
            try:
                return json.loads(val)
            except Exception:
                return []
        return val if val is not None else []

    return {
        "id":                row.id,
        "claim_id":          row.claim_id or "",
        "user_email":        row.user_email,
        "appeal_text":       row.appeal_text or "",
        "tone":              row.tone or "formal",
        "citations":         _parse_json_list(row.citations),
        "regulations_cited": _parse_json_list(row.regulations_cited),
        "generated_at":      row.generated_at.isoformat() if row.generated_at else "",
        "status":            row.status or "draft",
        "confidence_score":  row.confidence_score or 0.0,
    }


def get_user_appeals(user_email: str) -> List[Dict]:
    """Get all appeal letters for a user."""
    sb = _sb()
    if sb:
        try:
            res = sb.table("appeal_letters").select("*") \
                .eq("user_email", user_email) \
                .order("generated_at", desc=True) \
                .execute()
            appeals = res.data or []
            for a in appeals:
                for jfield in ["citations", "regulations_cited"]:
                    if isinstance(a.get(jfield), str):
                        try:
                            a[jfield] = json.loads(a[jfield])
                        except Exception:
                            a[jfield] = []
            if appeals:
                return appeals
        except Exception as e:
            print(f"[Repo] get_user_appeals Supabase error: {e}")

    # SQLite fallback
    db = _get_db()
    try:
        rows = db.query(AppealLetter).filter(
            AppealLetter.user_email == user_email
        ).order_by(AppealLetter.generated_at.desc()).all()
        return [_appeal_row_to_dict(r) for r in rows]
    finally:
        db.close()


def save_appeal(appeal: Dict) -> Dict:
    """Insert a new appeal letter record."""
    sb = _sb()
    user_email = appeal.get("user_email", "default")

    def _ensure_list(val):
        if isinstance(val, str):
            try:
                return json.loads(val)
            except Exception:
                return []
        return val if val is not None else []

    if sb:
        try:
            payload = {
                "claim_id":         appeal.get("claim_id", ""),
                "user_email":       user_email,
                "appeal_text":      appeal.get("appeal_text", ""),
                "tone":             appeal.get("tone", "formal"),
                "citations":        _ensure_list(appeal.get("citations", [])),
                "regulations_cited": _ensure_list(appeal.get("regulations_cited", [])),
                "confidence_score": appeal.get("confidence_score", 0.0),
                "status":           appeal.get("status", "generated"),
                "generated_at":     datetime.utcnow().isoformat(),
            }
            res = sb.table("appeal_letters").insert(payload).execute()
            if res.data:
                appeal["db_id"] = res.data[0]["id"]
        except Exception as e:
            print(f"[Repo] save_appeal Supabase error: {e}")

    # SQLite persist
    db = _get_db()
    try:
        row = AppealLetter(
            claim_id=appeal.get("claim_id", ""),
            user_email=user_email,
            appeal_text=appeal.get("appeal_text", ""),
            tone=appeal.get("tone", "formal"),
            citations=_ensure_list(appeal.get("citations", [])),
            regulations_cited=_ensure_list(appeal.get("regulations_cited", [])),
            confidence_score=appeal.get("confidence_score", 0.0),
            status=appeal.get("status", "generated"),
        )
        db.add(row)
        db.commit()
    except Exception as e:
        print(f"[Repo] save_appeal SQLite error: {e}")
        db.rollback()
    finally:
        db.close()

    return appeal


# ══════════════════════════════════════════════════════════════
#  CHAT MESSAGE REPOSITORY
# ══════════════════════════════════════════════════════════════

def save_chat_message(user_email: str, role: str, content: str,
                      model: str = "", has_context: bool = False,
                      sources: List = None) -> bool:
    """Persist a chat message to Supabase + SQLite."""
    sb = _sb()
    msg_record = {
        "user_email":  user_email,
        "role":        role,
        "content":     content,
        "model":       model,
        "has_context": has_context,
        "sources":     sources or [],
        "created_at":  datetime.utcnow().isoformat(),
    }
    saved_to_supabase = False
    if sb:
        try:
            sb.table("chat_messages").insert(msg_record).execute()
            saved_to_supabase = True
        except Exception as e:
            print(f"[Repo] save_chat_message Supabase error: {e}")

    # SQLite persist
    db = _get_db()
    try:
        row = ChatMessage(
            user_email=user_email,
            role=role,
            content=content,
            model=model,
            has_context=has_context,
            sources=sources or [],
        )
        db.add(row)
        db.commit()
    except Exception as e:
        print(f"[Repo] save_chat_message SQLite error: {e}")
        db.rollback()
    finally:
        db.close()

    return saved_to_supabase


def get_chat_history(user_email: str, limit: int = 50) -> List[Dict]:
    """Get recent chat history for a user."""
    sb = _sb()
    if sb:
        try:
            res = sb.table("chat_messages").select("*") \
                .eq("user_email", user_email) \
                .order("created_at", desc=False) \
                .limit(limit) \
                .execute()
            if res.data:
                return res.data
        except Exception as e:
            print(f"[Repo] get_chat_history Supabase error: {e}")

    # SQLite fallback
    db = _get_db()
    try:
        rows = db.query(ChatMessage).filter(
            ChatMessage.user_email == user_email
        ).order_by(ChatMessage.created_at).limit(limit).all()
        return [
            {
                "user_email":  r.user_email,
                "role":        r.role,
                "content":     r.content,
                "model":       r.model or "",
                "has_context": r.has_context or False,
                "sources":     r.sources if r.sources else [],
                "created_at":  r.created_at.isoformat() if r.created_at else "",
            }
            for r in rows
        ]
    finally:
        db.close()


# ══════════════════════════════════════════════════════════════
#  DASHBOARD STATS
# ══════════════════════════════════════════════════════════════

def get_dashboard_stats(user_email: str) -> Dict:
    """Get real stats for a user from Supabase or SQLite fallback."""
    sb = _sb()
    if sb:
        try:
            docs_res = sb.table("documents").select("id", count="exact") \
                .eq("user_email", user_email).execute()
            claims_res = sb.table("claim_analyses").select("id,appeal_strength", count="exact") \
                .eq("user_email", user_email).execute()
            appeals_res = sb.table("appeal_letters").select("id", count="exact") \
                .eq("user_email", user_email).execute()

            total_docs = docs_res.count or 0
            claims = claims_res.data or []
            total_claims = claims_res.count or 0
            total_appeals = appeals_res.count or 0

            strong = 0
            for c in claims:
                strength = c.get("appeal_strength", {})
                if isinstance(strength, str):
                    try:
                        strength = json.loads(strength)
                    except Exception:
                        strength = {}
                if isinstance(strength, dict) and strength.get("overall_score", 0) >= 70:
                    strong += 1

            success_rate = round((strong / total_claims) * 100) if total_claims > 0 else 0

            recent_res = sb.table("claim_analyses").select(
                "claim_id,patient_name,insurer_name,status,analyzed_at"
            ).eq("user_email", user_email).order("analyzed_at", desc=True).limit(5).execute()

            recent = []
            for c in (recent_res.data or []):
                recent.append({
                    "patient_name": c.get("patient_name", "Unknown"),
                    "insurer":      c.get("insurer_name", "Unknown"),
                    "status":       c.get("status", "unknown"),
                    "timestamp":    c.get("analyzed_at", ""),
                })

            return {
                "total_documents":  total_docs,
                "claims_analyzed":  total_claims,
                "appeals_generated": total_appeals,
                "success_rate":     success_rate,
                "active_cases":     total_claims,
                "avg_processing_time": "3-5s" if total_claims > 0 else "--",
                "weekly_trend":     [],
                "recent_claims":    recent,
            }
        except Exception as e:
            print(f"[Repo] get_dashboard_stats Supabase error: {e}")

    # SQLite fallback — real counts from local DB
    db = _get_db()
    try:
        total_docs = db.query(Document).filter(Document.user_email == user_email).count()
        total_claims = db.query(ClaimAnalysis).filter(ClaimAnalysis.user_email == user_email).count()
        total_appeals = db.query(AppealLetter).filter(AppealLetter.user_email == user_email).count()

        recent_rows = db.query(ClaimAnalysis).filter(
            ClaimAnalysis.user_email == user_email
        ).order_by(ClaimAnalysis.analyzed_at.desc()).limit(5).all()

        recent = []
        for c in recent_rows:
            recent.append({
                "patient_name": c.patient_name or "Unknown",
                "insurer":      c.insurer_name or "Unknown",
                "status":       c.status or "unknown",
                "timestamp":    c.analyzed_at.isoformat() if c.analyzed_at else "",
            })

        return {
            "total_documents":   total_docs,
            "claims_analyzed":   total_claims,
            "appeals_generated": total_appeals,
            "success_rate":      0,
            "active_cases":      total_claims,
            "avg_processing_time": "3-5s" if total_claims > 0 else "--",
            "weekly_trend":      [],
            "recent_claims":     recent,
        }
    finally:
        db.close()
