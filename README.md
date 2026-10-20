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

## 🚀 Progressive Credential Loading & Execution Tiers

This project implements **Progressive Credential Loading (PCL)**, allowing it to run immediately out-of-the-box without external dependencies while seamlessly upgrading as credentials are provided.

### Tier 1: Zero-Config Mock Mode (Default)
Ideal for CI, testing, and rapid local evaluation.
- **Execution:** Run with default configuration (`cp .env.example .env`). Zero API keys, databases, or cloud credentials required.
- **Fallback Behavior:** In-memory caches, deterministic offline heuristics, mock vector embeddings, and local mock storage are automatically used.
- **Health Verification:** Endpoints report `{"mode": "mock"}` for unconfigured dependencies.

### Tier 2: Local Development with Live Services
Connect specific external services while keeping others mocked.
- **Execution:** Provide credentials in `.env` for the services you want active (e.g., `DATABASE_URL, REDIS_URL, S3_ENDPOINT_URL`).
- **Progressive Upgrade:** The runtime inspects environment variables on boot and dynamically promotes only configured modules to live mode.
- **Safe Fallback:** Any missing credentials automatically remain on mock fallbacks with no crashes or missing service errors.

### Tier 3: Production Hardened
Enterprise deployment with production-grade backends, security scans, and container distributions.
- **OCI Container Image:** Pre-built, multi-arch image on GitHub Container Registry:
  ```bash
  docker pull ghcr.io/sumitdalavi/document-processor-ocr:v0.2.0
  ```
- **Production Orchestration:** Mount secrets via Kubernetes Secrets or cloud secret managers with atomic config reload support.
- **Release Verification:** Checksums and SPDX SBOM available on [GitHub Releases](https://github.com/SumitDalavi/document-processor-ocr/releases).

## 📚 Documentation

- [Architecture](docs/ARCHITECTURE.md) — System diagram and component details
- [Runbook](docs/runbook.md) — Setup, commands, and expected outputs
- [Decisions](docs/decisions.md) — ADRs for infrastructure
- [Changelog](docs/changelog.md) — Change history

## Release & Security Verification

Every tagged release (`v*.*.*`) triggers an automated DevSecOps release workflow:
1. **Automated Testing:** Runs test suite gates before build.
2. **Container Image Build:** Builds production container image (`ghcr.io/sumitdalavi/document-processor-ocr:<tag>`).
3. **Vulnerability Scanning:** Scans the image using [Aqua Security Trivy](https://github.com/aquasecurity/trivy-action) for `HIGH` and `CRITICAL` CVEs.
4. **SBOM Generation:** Generates a Software Bill of Materials (SBOM) in SPDX JSON format (`sbom.spdx.json`) using [Anchore Syft](https://github.com/anchore/sbom-action).
5. **GitHub Release Publishing:** Packages release notes and attaches `sbom.spdx.json` as a verifiable supply-chain asset.

### Verifying Releases via GitHub CLI
```bash
# View release details
gh release view v0.1.0 --repo SumitDalavi/document-processor-ocr

# Download and verify SBOM
gh release download v0.1.0 --repo SumitDalavi/document-processor-ocr --pattern "sbom.spdx.json"
cat sbom.spdx.json | jq .
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Runbook](docs/runbook.md)
- [Decisions](docs/decisions.md)
- [Changelog](docs/changelog.md)