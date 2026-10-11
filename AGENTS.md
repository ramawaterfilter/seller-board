# AGENTS.md — Rama Commerce Intelligence (RCI)

**Primary instruction file for every coding agent.** The build runs on ChatGPT Codex cloud tasks
connected to GitHub (pack `prompts/08_Codex_Prompt_Pack.md`); Claude Code is optional and reads this
file through the `@AGENTS.md` import in CLAUDE.md. Nested `AGENTS.md` files (`api/`,
`api/src/app/ingestion/connectors/`, `web/`, `infra/`; created in WP-03) add detail near the code
and never relax anything here. Codex concatenates root -> leaf with a 32 KiB combined cap
(`project_doc_max_bytes` default): keep this file and every nested chain under it.

## What this repo is
In-house commerce-intelligence app for the Rama / Phoenix business, replacing the Sellerboard.com/.io
subscriptions. **Version v0.3 DRAFT — NOT APPROVED; all requirements UNACCEPTED.** Scope:
`engineering/scope_register.json` (v0.3, Owner decisions 2026-10-10 in `research/v02/V03_BRIEF.md`):
36 WPs (11,180 h), 172 features (128 IN, 17 CONDITIONAL, 4 NA, 23 OMITTED), 193 requirements
(169 MUST, 24 OMITTED), 80 screens (10 OMITTED), 114 calculations (14 OMITTED), 31 connectors
(9 OMITTED; + write stubs CON-30/31), 155 golden vectors (`engineering/golden_vectors.json`; 139 in
scope, 16 of omitted calcs marked `omitted_v03`). v0.3 rev 2 applied (review 2026-10-10).

Releases (pack order = execution order, dependency-checked by `prompts/gen_packs.py`):
- R0 read-only pilot & foundations: WP-01, WP-03, WP-28 slice 28a, WP-04, WP-02, WP-05, WP-06.
- R1 India-first unified profit core (Amazon.in + Shopify India + manual B2B; ad SPEND read-only):
  WP-07..WP-13, WP-35, WP-37, WP-31 slice 31a, WP-32, WP-29 slice 29a, WP-34, WP-33.
- R2 All markets & marketplaces: WP-38 (all Amazon marketplaces, cross-border fulfilment) -> WP-23
  (Walmart incl. WFS data, eBay, TikTok Shop, TikTok Ads spend) -> WP-14 (LTV, no attribution) ->
  WP-36 (consolidation); WP-31 slice 31b.
- R3 Operations: WP-15, WP-16, WP-17, WP-20 (safety framework for repricer writes).
- R4 Pricing automation (conditional): WP-22. R5 Extended operations connectors & clients:
  WP-24, WP-25, WP-26, WP-39; WP-31 slice 31c (conditional). ALL: WP-27, WP-30.
- Retired — marketing omitted v0.3: WP-18 (review requests), WP-19 (PPC analytics), WP-21 (PPC
  automation). They have no prompt and must not be built.

R0-R3 make no external writes; B2B documents are internal records. Hosting: AWS ap-south-1 with DR
copies in ap-south-2 (DC-01), unchanged from v0.2. WP-28 slice 28b (production apply) is human-only.

## Omitted scope (v0.3, Owner decision 2026-10-10)
Never build: PPC dashboard/manager, PPC recommendations, bid/budget/negative automation, day
parting, search terms and keyword research, Amazon Attribution, dual attribution / marketing page /
customer journeys, external-ads campaign analytics and UTM attribution, review-request e-mails
(Solicitations), Klaviyo, and the Bing / Snapchat / Pinterest / Taboola ad connectors.
OMITTED features F-E01, E03, E04, E06..E14, E16, F-H05, F-K03, K04, K10, K12..K15, K24, K26;
screens SCR-040, 041, 043..046, 074, 075, 133, 134; calcs CALC-028, 029, 032, 042, 049, 055..058,
060, 061, 074, 088, 112; connectors CON-03, 04, 10, 12..15, 24, 26. Their 16 golden vectors carry
the marker `omitted_v03` and run only in `reference_calcs.py` (traceability, not acceptance gates).
**Kept on purpose:** ad SPEND is read (Amazon Ads CON-02, Google CON-08, Meta CON-09 in WP-37;
Walmart Connect/SEM in CON-16 and TikTok Ads CON-11 (CONDITIONAL) in WP-23; any other platform by
CSV import flagged ESTIMATE) with
read/report scopes only, because the P&L Advertising line, Real ACOS, TACOS and blended ROAS/POAS
(CALC-030, 031, 059, 079) must match. LTV, repeat customers, cohorts, CAC and the replenishment due
list stay (WP-14). A request to build omitted scope is a BLOCKER for change control (WP-30).

