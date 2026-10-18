> **NOTE:** This repository is an archival lab or partial prototype. It is not actively maintained and should not be used as a reference for production-grade deployments or performance benchmarks.


# document-processor-ocr

[![CI Pipeline](https://github.com/SumitDalavi/document-processor-ocr/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/SumitDalavi/document-processor-ocr/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/SumitDalavi/document-processor-ocr)](https://github.com/SumitDalavi/document-processor-ocr/releases)
[![Release Workflow](https://github.com/SumitDalavi/document-processor-ocr/actions/workflows/release.yml/badge.svg)](https://github.com/SumitDalavi/document-processor-ocr/actions/workflows/release.yml)

> **Maturity:** Functional Prototype
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

## 🔒 Release & Security Verification

Every tagged release (*.*.*) triggers an automated DevSecOps release workflow:
1. **Automated Testing:** Runs pytest test suite with pytest-asyncio and httpx.
2. **Container Image Build:** Builds the service container image (ghcr.io/sumitdalavi/document-processor-ocr:<tag>).
3. **Vulnerability Scanning:** Scans the container image using [Aqua Security Trivy](https://github.com/aquasecurity/trivy-action) for HIGH and CRITICAL CVEs.
4. **SBOM Generation:** Generates a Software Bill of Materials (SBOM) in SPDX JSON format (sbom.spdx.json) using [Anchore Syft](https://github.com/anchore/sbom-action).
5. **GitHub Release Publishing:** Packages release notes and attaches sbom.spdx.json as a verifiable supply-chain asset.

## 👨‍💻 Author

**Sumit Dalavi** — Senior DevSecOps / Platform Engineer  
[GitHub](https://github.com/SumitDalavi) | [LinkedIn](https://in.linkedin.com/in/sumit-dalavi-762838129)

## 📚 Documentation

- [Architecture](docs/ARCHITECTURE.md) — System diagram and component details
- [Runbook](docs/runbook.md) — Setup, commands, and expected outputs
- [Decisions](docs/decisions.md) — ADRs for infrastructure
- [Changelog](docs/changelog.md) — Change history
