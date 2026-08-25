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

load_dotenv()

app = FastAPI(title="Multi-Modal Document Processor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# In-memory store for processed documents
processed_documents: list[dict] = []


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
        # Step 1: Extract text
        text_result = extract_text(str(save_path))
        
        # Step 2: Classify document
        doc_type = classify_document(text_result["full_text"])
        
        # Step 3: Extract structured data
        extraction = extract_structured_data(text_result["full_text"], doc_type)
        
        # Step 4: Validate
        validation = validate_extraction(extraction)
        
        # Store result
        result = {
            "id": doc_id,
            "filename": file.filename,
            "text_extraction": text_result,
            "document_type": doc_type,
            "structured_data": extraction,
            "validation": validation,
            "status": validation["routing"]
        }
        processed_documents.append(result)
        
        return result
    
    except Exception as e:
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
    processed_documents.append(result)
    
    return result


@app.get("/api/documents")
async def list_documents():
    """List all processed documents."""
    return {
        "documents": [{
            "id": d["id"],
            "filename": d["filename"],
            "document_type": d["document_type"],
            "status": d["status"],
            "validation_passed": d["validation"]["validation"]["passed"],
            "confidence": d["validation"]["confidence"]
        } for d in processed_documents],
        "total": len(processed_documents)
    }


@app.get("/api/documents/{doc_id}")
async def get_document(doc_id: str):
    """Get full details for a specific document."""
    doc = next((d for d in processed_documents if d["id"] == doc_id), None)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@app.post("/api/documents/{doc_id}/approve")
async def approve_document(doc_id: str):
    """Human reviewer approves a document."""
    doc = next((d for d in processed_documents if d["id"] == doc_id), None)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc["status"] = "approved"
    return {"success": True}


@app.post("/api/documents/{doc_id}/reject")
async def reject_document(doc_id: str):
    """Human reviewer rejects a document."""
    doc = next((d for d in processed_documents if d["id"] == doc_id), None)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc["status"] = "rejected"
    return {"success": True}


@app.get("/api/stats")
async def get_stats():
    """Processing pipeline analytics."""
    total = len(processed_documents)
    if total == 0:
        return {"total": 0}
    
    by_type = {}
    by_status = {}
    by_routing = {}
    
    for d in processed_documents:
        dt = d["document_type"]
        by_type[dt] = by_type.get(dt, 0) + 1
        
        status = d["status"]
        by_status[status] = by_status.get(status, 0) + 1
        
        routing = d["validation"]["routing"]
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
