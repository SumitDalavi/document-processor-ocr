# Architecture — document-processor-ocr
> Last updated: 2026-08-29 | Maturity: Partial Prototype
> _OCR document processing with FastAPI and Celery._

## System Diagram
```mermaid
flowchart TD
    Client(["Client"])
    API["FastAPI App"]
    Queue["Redis (Queue)"]
    Worker["Celery Worker"]
    DB[("PostgreSQL")]
    Storage[("MinIO (S3)")]
    OCR["OCR Engine (Tesseract/Vision)"]

    Client -->|"1. POST /upload"| API
    API -->|"2. Save to"| Storage
    API -->|"3. Enqueue Job"| Queue
    Worker -->|"4. Consume Job"| Queue
    Worker -->|"5. Fetch file"| Storage
    Worker -->|"6. Run OCR"| OCR
    Worker -->|"7. Save Metadata"| DB
```

## Component Table
| Component | File | Responsibility | Tech |
|---|---|---|---|
| API | `api/` | Ingests documents | FastAPI |
| Worker | `doc_queue/` | Async processing | Celery |
| Storage | `storage/` | MinIO interface | Python |
| Database | `docker-compose.yml`| RDBMS for states | PostgreSQL |

## Dependency Honesty Table
| Dependency | Status | Notes |
|---|---|---|
| Postgres | **Real** | Used for metadata and job status. |
| MinIO | **Real** | Used as S3-compatible storage. |
| OCR Engine | **Mocked** | Simulated with a fixture for fast CI execution. |
