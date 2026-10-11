# ADR-001 — architecture baseline
Status: existing specification decision referenced; implementation started 2026-10-12.

The stack decision and alternatives are in docs/05_Engineering_Specification.md
sections 1.1–1.4: Python 3.12, FastAPI, SQLAlchemy 2 / Alembic, PostgreSQL 16,
Redis 7 / arq, React 18 / TypeScript / Vite on Node 22. Follow that decision.
AWS primary ap-south-1, DR ap-south-2; deployment remains outside this local slice.

This slice implements API startup, local settings, health and sanitized error
responses only (WP-03 partial). Database adapters, authentication, RBAC, audit and
worker persistence remain pending. Readiness deliberately returns 503 until the
database and queue checks exist. No business or money endpoints are implemented.
See docs/knowledge-bank/DECISIONS.md for session decisions and limitations.
