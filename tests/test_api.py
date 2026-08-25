from fastapi.testclient import TestClient
from api.server import app

client = TestClient(app)

def test_process_text():
    response = client.post("/api/process-text", json={
        "text": "Invoice 12345\nTotal: $500.00",
        "document_type": "invoice"
    })
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["document_type"] == "invoice"

def test_list_documents():
    response = client.get("/api/documents")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert isinstance(data["documents"], list)
