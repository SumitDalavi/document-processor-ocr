# Runbook — document-processor-ocr
> Last updated: 2026-08-29

## Quick Start
```bash
docker-compose up -d --build
```
API runs on `http://localhost:4006`.
MinIO Console runs on `http://localhost:9001` (minioadmin:minioadmin).

## Environment Variables
| Variable | Default | Purpose |
|---|---|---|
| DB_URL | `postgresql://ocr:secret@postgres:5432/ocrdb` | Postgres connection |
| S3_ENDPOINT | `http://minio:9000` | S3 API endpoint |

## Common Failure Modes
| Symptom | Cause | Fix |
|---|---|---|
| Jobs not processing | Celery worker dead | `docker-compose logs worker` |
| S3 upload fails | MinIO not ready | Check `docker-compose ps minio` |

## Release Runbook

### Triggering a New Release
Releases are automated via GitHub Actions (`.github/workflows/release.yml`) and trigger whenever a semantic version tag is pushed:

```bash
# 1. Ensure master is clean and up-to-date
git checkout master
git pull origin master

# 2. Tag the release
git tag -a v0.1.0 -m "Release v0.1.0"

# 3. Push the tag to trigger the pipeline
git push origin v0.1.0
```

### Release Pipeline Stages
1. **Test Verification:** Runs project test suite gates prior to container build.
2. **Container Image Build:** Builds the production container image (`ghcr.io/sumitdalavi/document-processor-ocr:<tag>`).
3. **Trivy Vulnerability Scan:** Scans the built container for CRITICAL and HIGH CVEs via Aqua Security Trivy.
4. **Anchore Syft SBOM Generation:** Creates an SPDX JSON Software Bill of Materials (`sbom.spdx.json`).
5. **GitHub Release Publishing:** Creates the release with auto-generated release notes and attaches `sbom.spdx.json`.

### Verifying the Release
```bash
# Check workflow run status
gh run list --workflow=release.yml --repo SumitDalavi/document-processor-ocr

# Inspect the published release and attached assets
gh release view v0.1.0 --repo SumitDalavi/document-processor-ocr

# Download and inspect the SBOM
gh release download v0.1.0 --repo SumitDalavi/document-processor-ocr -p "sbom.spdx.json"
cat sbom.spdx.json | jq .spdxVersion
```

### Release Failure Modes
| Symptom | Cause | Resolution |
|---|---|---|
| `Unable to resolve action ... unable to find version` | Pinned action tag missing or upstream tag modified | Pin action to a verified release tag (`@v0.36.0`) or commit SHA |
| `invalid reference format: repository name must be lowercase` | Container repository owner contains uppercase characters | Lowercase the repository owner before tagging (`tr '[:upper:]' '[:lower:]'`) |
| `File not found: sbom.spdx.json` during release step | SBOM action configured with `artifact-name` instead of `output-file` | Ensure `output-file: sbom.spdx.json` is set in Anchore action |