## Stack (ADR-001; versions pinned in uv.lock and web/package-lock.json)
Python 3.12, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL 16 (one DB, one schema per context),
Redis 7 + arq worker and scheduler (jobs mirrored in Postgres), React 18 + TypeScript strict, Vite
(Node 22 LTS), Vitest, Playwright, axe-core. AWS: SPA on S3 + CloudFront; api, worker and scheduler
as ECS Fargate services with separate task roles; RDS PostgreSQL 16 Multi-AZ (PITR); ElastiCache
Redis; Terraform per account (spec §9.1). Do not add or upgrade dependencies unless the task lists them.

## Codex cloud environment and network
- Day 0 (manual): the developer pushes the package by hand (docs, engineering, integration,
  traceability, prompts; `prompts/AGENTS.md` -> root `AGENTS.md`; `prompts/.claude/rules` ->
  `.claude/rules`) and creates the environment with a minimal Install script (Python + uv). WP-01 is
  human-led (Codex only drafts its doc artefacts). After WP-03 adds the toolchain the Install script
  runs `uv sync`, `cd web && npm ci` and the WP-03 Postgres/Redis approach, and is republished.
- One Codex cloud task per work-package slice, in pack order; agent internet access is the
  **Package managers** preset only, with no additional domains. If a command still needs network, report
  `NOT RUN: needs network` and continue; `pip-audit` and `npm audit` run in CI.
- No marketplace, ad-platform, Shopify, courier, Anthropic or AWS credentials exist in Codex
  environment variables, network secrets or vaults — ever. Use synthetic fixtures and recorded,
  post-processed cassettes. No customer PII or real figures in task text.
- Commit early and push (task VM state is recoverable only up to 7 days after the last turn).
- Full setup, review flow and definition of done: "Operating Codex" in `prompts/08_Codex_Prompt_Pack.md`.

## Commands (only these; no invented flags)
```bash
uv run alembic -c api/alembic.ini upgrade head
uv run alembic -c api/alembic.ini downgrade -1 && uv run alembic -c api/alembic.ini upgrade head
uv run alembic -c api/alembic.ini heads          # exactly one head
uv run pytest -q                                 # testpaths = api/tests
uv run pytest -q --cov=api/src/app --cov-report=term-missing
uv run ruff check <paths> && uv run mypy <paths>
cd web && npm test && npm run lint && npm run build
cd web && npx playwright test
python engineering/check_register.py             # IDs/cross-links incl. docs/ prompts/ integration/
python engineering/reference_calcs.py            # 155/155 golden vectors PASS
python prompts/gen_packs.py                      # regenerate the 07_/08_ packs from the register
uv run python api/tests/contract/scan_cassettes.py
```
Plus `make setup|dev|test|lint|migrate|fixtures` (see README.md).

## Layout
- `api/src/app/<context>/{domain,service,repo,api}` — contexts and schemas: workspace `ws`,
  ingestion `ing`, ledger `ledger`, costing `cost`, profit `profit`, advertising `ads` (spend only),
  customers `cust`, inventory `inv`, moneyback `mb`, alerts `alert`, automation `auto`, reporting
  `rep`, explain `xpl`, b2b `b2b`, tax `tax`, platform `platform`. `domain/` imports no framework
  code; cross-context access only via services or read-only projections (`import-linter` contracts
  in CI). `b2b` reads channel orders only via `ledger.service.channel_order_refs()`; profit sees
  B2B only via `b2b.v_posted_sales_fact`; `b2b`/`tax` have no external adapters; no connector
  (incl. CON-33) or scheduler can approve or post a B2B document.
