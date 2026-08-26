"""Postgres storage for extracted document text and metadata."""
from __future__ import annotations
import json, os, uuid
from typing import Optional, List
from datetime import datetime, timezone

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    _DB_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/docprocessor")
    _engine = create_engine(_DB_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=_engine)
    _PG = True
except Exception:
    _PG = False
    SessionLocal = None


def ensure_schema():
    """Create the documents table if it doesn't exist."""
    if not _PG:
        return
    with _engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS documents (
                id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                filename    TEXT NOT NULL,
                s3_key      TEXT,
                text_content TEXT,
                metadata    JSONB,
                page_count  INT,
                status      TEXT DEFAULT 'pending',
                created_at  TIMESTAMPTZ DEFAULT NOW(),
                processed_at TIMESTAMPTZ
            )
        """))
        conn.commit()


def store_extraction(filename: str, text_content: str, metadata: dict, page_count: int = 1, s3_key: str = "") -> str:
    """Persist extracted document content. Returns the document UUID."""
    if not _PG:
        doc_id = str(uuid.uuid4())
        print(f"[mock] Would store doc {doc_id}: {filename} ({page_count} pages)")
        return doc_id

    with SessionLocal() as db:
        result = db.execute(
            text("""
                INSERT INTO documents (filename, s3_key, text_content, metadata, page_count, status, processed_at)
                VALUES (:fn, :s3, :txt, :meta::jsonb, :pages, 'done', NOW())
                RETURNING id
            """),
            {"fn": filename, "s3": s3_key, "txt": text_content,
             "meta": json.dumps(metadata), "pages": page_count},
        )
        doc_id = str(result.fetchone()[0])
        db.commit()
        return doc_id


def get_document(doc_id: str) -> Optional[dict]:
    """Retrieve a stored document by ID."""
    if not _PG:
        return {"id": doc_id, "status": "mock", "text_content": "Mock content"}

    with SessionLocal() as db:
        row = db.execute(
            text("SELECT id, filename, text_content, metadata, page_count, status, created_at FROM documents WHERE id = :id"),
            {"id": doc_id},
        ).fetchone()
        return dict(row._mapping) if row else None


def list_documents(limit: int = 20) -> List[dict]:
    """List recently processed documents."""
    if not _PG:
        return []
    with SessionLocal() as db:
        rows = db.execute(
            text("SELECT id, filename, status, page_count, created_at FROM documents ORDER BY created_at DESC LIMIT :lim"),
            {"lim": limit},
        ).fetchall()
        return [dict(r._mapping) for r in rows]
