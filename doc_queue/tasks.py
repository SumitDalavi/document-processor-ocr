import os
from celery import shared_task
from doc_queue.celery_app import celery_app
from data.ingestion import extract_text
from extraction.extractor import extract_structured_data, classify_document
from validation.validator import validate_extraction

@shared_task(name="process_document_task")
def process_document_task(file_path: str, filename: str):
    """
    Background task to process a document through the OCR and extraction pipeline.
    """
    try:
        # Step 1: Extract text
        text_result = extract_text(file_path)
        
        # Step 2: Classify document
        doc_type = classify_document(text_result["full_text"])
        
        # Step 3: Extract structured data
        extraction = extract_structured_data(text_result["full_text"], doc_type)
        
        # Step 4: Validate
        validation = validate_extraction(extraction)
        
        return {
            "filename": filename,
            "text_extraction": text_result,
            "document_type": doc_type,
            "structured_data": extraction,
            "validation": validation,
            "status": validation["routing"]
        }
    except Exception as e:
        return {"error": str(e), "filename": filename, "status": "failed"}
