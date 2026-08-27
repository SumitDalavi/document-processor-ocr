import pytest
import os
import sys
import json
import uuid
import time
from unittest.mock import patch, MagicMock, mock_open

# We need to mock dependencies before importing modules
# We will mock openai, httpx, boto3, and sqlalchemy.

@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
    monkeypatch.setenv("WORKER_THREADS", "1")

# Mock the entire openai library
mock_openai_client = MagicMock()
mock_openai_module = MagicMock()
mock_openai_module.OpenAI.return_value = mock_openai_client
sys.modules["openai"] = mock_openai_module

# Mock httpx
mock_httpx = MagicMock()
sys.modules["httpx"] = mock_httpx

# Mock boto3
mock_boto3 = MagicMock()
sys.modules["boto3"] = mock_boto3

# Mock sqlalchemy
mock_sqlalchemy = MagicMock()
mock_sqlalchemy.text = lambda x: x
sys.modules["sqlalchemy"] = mock_sqlalchemy
mock_sqlalchemy_orm = MagicMock()
sys.modules["sqlalchemy.orm"] = mock_sqlalchemy_orm

# Now import the modules to test
from api.server import app, processed_documents
from api.webhook import notify_completion
from extraction.extractor import classify_document, extract_structured_data, GeneralExtraction, InvoiceExtraction, ContractExtraction
from doc_queue.worker import DocumentQueue, Job
from storage.s3_store import download_document, upload_result, get_presigned_url
from storage.postgres_store import ensure_schema, store_extraction, list_documents, get_document as get_postgres_document
from validation.validator import validate_extraction, ValidationResult, validate_date, validate_amount, validate_invoice, validate_contract

from fastapi.testclient import TestClient

client = TestClient(app)

# ----------------- validation.validator ----------------- #

def test_validation_result():
    res = ValidationResult()
    res.add_error("field1", "error")
    res.add_warning("field2", "warning")
    d = res.to_dict()
    assert d["passed"] is False
    assert len(d["errors"]) == 1
    assert len(d["warnings"]) == 1
    assert d["total_issues"] == 2

def test_validate_date():
    res = ValidationResult()
    validate_date("", "empty_date", res)
    assert len(res.warnings) == 1
    
    res = ValidationResult()
    validate_date("2024-01-01", "valid_date", res)
    assert len(res.warnings) == 0

    res = ValidationResult()
    validate_date("1990-01-01", "old_date", res)
    assert len(res.warnings) == 1

    res = ValidationResult()
    validate_date("not-a-date", "invalid_date", res)
    assert len(res.warnings) == 1

def test_validate_amount():
    res = ValidationResult()
    validate_amount(-10, "neg", res)
    assert len(res.errors) == 1

    res = ValidationResult()
    validate_amount(2_000_000, "large", res)
    assert len(res.warnings) == 1

def test_validate_invoice():
    # Valid
    ext = {
        "vendor_name": "V", "invoice_number": "1",
        "invoice_date": "2024-01-01", "due_date": "2024-02-01",
        "subtotal": 100, "tax": 10, "total_amount": 110,
        "line_items": [{"total": 100}]
    }
    res = validate_invoice(ext)
    assert res.passed

    # Invalid
    ext = {
        "invoice_date": "invalid",
        "subtotal": 100, "tax": 50, "total_amount": 150,
        "line_items": [{"total": 90}]
    }
    res = validate_invoice(ext)
    assert not res.passed
    assert len(res.errors) >= 2 # missing vendor, missing invoice_number
    assert len(res.warnings) >= 1 # mismatched subtotal, high tax

    # Tax 100 on total 100
    ext = {"vendor_name": "V", "invoice_number": "1", "subtotal": 0, "tax": 100, "total_amount": 100, "line_items": []}
    res = validate_invoice(ext)
    assert res.passed

