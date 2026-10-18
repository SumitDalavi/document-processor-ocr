# Changelog

## [v0.1.0] — 2026-10-18
### Added
- Automated GitHub Actions release pipeline triggered on `v*.*.*` git tags (`.github/workflows/release.yml`).
- Container image packaging (`ghcr.io/sumitdalavi/document-processor-ocr`).
- Container vulnerability scanning via Aqua Security Trivy (`aquasecurity/trivy-action@v0.36.0`).
- SPDX-format Software Bill of Materials (SBOM) generation step (`anchore/sbom-action@v0`).
- Automated GitHub release publishing attaching `sbom.spdx.json` via `softprops/action-gh-release@v2`.

## [2026-08-29] — Phase 2 Evidence
### Added
- Added Postgres and MinIO to `docker-compose.yml`.
- Added `tests/e2e/test_local_infrastructure.sh` to simulate full stack integration testing.
- Standardized documentation (`runbook.md`, `decisions.md`, `ARCHITECTURE.md`).
- Added maturity badge and mock boundaries to `README.md`.