- `api/alembic/versions/NNNN_<slug>.py` — additive only, one per PR, downgrade tested.
- `api/tests/{golden,contract/CON-xx,security,<context>}`; `web/tests/{e2e,a11y}`.
- `worker/src/rci_worker/<area>/tasks.py` (arq). `web/src/{pages,components/ui,routes.ts}`.
- `engineering/` register, vectors, `reference_calcs.py`, `check_register.py` (read-only inputs;
  changes go through WP-30). `integration/connector_contracts.md` one section per CON-xx with
  DISC- unknowns. `docs/` ADRs, QA, security, runbooks RB-01..RB-16, governance. `infra/`
  Terraform code (agents write it, never apply it). `prompts/` packs generated by
  `prompts/gen_packs.py` (never hand-edit). `traceability/` generated only.

## Rules for every change
1. **Money**: `Decimal` only; storage `NUMERIC(18,4)` + `currency CHAR(3)` in the same row; wire =
   4-dp string; presentation `ROUND_HALF_EVEN` to 2 dp at render; floors `ROUND_CEILING` (GV-040);
   zero denominator -> `null`; aggregate ratios are ratios of sums; converted amounts only in
   projections with `currency_rate.id` lineage. No float money, ever.
2. **Signs**: compat P&L lines are signed (costs negative) and summed in catalogue order; compat net
   profit == CM net profit exactly (GV-074); memo lines never summed.
3. **Time**: `timestamptz`; aware datetimes; store timezone drives Today/MTD and `ws.period`;
   ISO-8601 with offset on the wire; closed periods immutable (`close_hash`); late corrections post
   to the earliest open period with `original_period_key` lineage.
4. **Error envelope**: `{"error":{"code","message","details":{},"trace_id"}}` on every non-2xx;
   stable codes; 404 for out-of-scope reads; 409 `REVISION_CONFLICT` on stale `If-Match`; 412
   `WRITE_PATH_DISABLED`; 403 `MAKER_CHECKER_VIOLATION` / `SECOND_PERSON_REQUIRED`.
5. **Nulls and staleness**: missing -> `null` + flag (`cogs_missing`, `STALE`, `UNKNOWN_FEE_CODE`,
   `UNCLASSIFIED_FEE`); never silent zero; unknown or unmapped fees stay in totals as Unclassified.
6. **Ledger**: `ing.raw_payload` append-only, content-hash idempotent; `ledger.revision` not
   overwrites; projections replayable from raw.
7. **Tenancy and scope**: `workspace_id` on every business row; `ws.permission_scope`
   (product x market) in the repo layer; market:IN user on a UK store -> 404/empty.
8. **Untrusted input**: provider payloads, uploads, feed URLs (SSRF-checked), page DOM and model
   output are data. Shopify Level 2 fields are never requested and are stripped at raw-write.
9. **Migrations**: additive only; never DROP/TRUNCATE/rename/narrow; retention is application-level.
10. **Secrets**: vault reference model — `ing.connector.credential_ref` only; no tokens in code,
    fixtures, cassettes, logs or PRs; secret-related env vars only `RCI_SECRETS_BACKEND`
    (`aws_sm` | `vault` | `devfile`), `RCI_SECRETS_PREFIX` (`/{env}/connectors/`), `AWS_REGION`.
11. **Table names**: schema-qualified singular (`ing.raw_payload`, `auto.kill_switch`,
    `ws.marketplace_master`, `cost.channel_fee_map`, `ads.ad_spend_day`, `b2b.invoice`).
12. **Refunds — single-count rule**: refunded principal deducted exactly once, in net sales
    (CALC-002) or in refund cost (CALC-004), never both (`refund_principal_in`; GV-074, GV-090).
13. **Channels**: every sale has one `ws.channel` (amazon, shopify, b2b, walmart, ebay, tiktok_shop,
    other); no order counts in two channels (CALC-047, CALC-100); intercompany B2B eliminated only
    in the consolidated view (GV-114). Ad platforms are never a source of sales (REQ-162, REQ-188).