def test_validate_contract():
    # Valid
    ext = {"parties": ["A", "B"], "effective_date": "2024-01-01", "key_obligations": ["O1"], "termination_clauses": ["T1"]}
    res = validate_contract(ext)
    assert res.passed

    # Invalid
    ext = {"parties": ["A"]}
    res = validate_contract(ext)
    assert not res.passed

def test_validate_extraction():
    ext = {"_document_type": "invoice", "confidence": 0.9, "vendor_name": "V", "invoice_number": "123"}
    res = validate_extraction(ext)
    assert res["routing"] == "auto-approve"

    ext = {"_document_type": "contract", "confidence": 0.4, "parties": ["A"]}
    res = validate_extraction(ext)
    assert res["routing"] == "detailed-review"

    ext = {"_document_type": "other", "confidence": 0.6}
    res = validate_extraction(ext)
    assert res["routing"] == "quick-review"

# ----------------- extraction.extractor ----------------- #

def test_classify_document():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="invoice"))]
    mock_openai_client.chat.completions.create.return_value = mock_response
    
    res = classify_document("test text")
    assert res == "invoice"

def test_extract_structured_data():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content='{"vendor_name": "Test"}'))]
    mock_openai_client.chat.completions.create.return_value = mock_response

    res = extract_structured_data("test text", "invoice")
    assert res["vendor_name"] == "Test"
    assert res["_document_type"] == "invoice"
    
    # Test fallback (two API calls: classify then extract)
    mock_resp_classify = MagicMock()
    mock_resp_classify.choices = [MagicMock(message=MagicMock(content='invoice'))]
    mock_resp_extract = MagicMock()
    mock_resp_extract.choices = [MagicMock(message=MagicMock(content='{}'))]
    mock_openai_client.chat.completions.create.side_effect = [mock_resp_classify, mock_resp_extract]
    
    res2 = extract_structured_data("test text", None)
    assert res2["_document_type"] == "invoice"

# ----------------- queue.worker ----------------- #

def test_worker_queue():
    q = DocumentQueue(num_workers=1)
    
    def process_fn(path, fmt):
        if path == "error":
            raise ValueError("bad path")
        return {"status": "ok"}
        
    q.set_processor(process_fn)
    q.start()
    
    j1 = q.enqueue("doc.pdf")
    j2 = q.enqueue("error")
    
    time.sleep(0.1) # wait for worker
    
    j1_fetched = q.get_job(j1.id)
    assert j1_fetched.status == "done"
    assert j1_fetched.result == {"status": "ok"}
    
    j2_fetched = q.get_job(j2.id)
    assert j2_fetched.status == "failed"
    assert "bad path" in j2_fetched.error
    
    assert q.get_job("invalid") is None
    
    q.stop()
    
# ----------------- api.webhook ----------------- #

def test_webhook():
    import api.webhook
    api.webhook._OK = True
    
    mock_httpx.post.return_value = MagicMock(status_code=200)
    res = notify_completion("http://url", "1", "ok")
    assert res is True
    
    mock_httpx.post.side_effect = Exception("err")
    res = notify_completion("http://url", "1", "ok")
    assert res is False
    
    api.webhook._OK = False
    res = notify_completion("http://url", "1", "ok")
    assert res is False

# ----------------- storage.s3_store ----------------- #

def test_s3_store():
    import storage.s3_store
    storage.s3_store._BOTO3 = True
    
    download_document("key", "path")
    storage.s3_store._S3.download_file.assert_called_with("doc-processor-input", "key", "path")
    
    upload_result("path", "key")
    storage.s3_store._S3.upload_file.assert_called_with("path", "doc-processor-output", "key")
    
    storage.s3_store._S3.generate_presigned_url.return_value = "http://presigned"
    res = get_presigned_url("key")
    assert res == "http://presigned"
    
    # Test missing boto3
    storage.s3_store._BOTO3 = False
    with pytest.raises(RuntimeError):
        download_document("key", "p")
    with pytest.raises(RuntimeError):
        upload_result("p", "key")
    assert get_presigned_url("key") == "[mock] s3://doc-processor-output/key"

