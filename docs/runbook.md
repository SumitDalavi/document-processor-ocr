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