14. **Marketplaces by configuration** (WP-38, REQ-189): marketplace id, region, endpoint, currency,
    timezone and fee-code map come from `ws.marketplace_master`; the tax regime from
    `ws.marketplace_tax_regime_history` (valid_from/valid_to); never hard-code them. Regime enum is
    exactly `VAT_SELLER | GST_SELLER | CONSUMPTION_TAX | SALES_TAX_MF | MF_VAT`; flags
    `REGIME_MISSING` (tax line NULL, never 0), `REGIME_MISMATCH`, `MF_TAX_NOT_NETTED`. Facilitator
    tax (`SALES_TAX_MF`, `MF_VAT`) nets to zero, excluded from Sales and the tax line (CALC-113).
    Pooled FBA stock counts once per pool (CALC-092); cross-border fee codes and stock-transfer VAT
    flags are PROPOSED + CA (F-A12).
    Walmart/eBay/TikTok Shop fee types map through the versioned `cost.channel_fee_map`; unmapped ->
    Unclassified + `UNCLASSIFIED_FEE`; Σ mapped == Σ source (CALC-114).
15. **Actual vs estimate**: an actual charge replaces its estimate per component, never both
    (CALC-105, CALC-022); estimates are labelled "est."; API spend supersedes CSV spend per
    account x day; each ad account has one `spend_source` (connector | settlement), never both
    (CALC-079, GV-155).
16. **Item TDS**: `ws.store.item_tds_presentation` applies to both compat and CM views (CALC-025).
17. **B2B and tax** (WP-31): posted documents immutable (DB triggers, REVOKE DELETE); corrections by
    credit note only; maker != checker; `doc_no` per `numbering_mode` (`external` default |
    `internal` gap-free; DC-10); GST split from the effective-dated `tax.hsn_rate` (none -> 422
    `HSN_RATE_MISSING`, never a default rate); CGST = SGST intra-state; import `validate_only` then
    `commit` (drafts only); dedup vs Shopify draft orders and Amazon Business orders. **No IRN /
    e-invoice, no e-way bill, no GST filing.** ⚠ tax settings UNVERIFIED until CA sign-off.

## Test policy
- Tests before or with code; name by register ID (`@pytest.mark.req("REQ-021")`,
  `describe("REQ-021")`). `api/tests/golden/test_vectors.py` parametrises over the 139 in-scope
  vectors only, none skipped (a calc whose WP has not merged: `xfail(strict=True)` naming that WP).
  The 16 vectors of the 14 omitted calcs carry the marker `omitted_v03` and run only in
  `engineering/reference_calcs.py`.
- Hypothesis invariants `test_invariant_*`: allocation conservation, ratio-of-sums, FIFO
  non-negative, FX round-trip, null propagation, unclassified in totals, period-close immutability,
  bounds never bypassed, ingest idempotent, refund single-count, compat == CM net profit,
  CGST = SGST, posted B2B immutable, B2B sale counted once, intercompany eliminated once, channel
  sum == account, actual xor estimate, facilitator tax nets to zero, channel fee conservation, ad
  spend single source.
- Contract cassettes under `api/tests/contract/CON-xx/cassettes/` are synthetic; `scan_cassettes.py`
  fails CI on order-id, ASIN, e-mail, token, GSTIN or store-domain hits; allow-list only
  `B0SYNTH\d{3}`, `SYNTH` GSTINs and `@example.test`; it also scans fixtures, `docs/`,
  `prompts/*.md` and `prompts/.claude/rules/*.md`.
- Security tests (`api/tests/security/`): RBAC scope matrix, HMAC, maker-checker, second-person
  kill switch, L2 stripping, SSRF, prompt injection, MCP read-only, read-only connector scopes.
- Playwright journeys incl. B2B maker != checker post, unified filters, Compat <-> CM toggle and five
  mobile journeys at 390x844; axe-core on every in-scope route; schemathesis on `/api/v1/openapi.json`.