# ----------------- storage.postgres_store ----------------- #

def test_postgres_store():
    import storage.postgres_store
    storage.postgres_store._PG = True
    
    mock_conn = MagicMock()
    mock_result = MagicMock()
    mock_result.fetchone.return_value = ["1234"]
    mock_conn.execute.return_value = mock_result
    
    mock_session = MagicMock()
    mock_session.__enter__.return_value = mock_conn
    storage.postgres_store.SessionLocal = MagicMock(return_value=mock_session)
    storage.postgres_store._engine = MagicMock()
    storage.postgres_store._engine.connect.return_value = mock_session
    
    ensure_schema()
    
    doc_id = store_extraction("f", "t", {})
    assert doc_id == "1234"
    
    mock_result.fetchone.return_value = MagicMock(_mapping={"id": "1234"})
    doc = get_postgres_document("1234")
    assert doc["id"] == "1234"
    
    mock_result.fetchone.return_value = None
    assert get_postgres_document("invalid") is None
    
    mock_result.fetchall.return_value = [MagicMock(_mapping={"id": "1234"})]
    docs = list_documents()
    assert len(docs) == 1
    
    # Test missing PG
    storage.postgres_store._PG = False
    ensure_schema()
    doc_id = store_extraction("f", "t", {})
    assert doc_id is not None
    assert get_postgres_document("id")["status"] == "mock"
    assert list_documents() == []

# ----------------- api.server ----------------- #

def test_server():
    # Clean in-memory
    processed_documents.clear()
    
    with patch("api.server.extract_text") as mock_ext_text, \
         patch("api.server.classify_document") as mock_classify, \
         patch("api.server.extract_structured_data") as mock_ext_data, \
         patch("api.server.validate_extraction") as mock_val:
         
        mock_ext_text.return_value = {"full_text": "text"}
        mock_classify.return_value = "invoice"
        mock_ext_data.return_value = {"data": "data"}
        mock_val.return_value = {"validation": {"passed": True}, "routing": "auto-approve", "confidence": 0.9}
        
        # Test Upload
        with open("test.txt", "w") as f:
            f.write("test")
        with open("test.txt", "rb") as f:
            res = client.post("/api/upload", files={"file": ("test.txt", f, "text/plain")})
        assert res.status_code == 200
        doc_id = res.json()["id"]
        
        # Test Exception in Upload
        mock_ext_text.side_effect = Exception("failed")
        with open("test.txt", "rb") as f:
            res = client.post("/api/upload", files={"file": ("test.txt", f, "text/plain")})
        assert res.status_code == 500
        mock_ext_text.side_effect = None

        # Test process-text
        res = client.post("/api/process-text", json={"text": "text"})
        assert res.status_code == 200
        doc_id2 = res.json()["id"]
        
        # Test list documents
        res = client.get("/api/documents")
        assert res.status_code == 200
        assert res.json()["total"] == 2
        
        # Test get document
        res = client.get(f"/api/documents/{doc_id}")
        assert res.status_code == 200
        assert res.json()["id"] == doc_id
        
        res = client.get("/api/documents/invalid")
        assert res.status_code == 404
        
        # Test approve
        res = client.post(f"/api/documents/{doc_id}/approve")
        assert res.status_code == 200
        assert processed_documents[0]["status"] == "approved"
        
        res = client.post("/api/documents/invalid/approve")
        assert res.status_code == 404
        
        # Test reject
        res = client.post(f"/api/documents/{doc_id}/reject")
        assert res.status_code == 200
        assert processed_documents[0]["status"] == "rejected"
        
        res = client.post("/api/documents/invalid/reject")
        assert res.status_code == 404
        
        # Test stats
        res = client.get("/api/stats")
        assert res.status_code == 200
        assert res.json()["total"] == 2
        
        # Clear docs for stats empty
        processed_documents.clear()
        res = client.get("/api/stats")
        assert res.status_code == 200
        assert res.json()["total"] == 0

