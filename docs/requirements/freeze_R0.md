# R0 requirement baseline — DRAFT

Prepared 2026-10-12 from scope register v0.3 rev 2. Not frozen or accepted. WP-01 is human-led; this document is a review artefact, not sign-off.

## Requirements

Acceptance text below is copied verbatim from the register.

### REQ-001 — F-A01 (WP-03)

The system shall provide: Login with MFA (authenticator app, e-mail), session policy.

Acceptance: Given synthetic fixture FIX-A-001 for SCR-001, when the user performs the screen-level acceptance test in 03_UI_UX_Atlas.md (SCR-001), then all listed controls render, validation/errors behave as specified, and the action is audit-logged.

Screens: SCR-001; calculations: none; connectors: none. Status: UNACCEPTED.

### REQ-002 — F-A02 (WP-04)

The system shall provide: Multi-workspace / multi-account switcher.

Acceptance: Given synthetic fixture FIX-A-002 for SCR-002, when the user performs the screen-level acceptance test in 03_UI_UX_Atlas.md (SCR-002), then all listed controls render, validation/errors behave as specified, and the action is audit-logged.

Screens: SCR-002; calculations: none; connectors: none. Status: UNACCEPTED.

### REQ-003 — F-A03 (WP-04)

The system shall provide: Legal entities, brands, stores, marketplaces, warehouses config.

Acceptance: Given synthetic fixture FIX-A-003 for SCR-115,SCR-101, when the user performs the screen-level acceptance test in 03_UI_UX_Atlas.md (SCR-115,SCR-101), then all listed controls render, validation/errors behave as specified, and the action is audit-logged.

Screens: SCR-115,SCR-101; calculations: none; connectors: none. Status: UNACCEPTED.

### REQ-004 — F-A04 (WP-04)

The system shall provide: Currencies, timezones, target periods per store.

Acceptance: Given synthetic fixture FIX-A-004 for SCR-101, when the user opens the screen, then all listed columns/controls render and values match golden vectors GV-033 to the cent.

Screens: SCR-101; calculations: CALC-026; connectors: none. Status: UNACCEPTED.

### REQ-006 — F-A06 (WP-03)

The system shall provide: User invitations & roles by function/product/market.

Acceptance: Given synthetic fixture FIX-A-006 for SCR-115, when the user performs the screen-level acceptance test in 03_UI_UX_Atlas.md (SCR-115), then all listed controls render, validation/errors behave as specified, and the action is audit-logged.

Screens: SCR-115; calculations: none; connectors: none. Status: UNACCEPTED.

### REQ-007 — F-A07 (WP-03)

The system shall provide: Safe demo mode (synthetic data).

Acceptance: Given synthetic fixture FIX-A-007 for SCR-002, when the user performs the screen-level acceptance test in 03_UI_UX_Atlas.md (SCR-002), then all listed controls render, validation/errors behave as specified, and the action is audit-logged.

Screens: SCR-002; calculations: none; connectors: none. Status: UNACCEPTED.

### REQ-008 — F-A08 (WP-06)

The system shall provide: Data retention & lifecycle settings.

Acceptance: Given synthetic fixture FIX-A-008 for SCR-101, when the user performs the screen-level acceptance test in 03_UI_UX_Atlas.md (SCR-101), then all listed controls render, validation/errors behave as specified, and the action is audit-logged.

Screens: SCR-101; calculations: none; connectors: none. Status: UNACCEPTED.

### REQ-119 — F-K01 (WP-05)

The system shall provide: Connector: Amazon SP-API (Orders, Finances, Reports, FBA Inventory, Inbound, Sales, Listings read).

Acceptance: Given synthetic fixture FIX-K-119 for SCR-100, when the user performs the screen-level acceptance test in 03_UI_UX_Atlas.md (SCR-100), then all listed controls render, validation/errors behave as specified, and the action is audit-logged.

Screens: SCR-100; calculations: none; connectors: CON-01. Status: UNACCEPTED.

### REQ-156 — F-L07 (WP-06)

The system shall provide: Diagnostics: sync status, freshness, errors, data lineage.

Acceptance: Given synthetic fixture FIX-L-156 for SCR-114, when the user performs the screen-level acceptance test in 03_UI_UX_Atlas.md (SCR-114), then all listed controls render, validation/errors behave as specified, and the action is audit-logged.

Screens: SCR-114; calculations: none; connectors: none. Status: UNACCEPTED.

### REQ-160 — F-L11 (WP-03)

The system shall provide: Data export/delete (GDPR/DPDP), audit log.

Acceptance: Given synthetic fixture FIX-L-160 for SCR-101, when the user performs the screen-level acceptance test in 03_UI_UX_Atlas.md (SCR-101), then all listed controls render, validation/errors behave as specified, and the action is audit-logged.

Screens: SCR-101; calculations: none; connectors: none. Status: UNACCEPTED.

### REQ-175 — F-L07 (WP-06)

Source failure yields 'stale/missing' status, never zero sales or cost.

Acceptance: GV-046.

Screens: SCR-114; calculations: none; connectors: none. Status: UNACCEPTED.

## Next freeze target

R1: WP-07, WP-08, WP-09, WP-10, WP-11, WP-12, WP-13, WP-35, WP-37, WP-31 slice 31a, WP-32, WP-29 slice 29a, WP-34, WP-33. Requirement acceptance is recorded through WP-30.

## Open dependencies

See ../discovery/open_questions.md. Source access, API facts, and CA confirmation remain unresolved. No credentials or real business data were used.