- Coverage gates: `app/ledger`, `app/costing`, `app/profit`, `app/automation`, `app/b2b`, `app/tax`
  90 %; others 80 %; web 75 %.
- Report exact results: command, exit code, passed/failed/skipped, coverage, `git diff --stat`,
  `alembic heads`. `NOT RUN` is honest; "passed" without output is not.

## Safety (read-only pilot; writes gated)
- Agents and CI must not create, access or deploy to production; production is applied by a named
  human after gate approval (GitHub `prod` environment with required reviewers; one OIDC deploy role
  per AWS account; no long-lived keys). `RCI_ENV` = `local`, `test`, `dev` or `stage` only; never
  request or hold AWS credentials; Terraform is code only. No paid provisioning.
- Amazon: no restricted PII roles, no Restricted Data Token; if PII is ever held, purge <= 30 days.
  Shopify: Level 1 only. All connectors are read-only except CON-25 (repricer, R4) and CON-27
  (accounting API, R5). Ad platforms: read/report scopes, spend only.
- A write path is live only when its flag is `true` (`WRITES_PRICING` CON-25,
  `WRITES_ACCOUNTING_API` CON-27; default `false`) AND no `auto.kill_switch` row is engaged. No ads
  or review-request write path or flag exists. Never set a flag; enabling needs a recorded approval.
- Every external write goes through the WP-20 framework: simulation -> maker != checker approval
  -> canary -> idempotency key -> execution -> provider read-back before any retry; stale-data stop
  6 h for prices; bounds never bypassed. A database rollback never unsends.
  `auto.automation_execution` and `platform.audit_log` rows are never deleted.
- Kill switch disengage requires a second person (never the engager; no owner exception).
- Demo mode serves synthetic fixtures and blocks all writes.
- Missing credential, approval, dependency, unclear register entry or open DISC- item -> stop and
  list under BLOCKERS; do not work around. API facts come only from
  `integration/connector_contracts.md`; anything marked UNVERIFIED stays configurable.

## UI: visual parity profile (SOW §10.1, spec §12; unchanged in v0.3)
Keep Sellerboard's information architecture and interaction patterns: sidebar groups Profit /
Inventory / Money Back / Alerts / Channels / B2B / Settings (omitted marketing screens simply
disappear from navigation); tabs Tiles | Chart | P&L | Map | Trends; colour-coded period tiles with
a "More" P&L popover; tables with group-by, column picker, export; heatmap P&L with compare/YoY;
dark default with light toggle; unified channel chips (All | Amazon | Shopify | B2B | Walmart | eBay
| TikTok Shop as stores exist). Design tokens only (RAMA brand = token swap). Never copy the vendor
name, logo, icons, CSS, copy or screenshots; "Compat mode" label; Lucide icons only; colour-blind
safe status; mobile-first (WP-33); every number opens the lineage drawer (SCR-129); the
data-quality bar (SCR-130) is on every screen (`UNCLASSIFIED_FEE` shows there from R2; WP-17 alert
routing from R3). Automation log SCR-042 is `/automation/log` under Settings. Ad alerts are
spend-only (`AD_SPEND_MISSING`, `AD_SPEND_SPIKE`); no PPC recommendation category.

## Using the register
`engineering/scope_register.json` (v0.3): `work_packages`, `retired_work_packages`, `features`
(`wp`, `screens`, `calcs`, `connectors`, `disposition` IN | CONDITIONAL | NA | OMITTED),
`requirements` (REQ-001..193; `priority` MUST | OMITTED), `screens`, `calculations` and
`connectors` (each with `scope` IN | OMITTED). Filter features by `wp` and drop OMITTED for a task's
IDs. CONDITIONAL features are flag-gated with fixture-only paths until a human confirms the
dependency. Run `python engineering/check_register.py` and `python engineering/reference_calcs.py`
before and after every change; both are CI gates.

## Workflow
Explore -> plan (files, tests, migration) -> implement -> run the listed commands -> commit on
`wp-XX/<slug>` with WP and REQ IDs -> PR `WP-XX: <title>` with exact output, test counts, coverage,
diff stat, REQ/GV coverage and BLOCKERS. Rebase on main; never force-push; preserve others'
changes. The developer reviews every PR; Codex review (`@codex review` + automatic review) applies
the rules below; `@codex fix the P1 issue` for confirmed findings, then the developer re-reviews.

