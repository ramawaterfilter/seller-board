# Connectors (nested)
- Read-only. Request read/report scopes only; ad platforms (CON-02/08/09, CON-11 TikTok Ads, Walmart Connect/SEM) are spend only — drop clicks, conversions and platform-reported sales at normalisation; one spend source per ad account (spend_source).
- credential_ref only; no token in code, fixtures, cassettes or logs; revocation -> CONNECTOR_REVOKED (RB-01).
- Raw first into ing.raw_payload with content-hash idempotency; per-region / per-account rate-limit buckets; 429 -> back-off; restatements supersede rows.
- API facts only from integration/connector_contracts.md; an UNVERIFIED fact is a DISC- BLOCKER, never a guess. Buyer PII stripped at raw-write.
- Cassettes synthetic and scanned (B0SYNTH\d{3}, SYNTH GSTINs, @example.test only).
## Code Review Rules
- P0: a write scope or write call, a credential or real identifier in a cassette, an omitted connector (CON-03/04/10/12..15/24/26) being built.
- P1: ad-platform data other than spend persisted, a missing revocation or 429 test, an endpoint/version not in the contract.
