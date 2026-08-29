# Decisions

## ADR-001: MinIO and Postgres for Local E2E
**Date:** 2026-08-29  
**Status:** Accepted

**Context:**  
We need robust E2E testing of the document pipeline without relying on external cloud resources (AWS S3, RDS).

**Decision:**  
We include MinIO (S3-compatible) and PostgreSQL in `docker-compose.yml`.

**Consequences:**  
- ✅ Local dev environment mirrors production architecture.
- ✅ E2E tests can validate real network calls.
- ⚠️ Docker stack uses more memory locally.
