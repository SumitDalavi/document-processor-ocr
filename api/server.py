"""
FastAPI Server for the Document Processing Pipeline.
Provides endpoints for uploading documents, processing them, and retrieving results.
"""
import os
import sys
import uuid
import shutil
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.ingestion import extract_text
from extraction.extractor import extract_structured_data, classify_document
from validation.validator import validate_extraction
from doc_queue.tasks import process_document_task
from celery.result import AsyncResult
import redis
import json

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

app = FastAPI(title="Multi-Modal Document Processor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


class ProcessRequest(BaseModel):
    text: str
    document_type: Optional[str] = None


@app.post("/api/upload")
async def upload_and_process(file: UploadFile = File(...)):
    """
    Upload a document file (PDF, image, or text) and run the full pipeline:
    1. Text extraction (OCR/native)
    2. Document classification
    3. Structured data extraction
    4. Business rule validation
    5. Confidence-based routing
    """
    doc_id = str(uuid.uuid4())[:8]
    ext = Path(file.filename or "file.pdf").suffix
    save_path = UPLOAD_DIR / f"{doc_id}{ext}"
    
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    try:
        # Submit to Celery
        task = process_document_task.delay(str(save_path), file.filename)
        
        # Initial status
        result = {
            "id": doc_id,
            "task_id": task.id,
            "filename": file.filename,
            "status": "processing"
        }
        redis_client.set(f"doc:{doc_id}", json.dumps(result))
        redis_client.sadd("documents", doc_id)
        
        return result
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/process-text")
async def process_text(req: ProcessRequest):
    """Process raw text directly (no file upload)."""
    doc_id = str(uuid.uuid4())[:8]
    
    doc_type = req.document_type or classify_document(req.text)
    extraction = extract_structured_data(req.text, doc_type)
    validation = validate_extraction(extraction)
    
    result = {
        "id": doc_id,
        "filename": "text-input",
        "document_type": doc_type,
        "structured_data": extraction,
        "validation": validation,
        "status": validation["routing"]
    }
    redis_client.set(f"doc:{doc_id}", json.dumps(result))
    redis_client.sadd("documents", doc_id)
    
    return result


@app.get("/api/documents")
async def list_documents():
    """List all processed documents."""
    doc_ids = redis_client.smembers("documents")
    docs = []
    for d_id in doc_ids:
        raw = redis_client.get(f"doc:{d_id}")
        if raw:
            d = json.loads(raw)
            # Sync celery task state if still processing
            if d.get("status") == "processing" and "task_id" in d:
                task = AsyncResult(d["task_id"])
                if task.ready():
                    if task.successful():
                        task_res = task.result
                        if "error" in task_res:
                            d["status"] = "failed"
                        else:
                            d.update(task_res)
                    else:
                        d["status"] = "failed"
                    redis_client.set(f"doc:{d_id}", json.dumps(d))

            docs.append({
                "id": d.get("id"),
                "filename": d.get("filename"),
                "document_type": d.get("document_type"),
                "status": d.get("status"),
                "validation_passed": d.get("validation", {}).get("validation", {}).get("passed") if "validation" in d else None,
                "confidence": d.get("validation", {}).get("confidence") if "validation" in d else None,
            })
    return {
        "documents": docs,
        "total": len(docs)
    }

@app.get("/api/documents/{doc_id}")
async def get_document(doc_id: str):
    """Get full details for a specific document."""
    raw = redis_client.get(f"doc:{doc_id}")
    if not raw:
        raise HTTPException(status_code=404, detail="Document not found")
    d = json.loads(raw)
    
    if d.get("status") == "processing" and "task_id" in d:
        task = AsyncResult(d["task_id"])
        if task.ready():
            if task.successful():
                task_res = task.result
                if "error" in task_res:
                    d["status"] = "failed"
                else:
                    d.update(task_res)
            else:
                d["status"] = "failed"
            redis_client.set(f"doc:{doc_id}", json.dumps(d))
    return d


@app.post("/api/documents/{doc_id}/approve")
async def approve_document(doc_id: str):
    """Human reviewer approves a document."""
    raw = redis_client.get(f"doc:{doc_id}")
    if not raw:
        raise HTTPException(status_code=404, detail="Document not found")
    doc = json.loads(raw)
    doc["status"] = "approved"
    redis_client.set(f"doc:{doc_id}", json.dumps(doc))
    return {"success": True}

@app.post("/api/documents/{doc_id}/reject")
async def reject_document(doc_id: str):
    """Human reviewer rejects a document."""
    raw = redis_client.get(f"doc:{doc_id}")
    if not raw:
        raise HTTPException(status_code=404, detail="Document not found")
    doc = json.loads(raw)
    doc["status"] = "rejected"
    redis_client.set(f"doc:{doc_id}", json.dumps(doc))
    return {"success": True}


@app.get("/api/stats")
async def get_stats():
    """Processing pipeline analytics."""
    doc_ids = redis_client.smembers("documents")
    docs = []
    for d_id in doc_ids:
        raw = redis_client.get(f"doc:{d_id}")
        if raw:
            docs.append(json.loads(raw))
            
    total = len(docs)
    if total == 0:
        return {"total": 0}
    
    by_type = {}
    by_status = {}
    by_routing = {}
    
    for d in docs:
        dt = d.get("document_type", "unknown")
        by_type[dt] = by_type.get(dt, 0) + 1
        
        status = d.get("status", "unknown")
        by_status[status] = by_status.get(status, 0) + 1
        
        routing = d.get("validation", {}).get("routing", "unknown") if "validation" in d else "unknown"
        by_routing[routing] = by_routing.get(routing, 0) + 1
    
    auto_approved = by_routing.get("auto-approve", 0)
    
    return {
        "total": total,
        "by_type": by_type,
        "by_status": by_status,
        "by_routing": by_routing,
        "auto_approval_rate": round(auto_approved / total * 100, 1) if total > 0 else 0
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4006)
