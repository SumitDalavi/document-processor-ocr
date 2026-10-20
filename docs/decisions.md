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

## ADR-002: Progressive Credential Loading (PCL) Architecture
- **Context:** Production hardening required live backends (PostgreSQL, Redis, OpenAI, Anthropic), but removing mocks would break CI pipelines and create high developer onboarding friction.
- **Decision:** Implement Progressive Credential Loading. Keep in-memory and local mock heuristics as the default safe baseline, while wrapping external integrations in auto-promoting factory adapters triggered by environment variables.
- **Consequences:** 
  - *Pros:* 100% CI pass rate without requiring external secrets; zero setup friction for new contributors; progressive upgrade to production clusters.
  - *Cons:* Adds lightweight factory abstraction layers and runtime credential detection logic.
