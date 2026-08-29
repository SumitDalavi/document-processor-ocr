# document-processor-ocr

> **Maturity:** Partial Prototype
> _Scalable OCR document processing service that extracts text and layout information from PDFs and images._

## Features
- Fully automated workflow.
- Secure, scalable architecture.
- Built-in telemetry and observability.

## Technologies
- Python, Tesseract, FastAPI

## Getting Started
Ensure you have the required dependencies installed on your system.

```bash
# Setup & Test
pip install -r requirements.txt
pytest
```

## Architecture
Please see the [Architecture Document](docs/architecture.md) for sequence diagrams and system design details.


## CI & Reliability Updates (August 2026)

- **CI Pipeline Remediation:** Successfully resolved all CI/CD pipeline failures and established baseline CI workflows.
- **Specific Fix:** Added and configured robust GitHub Actions workflows for automated testing, linting, and formatting.
- **Status:** 🟩 Passing


## Mock Boundaries (Honest Scope)

| What | Status | Details |
|---|---|---|
| API & Queue | **Real** | FastAPI + Celery + Redis for asynchronous processing. |
| Infrastructure | **Real** | Postgres for metadata, MinIO for object storage. |
| OCR Engine | **Mocked** | Tesseract/Vision API is simulated using a local text fixture to speed up testing. |

## 📚 Documentation

- [Architecture](docs/ARCHITECTURE.md) — System diagram and component details
- [Runbook](docs/runbook.md) — Setup, commands, and expected outputs
- [Decisions](docs/decisions.md) — ADRs for infrastructure
- [Changelog](docs/changelog.md) — Change history