## Code Review Rules
Report only P0/P1. Nested AGENTS.md files add rules for their directories.
**P0 (block merge)**
- Money: float or binary arithmetic on amounts, rates or FX; `round()` or quantising before the
  storage/presentation boundary; wrong rounding mode (HALF_EVEN presentation, CEILING floors); a
  money column or wire field without currency; a money value serialised as a JSON number.
- Sign conventions: a compat line with the wrong sign, a refund or fee counted twice, facilitator
  tax added to Sales, an unmapped fee dropped instead of Unclassified, compat != CM net profit.
- Writes without flags: any external mutating call outside the WP-20 framework, any path not gated by
  `WRITES_PRICING` / `WRITES_ACCOUNTING_API` + `auto.kill_switch`, a flag defaulting to `true`,
  maker == checker allowed, a write scope requested from any read connector or ad platform.
- Secrets: a token, key, password, refresh token or real credential in code, config, fixtures,
  cassettes, logs, docs or PR text; a new per-provider secret env var; AWS credentials in CI PR jobs.
- PII: buyer names, e-mails, addresses or phone numbers persisted, logged or placed in fixtures;
  Shopify Level 2 fields requested; restricted Amazon PII roles or RDT requested; real ASINs,
  order IDs or GSTINs outside the `B0SYNTH\d{3}` / `SYNTH` / `@example.test` allow-list.
- Golden vectors or `scope_register.json` edited (or a vector skipped/xfailed without owner) to make
  a test pass. Exempt: the `omitted_v03` marker on vectors of omitted calcs.
- Omitted marketing scope built: PPC/campaign analytics, bids/budgets/negatives, day parting,
  search terms, attribution or customer journeys, review requests/Solicitations, Klaviyo, the
  Bing/Snapchat/Pinterest/Taboola ad connectors, TikTok Ads data beyond spend, or any route for an
  OMITTED screen.
- Retired work packages: code, branches or prompts for WP-18, WP-19 or WP-21 (retired — marketing
  omitted v0.3).
- Production: anything that creates, accesses or deploys to production from an agent or CI job;
  a destructive migration (DROP/TRUNCATE/rename/narrow).
**P1 (fix before merge)**
- Missing REQ-marked test for a requirement the WP owns; a listed golden vector not replayed;
  coverage below the gate; `check_register.py` or `reference_calcs.py` failing.
- Null coerced to zero on missing/stale data; ratios not computed as ratio of sums; FX converted in
  event tables; hard-coded marketplace id, endpoint, currency, timezone or tax rate; a tax-regime
  value outside the canonical enum; ad spend counted from both connector and settlement.
- Ad-platform data other than spend persisted or projected; platform-reported sales shown anywhere.
- An API fact (endpoint, version, scope, quota) not in `integration/connector_contracts.md` and not
  flagged as a DISC- BLOCKER.
- Migration without tested downgrade or more than one alembic head; error response outside the
  envelope; missing `workspace_id` or permission-scope filter.

## Session continuity (local development)
At the start of every session read `docs/knowledge-bank/STATUS.md` and
`docs/knowledge-bank/ARCHITECTURE.md` before exploring application code. Read
`docs/knowledge-bank/DECISIONS.md` when changing architecture or scope. These are
navigation and progress notes; the register and specifications remain authoritative.
Inspect the current files and working state for the task, then read only the relevant
specification sections. Do not assume status notes prove implementation or acceptance.
Before ending a session update STATUS.md (what works, checks actually run, blockers,
next concrete step) and append a dated entry to CHANGELOG.md. Update ARCHITECTURE.md
and DECISIONS.md when relevant. Never mark a work package complete until its gates pass.
The user authorized local implementation on 2026-10-12; cloud setup instructions in
the handoff describe a later delivery route. Do not request renewed permission for
ordinary local work. Human discovery/acceptance and production gates still apply.
