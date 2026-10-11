# Connector Contracts — CON-01 … CON-33

**Version:** v0.3 DRAFT — NOT APPROVED · **Cutoff:** 2026-10-10 (baseline v0.1 2026-09-10; v0.3 Owner decisions 2026-10-10, `research/v02/V03_BRIEF.md`) · **Companion:** `docs/05_Engineering_Specification.md`, `integration/source_manifest.csv` · **Scope source:** `engineering/scope_register.json` v0.3 (31 connectors CON-01..29 and CON-32/33 — 22 in scope, 9 OMITTED (v0.3 rev 2: CON-11 TikTok Ads re-added as spend-only, CONDITIONAL, R2) — plus conditional write stubs CON-30/31; the only write connectors in scope are CON-25 repricer (R4, behind the WP-20 framework) and CON-27 accounting export (R5)) · **Sources:** S20–S49 (S45 Finances API, S46 retention, S49 FAQ), OBS, OBS-R (`research/v02/authorized_audit_io_and_com_2026-10-10.md`, formulas reconciled), `research/v02/formula_research_*.md`

**v0.3 changes in this file (2026-10-10):**
- **Marketing omitted.** CON-03, CON-04, CON-10, CON-12..CON-15, CON-24 and CON-26 are marked **OMITTED v0.3 (marketing)** (heading kept, one-line body). The review-request work package WP-18 and the PPC work packages WP-19 and WP-21 are retired (marketing omitted v0.3).
- **v0.3 rev 2 (review 2026-10-10):** CON-11 TikTok Ads is back as **spend-only, CONDITIONAL, R2 (WP-23)** because TikTok Shop ad spend is billed through TikTok Ads, not shop settlements; CON-16 adds the per-ad-account `spend_source` rule (connector | settlement, never both; GV-155), WFS inventory and inbound shipments for the planner (F-G11) and Walmart / eBay report pages (F-J08); CON-01 adds Pan-EU / EFN and Remote Fulfillment fee codes, pooled FBA stock and stock-transfer VAT flags (F-A12, PROPOSED + CA).
- **Ad platforms are read for SPEND only.** CON-02 (Amazon Ads), CON-08 (Google Ads), CON-09 (Meta), CON-11 (TikTok Ads, rev 2) and the Walmart Connect / SEM part of CON-16 request read/report scopes only and persist spend only; no campaign analytics, conversions or platform-reported sales; no write scope.
- **All markets.** CON-01 now covers every Amazon marketplace in the NA, EU and FE regions through the marketplace master and multi-region authorisation of WP-38 (R2). **CON-16, CON-17, CON-18 move to R2** (WP-23) with fuller contracts; **CON-19..CON-22 are R5** (WP-39). The CON-01 day-parting read data is removed.
- **New discovery items:** DISC-35 (marketplace master facts), DISC-36 (Walmart), DISC-37 (eBay), DISC-38 (TikTok Shop), DISC-39 (operations connectors). DISC-08, DISC-09, DISC-15, DISC-22 and DISC-30 are closed as omitted.

**v0.2 changes in this file:**
- **CON-01:** adds day-parting read data (removed in v0.3 — marketing omitted).
- **CON-05:** now **R1**. Adds the India store via WP-12, draft-order channel handling, order exclusion rules, and the gateway fee table with Shopify Payments "Auto".
- **CON-06:** now **R1**.
- **New contracts:** **CON-32** (courier/3PL cost source) and **CON-33** (internal B2B lead pipeline, read-only).
- **New discovery items:** DISC-29..34.
- **Review fixes (2026-10-10):** **CON-02, CON-08 and CON-09 are now R1, read-only, through WP-37** (ad spend for the R1 compat Advertising line, blended ROAS/POAS, expense bases and the parallel run); CON-02 search-term/PPC analytics (WP-19, now retired — marketing omitted v0.3) are not built. CON-01 R0 scope is the Amazon.in seller account (EU endpoint); UK in R2. Amazon PII rule reworded. CON-05 uses a custom app created through the currently supported path (DISC-10). Storage is AWS S3 ap-south-1 (DC-01 decided 2026-10-10).
- **Identifier convention:** DISC-xx in this file ≡ DISCOVERY-xx in the specification.

How to read this file
- Every fact carries a source ID (S20–S40, "Extra" = research addendum, OBS = authorized audit) or is marked **Planning assumption** / **DISCOVERY-xx**. Nothing else is asserted.
- "Documented" URLs are the official pages the research consulted. Where the research recorded that the official page did not render (Amazon Ads S33/S34, Amazon Attribution), the connector is **Unverified**.
- Costs: SP-API **$0** — Amazon "will not move forward with the SP-API usage and annual fees at this time" (S35); planning assumption $0, monitor. All other providers: planning assumption unless stated.
- Manual CSV/XLSX fallback exists for every read connector through `POST /uploads` (untrusted content, fixed schema per object).
- Discovery items are numbered **DISC-01 … DISC-39** (DISC-29..34 new in v0.2, DISC-35..39 new in v0.3) and consolidated at the end.
- Facts about Walmart, eBay and TikTok Shop APIs are kept generic unless the package's sources state them; every unverified item is a DISC- entry and a BLOCKER for the implementing task, never a guess.

Global notes that apply across connectors (stated explicitly as required):
1. **Shopify orders older than 60 days** need the `read_all_orders` scope, granted case-by-case after an approval request (S20; Partner Dashboard at research time — the current request path for our app type is confirmed in DISC-10). Until granted, backfill stops at 60 days.
2. **Amazon Ads needs its own access evaluation** (LWA security profile, Partner Network console, approvals ~2–3 business days per third-party sources; official page not rendered — S33, UNVERIFIED). v0.3: request reporting (read) access only; spend is the only data used.
3. **No claims-submission API is assumed** for reimbursements; Sellerboard itself directs users to Seller Support (OBS); our Money Back module records manual case IDs.
4. **Subscription contracts only via the app of record**: Shopify exposes `read_own_subscription_contracts` (the app's own records) and no read-all scope (S20); otherwise repeat orders are labelled `REPEAT_ORDERS`, never "subscription" (GV-037).
5. **Amazon Attribution** is omitted v0.3 (marketing); its unverified API status (Extra) no longer matters.
6. **Agent environments never hold provider credentials.** Codex cloud environments (and any developer sandbox) have no marketplace, ad-platform, Shopify or AWS credentials; contract tests run on recorded, post-processed synthetic cassettes. Live access exists only in the AWS accounts' secret store, set by humans.

Template per connector: Docs · Version · Auth/roles/regions · Source fields/grain/currency/timezone · Pagination/history · Quotas · Webhooks · Backfill/replay · Latency/freshness · Revocation · Protected data/retention · Cost · Manual fallback · Read vs write · Acceptance evidence · Unknowns.

---

## CON-01 — Amazon SP-API (Orders, Finances, Reports, FBA Inventory, Fulfillment Inbound, Sales, Listings read) — R0, core, **read**

**Docs (Documented):** SP-API welcome https://developer-docs.amazon.com/sp-api/docs/welcome (S27, dateModified 2026-09-09; `.com` URLs 302 → developer-docs.amazon). Private developer registration path: Seller Central → Apps and Services → Develop Apps (S28). Roles page (S29). Reports API v2021-06-30 reference (S30). Finances v2024-06-19 and v0 (Extra). FBA Inventory `getInventorySummaries` (Extra). Sales `getOrderMetrics` (Extra). Exact URL slugs for the reference pages under `developer-docs.amazon.com/sp-api/docs/` are to be pinned in DISC-01.
**Versions:** Reports **v2021-06-30** (S30). Finances **v2024-06-19** `listTransactions` and **v0** `listFinancialEvents` (S45/Extra). Orders API version: **DISCOVERY-02** (not captured in research). FBA Inventory API version: **DISCOVERY-02**. Fulfillment Inbound version: **DISCOVERY-25**. Sales API `getOrderMetrics` version: DISCOVERY-02. Listings Items read version: DISCOVERY-17.
**Auth / roles / regions:** LWA OAuth; developer type **private** (S27/S28). Registration: select roles, describe use case & security, agree Solution Provider Agreement, AUP, Data Protection Policy; Amazon case, 5-day response window (S28). Roles requested (unrestricted, S29): Finance and Accounting, Inventory and Order Tracking, Amazon Fulfillment, Selling Partner Insights, Pricing, Product Listing, Notifications. (Brand Analytics is no longer requested — CON-03 omitted v0.3.) **Restricted PII roles (Direct-to-Consumer Shipping, Tax Invoicing, Tax Remittance, Professional Services) are NOT requested** (S29). Regional endpoints NA, EU, FE (S27); mapping US→NA, UK/FR/DE/IN→EU is a **planning assumption; confirm in DISC-01** — one LWA refresh token per seller account per region; Rama IN and PWF UK observed as separate seller accounts (OBS). **R0/R1 scope: register and authorise the Amazon.in seller account (EU endpoint) for R0. R2 (WP-38): UK/US/FR/DE and every other Amazon marketplace in the NA, EU and FE regions, configured from the marketplace master (spec §3.15) — one private developer app, one LWA refresh token per seller account per region (`credential_ref` per region), per-region rate-limit buckets; marketplace ids, endpoints per region, currencies, timezones and tax regimes are seed data verified under DISC-35.** No Restricted Data Token (RDT) is requested; region attribution (CALC-111) uses region-level reports or `unknown` (spec §3.14). **Cross-border fulfilment (v0.3 rev 2, F-A12, R2, PROPOSED + ⚠ CA):** Pan-EU / EFN and Remote Fulfillment fees arrive as Finances fee codes and map through the marketplace's `fee_code_map_version` (unknown → Unclassified, `UNKNOWN_FEE_CODE`); FBA stock pooled across marketplaces is counted once per pool (CALC-092); cross-country stock transfers are flagged `VAT_STOCK_TRANSFER` for the CA, not computed. Exact fee-code and report names are DISC-35.
**Source objects, grain, currency, timezone:**
| Object | API / report type | Grain | Currency field | Timezone |
|---|---|---|---|---|
| Orders + items | Orders API `getOrders`/`getOrderItems` (family listed S27; ver. DISC-02) | order / order item | `OrderTotal.CurrencyCode`, item `ItemPrice.CurrencyCode` | UTC ISO-8601; store TZ applied at projection |
| Financial events | Finances v2024-06-19 `listTransactions`; v0 `listFinancialEvents` (S45/Extra) | transaction / event component | per component `CurrencyAmount.CurrencyCode` | UTC `PostedDate` |
| Settlements | Report `GET_V2_SETTLEMENT_REPORT_DATA_FLAT_FILE_V2` — **scheduled/system-generated only, cannot be requested** (S30) | settlement line | `currency` column | report header dates; settlement period |
| FBA inventory | `getInventorySummaries` (Extra); report `GET_FBA_INVENTORY_PLANNING_DATA` (S30) | SKU × FC / SKU | n/a | snapshot ts |
| Inventory ledger | `GET_LEDGER_SUMMARY_VIEW_DATA` (+ detail) (S30) | SKU × day × event | n/a | marketplace local date |
| Estimated fees | `GET_FBA_ESTIMATED_FBA_FEES_TXT_DATA` (S30) | SKU | marketplace currency | snapshot |
| Reimbursements | `GET_FBA_REIMBURSEMENTS_DATA` (S30) | reimbursement id | marketplace currency | approval date |
| Sales & traffic | `GET_SALES_AND_TRAFFIC_REPORT` (S30) | ASIN × day | marketplace currency | marketplace local date |
| Order metrics | Sales `getOrderMetrics` (Extra) | interval (Hour/Day/…) | marketplace currency | requested TZ |
| Inbound shipments | Fulfillment Inbound family (S27; ver. DISC-25) | shipment / item | n/a | UTC |
**Pagination / history limits:** Finances `PostedAfter/PostedBefore` ≤180 days apart, chain windows backwards; last 48 h may be missing (S45/Extra). `getInventorySummaries` `startDateTime` within 18 months (Extra). `getOrderMetrics` Hour granularity ≤30 days back, other granularities ≤2 years (Extra). Report documents retained **90 days by default** (S30) → settlement reports must be captured continuously; older settlements only via Seller Central manual download. Orders API history limit: DISC-02. Reports use `createReport → getReport (poll) → getReportDocument` (S30) with `nextToken` on list endpoints.
**Quotas / rate limits:** `listTransactions` 0.5 rps / burst 10; `listFinancialEvents` 0.5 rps / burst 30 (S45/Extra); `getInventorySummaries` 2 rps; `getOrderMetrics` 0.5 rps (Extra). Orders/Reports/Inbound limits: DISC-02. Usage plans & rate limits are per SP-API docs (S27); implement per-endpoint token buckets; honour `x-amzn-RateLimit-Limit` header and 429.
**Webhooks:** Notifications API family exists (S27); subscriptions (SQS/EventBridge) for report processing finished / listing changes: **DISCOVERY-26**. R0 uses polling.
**Backfill / replay:** R0 target 90 days (scope register). Finances: chained 180-day windows; Orders: by `LastUpdatedAfter` cursors; Reports: date-ranged requests where the report type accepts ranges; settlement: only what Amazon has generated in the last 90 days + manual upload. Replay from `raw_payload` with `cause='replay'`.
**Latency / freshness:** Orders 30 min SLO; Finances 6 h SLO with expected 48 h provider lag (S45); settlement per Amazon cadence (typically bi-weekly — planning assumption, DISC-04); reports 24 h.
**Revocation:** Refresh-token failure → connector `revoked`, jobs cancelled, alert; PII (none held) deletion within 30 days of revocation required by DPP (Extra); re-authorization via Seller Central app authorization.
**Protected data / retention:** **Do not request restricted PII roles; if ever held, purge ≤ 30 days after delivery / revocation** (Data Protection Policy, Extra). We hold no buyer PII (no restricted roles, no RDT); order rows keep `ship_country`/`ship_region` only. Report documents are stored in S3 ap-south-1 with lifecycle rules per prefix (PII-free settlement/finance documents: Object Lock compliance mode, 7 years — spec §9.6); in-app data retention beyond 18 months is a workspace setting (OBS/S46). Annual security review is part of the private developer agreement (S28) — DISC-01 to confirm obligations.
**Cost:** **$0** at this time (S35). Monitor; if fees return, the Nov-2025 plan was $1,400/yr + usage tiers (S35, cancelled May 2026).
**Manual fallback:** Seller Central report downloads (settlement flat file, inventory ledger, reimbursements, sales & traffic) as CSV/TSV/XLSX → `POST /uploads` with the same normalizers (report-type keyed).
**Read vs write:** read-only. The only Amazon write connector in scope is CON-25 (repricer, R4); CON-24 is omitted v0.3.
**Acceptance evidence:** (a) private developer app approved with the listed roles (screenshot of Develop Apps page, redacted); (b) recorded cassettes (synthetic IDs/amounts, CI-scanned) per report type and per Finances event type Shipment/Refund/ServiceFee/Adjustment (S45/Extra); (c) 90-day backfill completed for the IN store (Amazon.in seller account, EU endpoint) with `sync_job` success — UK store at R2; (d) settlement bridge reconciled to ≤0.01 for one full settlement per store (GV-034 logic); (e) contract tests green; (f) rate-limit test with injected 429.
**v0.2 day-parting read data — removed v0.3 (marketing omitted).** No `ads.daypart_heatmap` and no hourly order aggregation job are built.

**Unknowns:** DISC-01 (registration outcome, roles granted, exact reference URLs), DISC-02 (Orders/Inventory/Reports/Sales API versions and rate limits), DISC-03 (v2024-06-19 vs v0 field coverage for IN, GST/TCS components), DISC-04 (settlement cadence and V2 flat-file availability on Amazon.in), DISC-05 (sandbox availability for stage), DISC-06 (Sales & Traffic per marketplace), DISC-25 (Inbound API version), DISC-26 (Notifications), DISC-35 (marketplace master facts per marketplace). Amazon Business order flag field (`is_business_order`, used by CALC-100 dedup) is under DISC-02.

## CON-02 — Amazon Ads API — spend reporting only (SP/SB/SD v3: spend by campaign, advertised product, day) — **R1** (WP-37), core, **read** — **Unverified**

**v0.3 scope: SPEND only (marketing omitted).** Daily spend at campaign and advertised-product grain for SP, and campaign grain for SB/SD, per profile → `ads.ad_account`, `ads.ad_spend_day` (spec §3.13). It feeds CALC-079 (compat Advertising line), CALC-030/031 (TACOS, Real ACOS), CALC-059 (blended ROAS/POAS/MER) and CALC-091 (% of ad spend bases). **Reporting (read) access only; no write scope is requested; no keyword, target or search-term reports; impressions, clicks, conversions and platform-reported sales are not persisted.** The access application should be filed during R0 so spend is API-sourced for the R1 parallel run; until approved, the fixed-schema spend CSV fallback is used and labelled ESTIMATE (DISC-07).

**Docs:** https://advertising.amazon.com/API/docs/en-us/ — official page is a JS shell and did not render (S33). Third-party sources only (S33/S34).
**Version:** Reporting "v3" (third-party, UNVERIFIED) → **DISCOVERY-07**.
**Auth / access:** Separate access application: LWA security profile, Partner Network console, Direct Advertiser approvals ~2–3 business days (third-party, S33). Profiles per marketplace. **Amazon Ads needs its own access evaluation — not covered by SP-API registration.**
**Source fields / grain:** async report create → poll → download gzip JSON (S34); used grain: campaign and advertised product × day, spend only; currency = profile currency; timezone = profile timezone (assumption, DISC-07).
**Pagination / history:** SP lookback 95 days, SB/SD 60 days; restatements up to ~42 days (S34, UNVERIFIED).
**Quotas:** DISC-07. **Webhooks:** none assumed.
**Backfill / replay:** initial pull of full lookback per type; weekly re-request of trailing 45 days to capture restatements; rows superseded with `restated_at`.
**Latency:** daily; data restates. **Revocation:** token failure → revoked; re-auth.
**Protected data:** none (no PII). **Cost:** planning assumption $0 (no fee documented).
**Manual fallback:** Ads console report downloads (CSV/XLSX: date, campaign, spend, currency) → `POST /ads/spend-imports`.
**Read vs write:** read only. (The bid/budget write connector CON-26 is omitted v0.3.)
**Acceptance evidence:** access approval e-mail (redacted); recorded synthetic fixtures for SP/SB/SD spend reports; 60/95-day backfill; spend by profile × day matches the Ads console for one month; Advertising line reproduces GV-103; TACOS / Real ACOS reproduce GV-047/048; restatement re-pull supersedes rows (`restated_at`); scope test proves only reporting access is requested.
**Unknowns:** DISC-07 (official spec, versions, quotas, timezone, exact lookback windows).

## CON-03 — Amazon Brand Analytics / Search Terms (via Reports API) — OMITTED v0.3 (marketing)
**OMITTED v0.3 (marketing)** — removed from the build by the Owner on 2026-10-10 (research/v02/V03_BRIEF.md); not to be built, no credentials requested; kept as a heading for ID traceability only.

## CON-04 — Amazon Attribution — OMITTED v0.3 (marketing)
**OMITTED v0.3 (marketing)** — removed from the build by the Owner on 2026-10-10 (research/v02/V03_BRIEF.md); not to be built, no credentials requested; kept as a heading for ID traceability only.

## CON-05 — Shopify Admin GraphQL (orders, products, inventory, customers L1/L2, fulfillments) — **R1** (v0.2: India store in R1 via WP-12; UK/US/EU stores with R2 multi-market), core, **read**

**Local implementation facts (2026-10-12, first manual slice; not acceptance):**
Human-operated credential setup, multiple connections and direct paginated read
queries now target Admin GraphQL **2026-07** at
`https://{validated-shop}.myshopify.com/admin/api/2026-07/graphql.json`.
GraphQL operations validated against that version: shop/currentAppInstallation,
products, productVariants, inventoryItems, inventoryItem.inventoryLevels and
order/lineItems plus orders. Scope floor for this slice: read_orders/read_products/
read_inventory/read_locations; reject write_ scopes. No customer identity fields.
Shop.billingAddress.countryCodeV2 is validated but deprecated in this version;
only the country code is requested, not address fields. A future API upgrade must
verify its replacement. Currency/timezone come from Shop, never a guessed market.

Dev Dashboard client-credentials grant at `/admin/oauth/access_token` is supported
only when app and store share the same organization; client ID/secret exchange
returns an expiring token. Also accept a human-provisioned offline token from an
authorized existing installation. New OAuth install flow/refresh adapters are not
implemented. Per-connection credential_ref points to encrypted local devfile data;
no secrets in connector config. Current facts verified against official docs:
https://shopify.dev/docs/apps/build/authentication-authorization/client-credentials-grant
and https://shopify.dev/docs/apps/build/dev-dashboard/create-apps-using-dev-dashboard
and https://shopify.dev/docs/api/admin-graphql/2026-07/queries/inventoryItems .
Manual import is bounded to 60-day order creation history, with nested pagination;
bulk/webhook/Payments and scope approvals remain pending. DISC-10/29 stay open.

**Docs (Documented):** access scopes https://shopify.dev/docs/api/usage/access-scopes (S20); Order object https://shopify.dev/docs/api/admin-graphql/latest/objects/Order (S21, version 2026-07); bulk operations https://shopify.dev/docs/api/usage/bulk-operations/queries (S22); webhooks https://shopify.dev/docs/apps/build/webhooks (S23); protected customer data https://shopify.dev/docs/apps/launch/protected-customer-data (S24); versioning https://shopify.dev/docs/api/usage/versioning (S25); rate limits https://shopify.dev/docs/api/usage/limits (S26).
**Version:** Admin GraphQL **2026-07** (S21). Quarterly releases; stable versions 2025-07 … 2027-01; ≥12 months support; unsupported versions fall forward to the oldest supported (S25). Pin per connector in `ing.connector.api_version`; upgrade review each quarter. REST is legacy (S26) — not used.
**Auth / scopes:** custom app per store, created **through the currently supported path** (Shopify's app-creation path changed over time; DISC-10 confirms the current custom-app creation path and how `read_all_orders` is approved for it) — five stores (IN, UK, US, FR, DE — assumption: one shop per market, DISC-10). Scopes: `read_orders`, `read_all_orders` (**needed for orders older than 60 days; approval case-by-case** — S20; request path per DISC-10), `read_products`, `read_inventory`, `read_customers`, `read_fulfillments` (+ `read_merchant_managed_fulfillment_orders`/`read_assigned_fulfillment_orders`/`read_third_party_fulfillment_orders` variants, S20), `read_shopify_payments_payouts` and `read_shopify_payments_disputes` (CON-06). No write scopes.
**Source fields (S21):** Order: `displayFinancialStatus`, `displayFulfillmentStatus`, `totalPriceSet`, `subtotalPriceSet`, `totalTaxSet`, `currentTotalDiscountsSet`, `totalShippingPriceSet`, `netPaymentSet`, `totalRefundedSet`, `refunds[]`, `transactions[]`, `taxLines[]`, `currencyCode`, `presentmentCurrencyCode`, `createdAt`, `processedAt`, `cancelledAt`, `updatedAt`; MoneyBag has `shopMoney` + `presentmentMoney`. (v0.3: `customerJourneySummary` / UTM attribution is not requested or stored — F-E11 omitted, marketing.) We store shop money as `order_*` amounts with `currency=currencyCode` and `presentment_currency`. Grain: order / line item / refund / transaction. Timezone: ISO-8601 with offset; shop timezone in `shop.ianaTimezone`.
**Pagination / history:** cursor pagination (`pageInfo.endCursor`) for incremental; **bulk operations** for backfill: `bulkOperationRunQuery` → poll or `bulk_operations/finish` webhook → JSONL; from 2026-01 up to 5 concurrent per shop; max 5 connections, 2 nesting levels; must finish in 10 days; result URL expires 1 week (S22). History: 60 days without `read_all_orders` (S20).
**Quotas:** GraphQL calculated cost; restore rates Standard 100 pts/s, Advanced 200, Plus 1,000, Enterprise 2,000; single query cost cap 1,000 (S26). Read `extensions.cost.throttleStatus` and back off. Plan per store: DISC-10.
**Webhooks (S23):** topic list `orders/create`, `orders/updated`, `orders/cancelled`, `refunds/create`, `fulfillments/update`, `inventory_levels/update`, `products/update`, `app/uninstalled` is a **planning assumption; confirm exact topic names in DISC-10**; `bulk_operations/finish` (S22) and GDPR `customers/data_request`, `customers/redact`, `shop/redact` (S24) are documented. Receiving route: `POST /webhooks/shopify/{connector_id}`. Signature `X-Shopify-Hmac-SHA256` = base64 HMAC of raw body with the app client secret; 1 s connect / 5 s total timeout; must return 200; 8 retries over 4 hours; subscription deleted after 8 consecutive failures; dedupe by `X-Shopify-Webhook-Id`; ordering not guaranteed → nightly reconciliation by `updated_at` (S23). Delivery HTTPS (PubSub/EventBridge optional).
**Backfill / replay:** bulk JSONL per object type into `raw_payload` (S3 ap-south-1, DC-01); replay from stored JSONL. Backfill beyond 60 days blocked until `read_all_orders` granted (`BACKFILL_LIMIT`).
**Latency:** webhooks minutes; reconciliation nightly. **Revocation:** app uninstall → `app/uninstalled` webhook (planning assumption, DISC-10) / 401 → connector `revoked`; `shop/redact` handled within 30 days (S24).
**Protected data / retention (S24):** Level 1 (customer data excluding name/address/phone/e-mail) vs Level 2; requirements minimization, purpose limitation, consent, retention, encryption; L2 additionally encrypted backups, environment separation, DLP, access logs, incident response. Custom apps: L1/L2 available; L2 availability varies by plan and app type (DISC-10); unapproved fields return `null`. **We request L1 only**; identity hashed per market; GDPR webhooks completed within 30 days.
**Cost:** planning assumption $0 (custom app; plan cost already borne).
**Manual fallback:** Shopify admin CSV exports (orders, products, inventory) → uploads.
**Read vs write:** read-only. (Inventory/listing writes are out of scope; MCP/assistant write tools are not used by the application.)
**Acceptance evidence:** scopes screenshot per store; `read_all_orders` request submitted and outcome recorded; HMAC verification test with a recorded webhook; bulk op fixture (JSONL) for orders/products/inventory; 60-day (or full, if approved) backfill; order count reconciliation vs Shopify Analytics for one month per store; unapproved-field `null` handling test.
**v0.2 — Sales channels and draft orders (OBS-R: the dashboard filter lists "Online store, Other sales channels, Draft orders" and an import app; draft orders are counted as sales in the audited configuration — finding #4):**
- **Mapping.** Each order's sales channel (source) is mapped to `order_header.sales_channel_detail` ∈ {`online_store`, `draft_orders`, `pos`, `other_app:<name>`}. The exact GraphQL field(s) identifying the channel/app and the originating draft order, and how the draft-order name or PO reference is exposed (draft order name, note, custom attributes, PO number), are **not in the research → DISC-29**. The fallback is the Shopify admin orders CSV export with its channel column.
- **Draft-order policy** is set per store via `cost.order_inclusion_rule` with `rule_type='channel'`, `value='draft_orders'`, and one of three actions:
  1. **include** as D2C. This is the default only in parallel-run `sellerboard_mirror` mode.
  2. **`rechannel_b2b`** (PROPOSED default for stores where B2B orders are keyed as draft orders): the order is excluded from Shopify sales, and the B2B invoice for the same reference is the record of truth.
  3. **exclude.**
- **Two-sided dedup is always active (CALC-100, GV-113).** A B2B invoice whose `external_ref` equals a draft-order-channel order's `external_reference` is blocked. A draft-order-channel order arriving after a posted B2B invoice with the same reference is auto-excluded (`b2b_duplicate_auto`) with an alert. A sale is never counted twice.

**v0.2 — Order exclusion rules (CALC-090, GV-130, SCR-136):**
- Rules are by status (e.g., cancelled), channel, or tag (e.g., a COD-cancel tag, as observed). They are evaluated at **projection**, not at ingestion: every order stays in the ledger and in raw.
- `retain_costs=true` by default, so courier/RTO/payment costs of excluded orders are kept. This fixes finding #5, where tag-only exclusion dropped RTO costs. RTO itself is detected from fulfilment/courier events (CON-32, CALC-104), not only from tags.
- Changing a rule triggers a rebuild of the affected days.

**v0.2 — Payment fees and the gateway table (CALC-022, GV-136, SCR-135):**
- **Table.** `cost.payment_gateway` per store: gateway code (normalised transaction gateway name from `transactions[]`, S21), payment method (prepaid/COD), `shopify_fee_pct` (platform third-party transaction fee), `gateway_pct`, `fixed_fee`, `gst_on_fee_pct`, and `mode`.
- **"Auto" mode.** The fee is the **actual** fee: Shopify Payments `BalanceTransaction.fee` via CON-06 (R1), or PayPal/Razorpay/Stripe via the CON-07 settlement CSV. Until the actual arrives, the rule estimate is applied and labelled ESTIMATE (GV-020/021). Actual replaces estimate on arrival.
- **Unmapped gateway names** raise `GATEWAY_UNMAPPED` and use the store default rule.
- **OBS-R:** the audited store's Payment fees rows are per gateway plus "Other transaction fees". Shopify Payments availability for the India store is **DISC-11** (if it is unavailable, "Auto" for IN relies on CON-07).
- **Tax lines.** `taxLines[]` (S21) are split by head (IGST/CGST/SGST) for CALC-052. Intra-state orders with CGST ≠ SGST raise `GST_CGST_SGST_MISMATCH` (finding #2).

**v0.2 — Tracking numbers.** Fulfillment tracking numbers (AWB) and carrier come from `fulfillments` (`read_fulfillments`, S20). Exact field names are under DISC-10/29. They are written to `ledger.fulfilment_tracking` for CON-32 matching.

**Unknowns:** DISC-10 (plans per store, current custom-app creation path, `read_all_orders` approval path and outcome, L1 approval for our app type), DISC-13 (subscription app of record), DISC-29 (sales-channel / draft-order / PO-reference fields).

## CON-06 — Shopify Payments payouts & balance transactions — **R1** (v0.2, with CON-05; per-store availability DISC-11), core, **read**

**Docs:** scopes (S20); Payout fields `issuedAt`, `net`, `status`, `summary`; BalanceTransaction fields `amount`, `fee`, `net`, `type`, `associatedOrder` (Extra). Object reference under https://shopify.dev/docs/api/admin-graphql/latest/objects/ShopifyPaymentsPayout (path to verify, DISC-11).
**Version:** Admin GraphQL 2026-07 (as CON-05). **Scopes:** `read_shopify_payments_payouts`, `read_shopify_payments_disputes` (S20).
**Grain:** payout; balance transaction (per order/refund/adjustment). **Currency:** payout currency (shop payout currency). **Timezone:** `issuedAt` ISO-8601.
**Pagination / history:** cursor; history per Shopify Payments availability (DISC-11). **Quotas:** as CON-05. **Webhooks:** none assumed for payouts; poll daily.
**Backfill:** full history by cursor. **Latency:** 24 h SLO. **Revocation:** as CON-05. **Protected data:** none beyond order linkage. **Cost:** $0.
**Manual fallback:** Payouts CSV export from Shopify admin → uploads; **gateway fees for stores without Shopify Payments (likely IN — Razorpay etc.) come from CON-07**.
**Read vs write:** read.
**Acceptance:** payout bridge (`Payout.summary` vs Σ `BalanceTransaction`) reconciled for two payouts per store; `BalanceTransaction.fee` replaces estimated gateway fee (GV-020).
**Unknowns:** DISC-11 (Shopify Payments availability per store/market, especially IN; disputes fields).

## CON-07 — Other payment gateways (Razorpay / PayPal / Stripe) — fee import — R2, conditional, **read**

**Docs:** Not in research (PROP). Provider developer portals to be confirmed in **DISCOVERY-12**.
**Version:** DISC-12. **Auth:** API keys per gateway (stored in Secrets Manager). **Grain:** payment / settlement line. **Currency:** gateway settlement currency (INR for Razorpay; PayPal/Stripe per account). **Timezone:** provider.
**Pagination/history/quotas/webhooks:** DISC-12. **Backfill:** CSV first. **Latency:** daily. **Revocation:** key invalid → revoked. **Protected data:** payer e-mail/name present in gateway exports — strip at upload; only order reference, amounts, fee, tax kept. **Cost:** $0 (assumption).
**Manual fallback (DEFAULT for R2):** gateway settlement CSV → uploads with fixed schema `{payment_id, order_ref, captured_amount, fee, tax_on_fee, net, currency, settled_at}`.
**Read vs write:** read. **Acceptance:** one month of gateway fees loaded per store; fee actual replaces estimate (CALC-022).
**Unknowns:** DISC-12.

## CON-08 — Google Ads — spend only — **R1** (WP-37), extended, **read**
**v0.3 scope: SPEND only (marketing omitted).** Read-only reporting scope; cost by account/campaign × day into `ads.ad_spend_day`, mapped to the Shopify store(s) through `ads.ad_spend_mapping` (spec §3.13); feeds CALC-079/CALC-059/CALC-091. No clicks, conversions or UTM join are persisted. Developer-token and OAuth setup is a Rama action before WP-37 starts (DISC-18); CSV fallback until then.
**Docs:** not in research (S01/S02 mention integration only). Official portal to confirm: DISC-18. **Version:** DISC-18. **Auth:** OAuth (scope register note); developer token; read-only reporting scope. **Grain used:** account/campaign × day, cost; **currency:** account currency; **timezone:** account timezone. **Limits/quotas:** DISC-18. **Webhooks:** none. **Backfill:** by date range. **Latency:** daily. **Revocation:** OAuth revoke → revoked. **Protected data:** none. **Cost:** $0 assumption. **Fallback:** Google Ads report CSV → spend import (`date, account, campaign, spend, currency`). **Read/write:** read. **Acceptance:** cost by campaign/day matches the console for one month; spend cassettes synthetic and CI-scanned; Advertising line GV-103; scope test proves read-only. **Unknowns:** DISC-18.

## CON-09 — Meta (Facebook/Instagram) Ads — spend only — **R1** (WP-37), extended, **read**
**v0.3 scope: SPEND only (marketing omitted).** Read-only insights; spend by ad account/campaign × day into `ads.ad_spend_day` with store mapping (spec §3.13). Reported conversions and values are not persisted. Token setup is a Rama action before WP-37 starts (DISC-18); CSV fallback until then.
**Docs:** not in research; Marketing API insights (scope register). DISC-18. **Version:** DISC-18. **Auth:** OAuth system-user token with read-only ads permission. **Grain used:** ad account/campaign × day, spend. **Currency:** ad account currency; **timezone:** ad account timezone. **Limits:** DISC-18. **Webhooks:** none. **Backfill:** date ranges. **Latency:** daily. **Revocation:** token expiry → revoked. **Protected data:** none. **Cost:** $0. **Fallback:** Ads Manager CSV → spend import. **Read/write:** read. **Acceptance:** spend matches Ads Manager for one month; scope test proves read-only; no conversion field in `ads.ad_spend_day`. **Unknowns:** DISC-18.

## CON-10 — Microsoft / Bing Ads — OMITTED v0.3 (marketing)
**OMITTED v0.3 (marketing)** — removed from the build by the Owner on 2026-10-10 (research/v02/V03_BRIEF.md); not to be built, no credentials requested; kept as a heading for ID traceability only.

## CON-11 — TikTok Ads — spend only — **R2** (WP-23), **CONDITIONAL**, **read** (v0.3 rev 2)
**v0.3 rev 2 scope: SPEND only.** Re-added after the independent review: TikTok Shop ad spend is billed through TikTok Ads, not the shop settlement, so the TikTok Shop (and Shopify) Advertising line needs it (F-K11). Daily spend per advertiser account (account × day; campaign × day only where needed for store mapping) into `ads.ad_account` / `ads.ad_spend_day` (`platform='tiktok_ads'`, spec §3.13), mapped to stores through `ads.ad_spend_mapping`; feeds CALC-079 / CALC-059 / CALC-091. **Read/report scope only; no write scope; impressions, clicks, conversions and platform-reported sales are not persisted;** no campaign analytics (marketing stays omitted).
**Docs:** not in research — portal, API version, report endpoint, scope names, token model and quotas are **UNVERIFIED → DISC-18**. **Auth:** OAuth per advertiser account; `credential_ref` only. **Currency / timezone:** account currency and timezone as reported; day kept as reported (`AD_TZ_MISMATCH` info flag). **Backfill / replay:** by date range, raw-first; restatement window DISC-18. **Revocation:** token invalid → `revoked` (RB-01). **Cost:** $0 planning assumption.
**Fallback (default until access is confirmed):** the fixed-schema spend CSV (`POST /ads/spend-imports`, `platform=tiktok_ads`) — rows `source='csv_upload'`, labelled **ESTIMATE** ("est."), superseded by API rows for the same account × day. A mapped account-day with no spend fails `AD_SPEND_MISSING` (incomplete, never zero).
**CONDITIONAL:** the API client is built behind a flag with fixture-only paths until a human confirms access (DISC-18); the CSV path is always available.
**Acceptance:** synthetic cassettes; spend lands only on the Advertising line (never as sales, REQ-162); the scope test asserts read/report scopes only; CSV rows show "est." and are superseded by API rows.
**Unknowns:** DISC-18.

## CON-12 — Snapchat Ads — OMITTED v0.3 (marketing)
**OMITTED v0.3 (marketing)** — removed from the build by the Owner on 2026-10-10 (research/v02/V03_BRIEF.md); not to be built, no credentials requested; kept as a heading for ID traceability only.

## CON-13 — Pinterest Ads — OMITTED v0.3 (marketing)
**OMITTED v0.3 (marketing)** — removed from the build by the Owner on 2026-10-10 (research/v02/V03_BRIEF.md); not to be built, no credentials requested; kept as a heading for ID traceability only.

## CON-14 — Taboola — OMITTED v0.3 (marketing)
**OMITTED v0.3 (marketing)** — removed from the build by the Owner on 2026-10-10 (research/v02/V03_BRIEF.md); not to be built, no credentials requested; kept as a heading for ID traceability only.

## CON-15 — Klaviyo — OMITTED v0.3 (marketing)
**OMITTED v0.3 (marketing)** — removed from the build by the Owner on 2026-10-10 (research/v02/V03_BRIEF.md); not to be built, no credentials requested; kept as a heading for ID traceability only.

## CON-16 — Walmart Marketplace / WFS / Walmart Connect & SEM spend (read) — **R2** (WP-23), extended, **read**
**Scope (v0.3):** Walmart US/CA/MX seller accounts (one `ws.store` per account): orders and lines, items, inventory, returns/refunds, WFS fulfilment and fees, settlement / reconciliation reports bridged to payouts, and **Walmart Connect / SEM ad spend read** for the Walmart Advertising line (F-J07, CALC-079 — spend only). Fee and charge types map to compat lines through the versioned `cost.channel_fee_map` (CALC-114, GV-154); unmapped types → Unclassified fees + `UNCLASSIFIED_FEE`.
**Docs (Documented, Extra):** Walmart Marketplace API — OAuth token lifetime **15 min**; API families Orders / Items / Inventory / Prices / Reports. Developer portal path, API versions, settlement / reconciliation report names, WFS fee fields and the Walmart Connect / SEM reporting API and its access model: **DISC-36** (not in research). Vendor behaviour: Sellerboard supports Walmart US/CA/MX (S09), MCF/WFS multi-channel auto-detect (S11) and Walmart SEM spend + Walmart Connect (S14).
**Auth:** OAuth client credentials per seller account; cache and refresh the token before 15 min (Extra); `credential_ref` per account. Walmart Connect access: separate (DISC-36).
**Grain:** order / line; item; inventory snapshot; settlement / reconciliation line; WFS fee line; ad spend account/campaign × day. **Currency:** USD / CAD / MXN per marketplace. **Timezone:** provider timestamps stored as received; store timezone from configuration. **Limits / quotas / webhooks:** DISC-36 — honour 429 with back-off per account.
**Backfill / replay:** reports by date range (history limit DISC-36); raw-first; replay from `raw_payload`.
**Latency:** orders ≤ 6 h, settlements daily (PROPOSED SLOs). **Revocation:** credentials invalid → `revoked` (RB-01).
**Protected data:** buyer name/address in orders — not stored; stripped at raw-write. **Cost:** $0 planning assumption.
**Fallback:** Seller Center CSV reports (orders, settlement / reconciliation, WFS fees, WFS inventory and inbound shipments, Walmart Connect spend) → uploads with fixed schemas.
**Single spend source (v0.3 rev 2, F-J09, GV-155):** each Walmart Connect / SEM ad account has `ads.ad_account.spend_source` = `connector` (spend from this connector's report; the `WalmartConnectSpend` settlement line is excluded as memo) or `settlement` (the settlement line is the Advertising amount; connector rows are memo). Never both; Hypothesis `test_invariant_ad_spend_single_source`.
**WFS inventory and inbound (v0.3 rev 2, F-G11):** WFS inventory snapshots (`inv.inventory_snapshot`, source `walmart_wfs_inventory`) and WFS inbound shipments (`inv.shipment`, kind `wfs_inbound`) are ingested in R2 (WP-23) for the inventory planner (WP-15, R3). Report / endpoint names: DISC-36.
**Report pages (v0.3 rev 2, F-J08):** Walmart orders, products, daily and monthly reports reuse the reports catalogue (SCR-110) with the channel filter.
**Read/write:** read only (no price, item or campaign writes).
**Acceptance:** synthetic cassettes per object; settlement bridge reconciles a synthetic settlement to 0.01; fee mapping conservation (GV-154); Walmart Connect spend appears only as the Walmart Advertising line; WFS orders of other channels deduped (CALC-047). Real-account parity run once a Walmart account exists (formula parity PROPOSED until then).
**Unknowns:** DISC-36.

## CON-17 — eBay — **R2** (WP-23), extended, **read**
**Scope (v0.3):** eBay seller accounts per site: orders / fulfilment, finances (transactions, fees, payouts), returns and refunds; order-level COGS / shipping file import (S18 pattern). Fee types map through `cost.channel_fee_map` (CALC-114).
**Docs:** not in research. Target API families per the Owner brief: eBay **Sell Fulfillment** (orders) and **Sell Finances** (transactions, payouts) — names, versions, OAuth scopes, quotas, history limits and fee-type codes are **UNVERIFIED → DISC-37**. Vendor behaviour: Sellerboard offers eBay reports and order-level COGS/shipping file import (S11, S18). Not connected in the audited accounts (OBS).
**Auth:** OAuth (user token per seller account; refresh handling per DISC-37); read scopes only. **Grain:** order / line; finance transaction; payout. **Currency:** per site. **Timezone:** provider timestamps as received. **Limits / webhooks:** DISC-37.
**Backfill / replay:** by date range; raw-first. **Revocation:** token invalid → `revoked`. **Protected data:** buyer PII not stored. **Cost:** $0 planning assumption.
**Fallback:** eBay order and transaction report CSV + order-level COGS/shipping import → uploads.
**Read/write:** read only. **Acceptance:** synthetic cassettes; payout bridge reconciles; fee mapping conservation; unmapped fee raises `UNCLASSIFIED_FEE` (R2: data-quality bar SCR-130; R3: WP-17 alert routing). eBay orders, products, daily and monthly report pages (F-J08, v0.3 rev 2) reuse the reports catalogue (SCR-110).
**Unknowns:** DISC-37.

## CON-18 — TikTok Shop — **R2** (WP-23), extended, **read**
**Scope (v0.3):** TikTok Shop (commerce) seller accounts: orders, returns/refunds, finance statements / settlements and fees. Distinct from TikTok Ads (CON-11, spend-only, CONDITIONAL, R2 — v0.3 rev 2), which supplies the TikTok Shop Advertising line because shop ad spend is billed through TikTok Ads. Fee types map through `cost.channel_fee_map` (CALC-114).
**Docs:** not in research (S02 lists TikTok Shop as a Sellerboard.io integration only). API names, versions, auth model (app keys, shop authorisation, token refresh), signing, regions, quotas, history limits and fee/settlement types are **UNVERIFIED → DISC-38**.
**Grain:** order / line; settlement / statement line. **Currency / timezone:** per shop region. **Limits / webhooks:** DISC-38.
**Backfill / replay:** by date range; raw-first. **Revocation:** authorisation revoked → `revoked`. **Protected data:** buyer PII not stored. **Cost:** $0 planning assumption.
**Fallback:** Seller Center order and finance/settlement exports → uploads with fixed schemas.
**Read/write:** read only. **Acceptance:** synthetic cassettes; settlement bridge reconciles; fee mapping conservation; unmapped fee raises `UNCLASSIFIED_FEE`.
**Unknowns:** DISC-38.

## CON-19 — CJ Dropshipping — **R5** (WP-39), extended, **read**
Docs not in research (S02). DISC-39. Grain: fulfilment cost per order. Fallback: CSV/XLSX import first (`order_ref, cost_component, amount, currency, date`). Actual replaces estimate per component (CALC-105). Read only. Unknowns: DISC-39.

## CON-20 — ShipStation (actual shipping cost) — **R5** (WP-39), extended, **read**
**Docs:** Sellerboard lists ShipStation as an actual-shipping-cost source (S02, S49 FAQ); provider API docs not in research → DISC-39. Grain: shipment × label cost; currency per carrier account; fallback: shipments CSV `{order_ref, carrier, service, cost, currency, shipped_at}`. Actual shipping cost replaces profile estimate (CALC-020 actual-over-estimate rule, same pattern as CALC-022). Read. Protected data: recipient address — strip. Unknowns: DISC-39.

## CON-21 — Flexport / SFN — **R5** (WP-39), extended, **read**
Docs not in research (S02). DISC-39. Grain: fulfilment fee per order / inbound. Fallback: CSV/XLSX import first. Read only. Unknowns: DISC-39.

## CON-22 — Veeqo — **R5** (WP-39), extended, **read**
Docs not in research (S02/OBS: chip present on Sellerboard settings). DISC-39. Grain: shipment cost / inventory. Fallback: Veeqo export CSV → uploads (schema fixed on first sample). Recipient data stripped. Read only. Unknowns: DISC-39.

## CON-23 — Private Google Sheets / CSV-XLSX URL feeds (COGS, landed cost, expenses) — R1, core, **read**

**Docs:** Sellerboard pattern (S12): Settings → Automation → COGS import from Google Sheets or CSV/XLSX URL; columns ASIN, SKU, batch qty, period start, cost; methods Weighted / By period / FIFO; daily sync. Google Sheets API official docs: not in research (portal assumption; use service-account share-to-read).
**Version:** Google Sheets API v4 (planning assumption). **Auth:** service account e-mail shared on the sheet (read-only); CSV/XLSX URL must be HTTPS with allow-listed hosts.
**Schema (fixed, validated):** `asin, sku, batch_qty, period_start (YYYY-MM-DD), unit_cost, currency, [freight, duty, insurance, inbound]` — extra columns rejected; amounts parsed as Decimal; currency required (multi-currency sourcing GBP/EUR/USD/INR).
**Grain:** batch row. **Timezone:** dates only. **Limits:** file ≤10 MB, ≤50k rows. **Webhooks:** none; daily sync + `sync-now`. **Backfill:** re-read whole file; diff by row hash. **Latency:** 24 h. **Revocation:** share removed → 403 → alert. **Protected data:** none expected; content is **untrusted** (formula injection, prompt injection) — parsed only, never executed/rendered raw. **Cost:** $0. **Fallback:** manual upload (same schema). **Read/write:** read. **Acceptance:** golden vectors GV-006..013 reproduced from a sample feed; rejected-row report; idempotent re-sync (no duplicate batches). **Unknowns:** none blocking.

## CON-24 — Amazon Solicitations API (review requests) — OMITTED v0.3 (marketing)
**OMITTED v0.3 (marketing)** — removed from the build by the Owner on 2026-10-10 (research/v02/V03_BRIEF.md); not to be built, no credentials requested; kept as a heading for ID traceability only.

## CON-25 — Amazon Listings Items (price patch) — repricer writes — R4, conditional, **write**

**Docs (Documented):** `patchListingsItem` with JSON Patch on `/attributes/purchasable_offer`; ops merge/replace/delete; selectors `currency`, `marketplace_id`, `audience`; role Product Listing (S32). Vendor repricer feature reference (S10): guardrails Amazon Competitive Price Threshold, max +25 % above 90-day median, ±50 % from initial price — adopted as default bounds in `auto.price_rule`.
**Version:** Listings Items API version not captured in research → **DISCOVERY-17** (commonly documented as v2021-08-01; verify). Buy Box / competitor price observation source is **unknown (DISC-17: Pricing API or Notifications)**; until resolved, observations come from manual entry or CSV upload (`price_observation.source='manual'|'csv'`).
**Auth:** SP-API Product Listing role (S29). **Grain:** SKU × marketplace price. **Currency:** `purchasable_offer.currency` selector must equal marketplace currency. **Limits:** DISC-17. **Webhooks:** listing change notifications DISC-26. **Idempotency:** client token support DISC-16; otherwise read-back before retry.
**Write safety (WP-20 framework, the only external write path in scope):** simulation-first (`simulation_only=true` default in `price_rule`), floor from CALC-041 never bypassed (GV-040/041), maker-checker, canary (1 SKU), bounded exposure (max Δ per execution), stale-data stop 6 h, kill switch, read-back verification via Listings read. Seller Central min/max bounds respected (S10). **Rollback = compensating patch; the market may already have transacted at the new price.**
Env flag `WRITES_PRICING`. **Cost:** $0 (S35). **Fallback:** Seller Central manual price edit or price feed upload (manual); observations via CSV. **Read vs write:** write (read of listing via CON-01).
**Acceptance:** contract test with recorded `patchListingsItem` response including `submissionId`/issues; stage dry-run on a test SKU; approval flow demo; kill-switch drill.
**Unknowns:** DISC-16, DISC-17, DISC-26.

## CON-26 — Amazon Ads write (bids / budgets / negatives) — OMITTED v0.3 (marketing)
**OMITTED v0.3 (marketing)** — removed from the build by the Owner on 2026-10-10 (research/v02/V03_BRIEF.md); not to be built, no credentials requested; kept as a heading for ID traceability only.

## CON-27 — QuickBooks / Tally export (accounting) — R5, extended, **write (file export first)**

**Docs:** OBS: Sellerboard "QuickBooks: Settlements (beta), Configuration of QB accounts" (not connected). No API docs in research → **DISCOVERY-23** (QBO API version, Tally XML import format).
**Mode:** R5 ships file export (CSV / QBO-compatible journal / Tally XML) of settlement-level journal entries from the settlement bridge (CALC-027) and period P&L; API push later (conditional).
**Grain:** journal line per settlement × account. **Currency:** entity functional currency with INR reporting; FX rate ids included. **Write safety:** export is a file; no external mutation until API phase, which then follows the proposal pipeline under env flag `WRITES_ACCOUNTING_API`. **Acceptance:** accountant reconciles one closed month from export. **Unknowns:** DISC-23.

## CON-28 — Anthropic API (optional explain layer) — R5, optional, **read**

**Docs (Documented):** pricing S37 (Fable 5.1: $10/M input, $50/M output; cache read $0.25/M; Sonnet 5 $2/$10; Haiku 4.5 $1/$5; Batch 50 % off — Extra). Data-handling / retention terms: **DISCOVERY-24**.
**Auth:** API key in Secrets Manager. **Grain:** request. **Inputs allowed:** approved aggregate views only (spec §10.10) — never raw payloads, PII, credentials, execution payloads. **Untrusted content:** aggregates are typed values, not free text; provider/file content never enters prompts.
**Limits:** provider rate limits (DISC-24); internal per-user daily cap. **Cost:** metered per request in INR (`explain_response.cost_inr`); budget alert. **Fallback:** feature off. **Read/write:** read-only; no tools with side effects.
**Acceptance:** explain answers cite the aggregate hashes used; red-team test that injected text in product titles cannot reach the prompt.
**Unknowns:** DISC-24.

## CON-29 — Subscription provider (Shopify subscription app of record) — R2, conditional, **read**

**Docs (Documented):** S20 — subscription contracts exposed only via `read_own_subscription_contracts` (the app's own records); **no read-all scope**. True contracts therefore come only from the subscription app of record (its API or export).
**Version / API:** depends on the app of record → **DISCOVERY-13**. **Grain:** contract × billing cycle. **Currency:** shop currency. **Protected data:** contract has customer linkage — hashed identity only. **Fallback (default):** app-of-record CSV export `{contract_id, customer_hash_input, product, interval, status, created_at, next_billing}`; if unavailable, the repeat-order heuristic is shown and labelled `REPEAT_ORDERS` (GV-037) — never "Active subscriptions" (the OBS SnS tile is Amazon Subscribe & Save, sourced from SP-API reports where available — DISC-03). Sources for the repeat-vs-subscription rule: S20, S49 FAQ.
**Read/write:** read. **Acceptance:** subscription count matches app-of-record dashboard for one month or feature labelled heuristic. **Unknowns:** DISC-13.

---

## CON-32 — Courier / 3PL fulfilment cost source (e.g., 3PL fulfilment partner, courier invoices) — R1, conditional, **read** (v0.2)

**Purpose.** Replace shipping-profile *estimates* with *actual* forward, return, COD and RTO charges per order (CALC-105, CALC-104; F-D16, F-K30; WP-35).
- **Why (OBS-R finding #1):** the audited Shopify shipping profile equals the amount the customer is charged, and pick & pack is 0. Courier, 3PL and RTO costs are therefore absent, and Shopify profit is overstated.
- **Release and class:** R1, conditional. The class is conditional because the providers and file layouts must be confirmed with logistics.

**Docs.** No provider API documentation is in the research. **CSV/XLSX first**, and any provider API is **DISC-33**. Provider names in fixtures and code are synthetic codes (e.g., `3pl_a`, `courier_b`).

**Version.** n/a for files. `ing.connector.config.layout_version` per provider layout (PROPOSED: one versioned column mapping per provider).

**Auth.** Files are uploaded by a user with `logistics.write` through `POST /courier/imports`. API credentials (if DISC-33 yields an API) live in Secrets Manager under the vault reference model (spec §9.3).

**Source fields** (fixed allow-list after per-provider mapping; extra columns ignored, consignee columns dropped at parse):

| Field | Required | Type | Notes |
|---|---|---|---|
| `awb` | one of awb / order_ref | text | normalised upper case, spaces/hyphens removed |
| `order_ref` | one of awb / order_ref | text | Shopify order name, Amazon order id, B2B doc_no, or provider client-order id |
| `invoice_no` | yes | text | provider invoice / bill number |
| `invoice_date` | yes | date | provider invoice date (`YYYY-MM-DD` or mapped format) |
| `forward_charge` | default 0 | Decimal | freight forward |
| `return_charge` | default 0 | Decimal | customer return / reverse pickup |
| `cod_charge` | default 0 | Decimal | COD handling fee |
| `rto_charge` | default 0 | Decimal | return-to-origin freight |
| `other_charge` (+ label) | default 0 | Decimal | fuel surcharge, packaging, storage, pick & pack (3PL) |
| `gst_on_charges` | default 0 | Decimal | input GST (recoverable per entity setting, F2) |
| `currency` | yes (default entity currency) | ISO 4217 | |
| `charged_weight_g`, `declared_weight_g` | optional | int | weight dispute check |
| `zone` | optional | text | provider zone / slab |
| `payment_type` | optional | prepaid / cod | |
| `shipment_status` | optional | delivered / rto / in_transit / lost | feeds `ledger.logistics_event` |
| `pickup_date`, `closed_date` | optional | date | |
| invoice header total, GST total | optional (separate sheet or footer) | Decimal | footing check |

**Grain, currency, timezone.** The grain is an invoice line (one AWB can appear on several invoices: forward, then RTO, then a weight re-bill). Currency is the invoice currency (INR for India). Dates have no time component and are applied in the store timezone.

**Matching** (spec §3.8, job `courier.match`, after each import and nightly):
1. AWB exact against `ledger.fulfilment_tracking` (from CON-05 fulfillments, or tracking columns in 3PL files) within the legal entity.
2. Otherwise `order_ref` exact against the Shopify order name (store-configured prefix and `#` stripped), the Amazon order id, or the B2B `doc_no` (B2B dispatch → `freight_borne` actual).
3. AWB and reference resolving to **different** orders → `ambiguous`; never applied; `COURIER_MATCH_CONFLICT`.
4. Unmatched rows are retried nightly for 60 days (PROPOSED). Their cost is then booked as unallocated logistics cost on the invoice-date store-day: **never dropped**.
5. Manual match / dispute through `PATCH /courier/charges/{id}` (If-Match, audit-logged).

**Application.** Per component, **actual replaces estimate** (GV-117), with `source` ACTUAL / ESTIMATE / PARTIAL. RTO orders (status `rto` or an RTO charge present) are excluded from sales, and the forward + return + COD + damage cost is retained (GV-118). Non-recoverable GST on charges is costed.

**Tolerances** (PROPOSED, configurable in `ws.workspace.settings.logistics`):

| Check | Default | On breach |
|---|---|---|
| Invoice footing (Σ lines vs header total) | ≤ 1.00 | invoice `unbalanced`, rows held, `COURIER_INVOICE_UNBALANCED` |
| Weight dispute | charged > 1.10 × max(declared, product-master weight × qty + packaging) | `disputed` candidate |
| Estimate drift per shipping profile (30-day mean) | > 25 % | `SHIPPING_PROFILE_DRIFT` |
| Rate-card overcharge (optional rate card) | > max(5.00, 5 %) | overcharge candidate |
| Estimated share of Shopify orders older than 15 days | warn > 20 %, fail > 50 % | data-quality bar `SHIPPING_ESTIMATED_PCT` |

**Pagination / history / quotas.** Files: ≤ 10 MB, ≤ 50k rows per file. History is whatever the provider supplies; the backfill target is 90 days (R0 parity). API quotas: DISC-33.

**Webhooks.** None assumed; DISC-33.

**Backfill / replay.** Re-upload historical invoices, deduplicated by `(provider_code, invoice_no, line_hash)`. A corrected re-issue of the same `invoice_no` supersedes its lines (revision `restatement`). Replay re-parses the stored raw file with the current mapping version.

**Latency / freshness.** Bound by the provider invoice cadence. SLO: 7 days after invoice date; alert at 21 days (spec §9.5).

**Revocation.** Files: n/a. API (if any): credential failure → `revoked`.

**Protected data / retention.** Courier files often carry consignee name, address and phone (personal data under DPDP / GDPR for EU orders). These columns are **dropped at parse**: only AWB, references, amounts, weights, zone and status are stored. The raw file is kept 2 years with those columns redacted before storage (spec §5.5).

**Cost.** $0 (file upload). An API, if any, is a planning assumption.

**Manual fallback.** This connector *is* the manual path. An API is optional later (DISC-33).

**Read vs write.** Read only. Courier claims/disputes are recorded internally; nothing is sent to the provider.

**Untrusted content.** Formula-injection neutralised; Decimal parsing; fixed column mapping; no free-text field rendered unescaped.

**Acceptance evidence:**
- (a) one sample file per provider mapped (synthetic values in fixtures);
- (b) footing test on a full invoice;
- (c) match rate report ≥ 95 % of value matched on a one-month pilot (PROPOSED);
- (d) GV-117 and GV-118 reproduced from fixture files;
- (e) idempotent re-upload (no duplicate cost);
- (f) consignee-column stripping proven by a CI scan of stored rows.

**Unknowns.** DISC-33 (providers in use per market, invoice layouts, API availability), DISC-29 (tracking-field names in Shopify fulfillments).

## CON-33 — Internal B2B lead pipeline app (won deals → draft B2B invoices) — R5, conditional, **read** (v0.2)

**Purpose.** Pull **won** deals from the owner's internal B2B lead-pipeline application, so that a B2B invoice need not be re-keyed (F-M11, F-K31; WP-31, release R5). The connector is strictly read-only on the source, and on our side it creates only **drafts**. It **never auto-approves, auto-posts or cancels** (spec §2 import rule 7, §7.4, §10.13).

**Docs / version.** Internal application; no external documentation. Export format or API: **DISC-34** (owner-confirmed). PROPOSED order of preference: (1) a scheduled JSON/CSV export to object storage or e-mail drop; (2) a read-only REST endpoint with a scoped token.

**Auth.** If an API: a read-only service token stored in Secrets Manager (vault reference), never in env vars or the DB. If a file: uploaded by a user with `b2b.import`.

**Source fields** (minimum contract, PROPOSED):
- `deal_id`
- `deal_updated_at`
- `stage` (only `won` is consumed)
- `won_at`
- `customer`: GSTIN if known, legal name, state, customer type
- `salesperson_code`
- `territory_code`
- `lines[]`: product identifier (internal SKU / EAN), qty, agreed unit price ex-GST, discount fraction
- `currency`
- `expected_dispatch_date`
- `customer_po_ref`
- `notes`

Contact persons are **not** pulled; if present, they are dropped at parse (DPDP minimisation).

**Grain / currency / timezone.** Deal; deal currency (INR expected); timestamps ISO-8601 with offset.

**Mapping to B2B:**
- **Customer:** matched by GSTIN, else by `customer_code` mapping. If there is no match, the deal is held in `ing.lead_pipeline_deal` with status `customer_unmatched`, and no customer is created automatically.
- **Products:** matched by product master (CALC-087). Unmatched lines block draft creation.
- **Prices:** checked against the customer's price list. Deviations beyond `max_disc_pct` are flagged on the draft.
- **Invoice draft:** created with `source='lead_pipeline'`, `source_ref=deal_id`, `external_ref_type='lead_pipeline_deal'`, `external_ref=deal_id`, and `maker_id NULL` until a user adopts it.
- **Dedup:** CALC-100 runs as for any invoice, and also checks `customer_po_ref` against Shopify draft-order references.

**Idempotency.** Key `lead:{connector}:{deal_id}:{deal_updated_at}`.
- A deal already converted to a draft **updates that draft only while it is still `draft` and unadopted**.
- Once a user has adopted or approved the draft, later deal changes raise `LEAD_DEAL_CHANGED_AFTER_ADOPTION` for the user to resolve manually.
- Deals moving out of `won` raise an alert; the connector never cancels anything.

**Quotas / webhooks.** Pull daily (PROPOSED). No webhooks in R5.

**Backfill.** Won deals since a configured date (default: start of the current FY).

**Latency.** 24 h SLO; alert at 72 h (spec §9.5).

**Revocation.** Token invalid → `revoked` and alert.

**Protected data.** Business identifiers only (GSTIN, access-controlled); no personal contacts.

**Cost.** $0 (internal).

**Manual fallback.** CSV export of won deals uploaded through `POST /b2b/import?kind=invoices&mode=validate_only|commit` with `source='lead_pipeline'`.

**Read vs write.** Read only. There is **no write-back** to the pipeline app in scope (marking a deal "invoiced" would be a new write contract).

**Acceptance evidence:**
- (a) fixture export with synthetic deals → drafts with correct customer/product mapping;
- (b) proof that no code path can approve or post: import-linter contract plus an API test as the connector service identity → 403;
- (c) idempotent re-pull;
- (d) changed-after-adoption alert;
- (e) dedup against a Shopify draft-order reference (GV-113 pattern).

**Unknowns.** DISC-34 (export/API availability, field names, stage values, hosting).

---

## CON-30 — Amazon Listings Items (listing content publication) — CONDITIONAL stub, **no release**, **write**

Status: **not scoped**. Exists so that `listing_update` can be added to `auto.automation_proposal.action_type` only after this contract is completed. No endpoint, version or quota is asserted.
**Docs:** Listings Items API (S32 shows the purchasable-offer patch path only; content attributes not researched). **Version:** DISCOVERY-17. **Auth:** SP-API Product Listing role (S29). **Grain:** SKU × marketplace × attribute. **Currency/timezone:** n/a. **Limits/idempotency:** DISC-16/17. **Webhooks:** listing-change notifications DISC-26.
**Write-safety template (mandatory before any release):** env flag `WRITES_LISTINGS` (to be added only through change control, default false) · proposal pipeline (draft → simulated → proposed → approved by checker ≠ maker → canary of 1 SKU with read-back → executing) · bounded exposure (max SKUs per execution, attribute allow-list; price attributes excluded — those belong to CON-25) · stale-data stop (listing read ≤ 6 h old) · idempotency key per `(proposal, attempt, phase)` · DB kill switch `action:listing_update` · compensating patch as the only rollback (a published listing may already have been crawled/indexed) · full request/response in `automation_execution` · audit log.
**Manual fallback:** Seller Central listing edit / flat-file upload (manual, recorded). **Acceptance (for future scoping):** contract cassette for one attribute patch incl. `issues[]`; canary drill; kill-switch drill. **Unknowns:** DISC-16, DISC-17, DISC-26, plus a business decision that listing publication belongs in this application at all.

## CON-31 — Fulfilment commands (MCF/FBA fulfilment orders, removal orders, inbound shipment creation) — CONDITIONAL stub, **no release**, **write**

Status: **not scoped**. Exists so that `fulfillment_action` can be added to `action_type` only after this contract is completed. No endpoint, version or quota is asserted.
**Docs:** SP-API Fulfillment Outbound / Inbound families are listed in the welcome page (S27) only; not researched further. **Version:** DISCOVERY-25 (Inbound) / DISCOVERY-28 (Outbound — new item). **Auth:** SP-API Amazon Fulfillment role (S29); MCF order creation needs buyer shipping address → **restricted PII role (Direct-to-Consumer Shipping, S29) which this application does not hold** — a blocking constraint for MCF creation; removal orders and inbound plans may not need it (DISC-28).
**Write-safety template (mandatory before any release):** env flag `WRITES_FULFILMENT` (default false) · proposal pipeline with checker ≠ maker · canary of 1 order/shipment with read-back · bounded exposure (max units/value per execution) · stale-data stop (inventory snapshot ≤ 1 h) · idempotency (client token if supported, DISC-16, else read-back before retry) · DB kill switch `action:fulfillment_action` · **physical actions cannot be rolled back** (a removal or shipment in motion is irreversible; only cancellation where the provider allows) · execution log · audit.
**Manual fallback:** Seller Central / Shopify admin actions (manual, recorded). **Acceptance (for future scoping):** PII-role decision documented; one cassette per command; cancellation path tested. **Unknowns:** DISC-16, DISC-25, DISC-28.

---

## Discovery register (DISC-xx)

| ID | Item | Blocks | Owner | Resolution path |
|---|---|---|---|---|
| DISC-01 | SP-API private developer registration outcome; roles granted; exact reference-doc URLs; annual security review obligations | CON-01 | Integration eng | File registration in WP-01 week 1; Amazon case (5-day window, S28) |
| DISC-02 | Orders / FBA Inventory / Reports / Sales API versions and per-endpoint rate limits (not captured in research) | CON-01 | Integration eng | Read reference pages once registered; record in manifest |
| DISC-03 | Finances v2024-06-19 vs v0 coverage for Amazon.in (GST, TCS, Item TDS, affordability, technology fee components observed in OBS fee list); Subscribe & Save data source | CON-01, CALC-025 | Financial/data eng | Pull 30 days of both for IN store; diff |
| DISC-04 | Settlement report cadence per marketplace; V2 flat file availability on IN/UK/US/FR/DE | CON-01, CALC-027 | Finance | Inspect scheduled reports in Seller Central |
| DISC-05 | SP-API sandbox availability/fidelity for stage | CON-01 | DevOps | Docs after registration |
| DISC-06 | Sales & Traffic report type IDs and granularity per marketplace; a region- or FC-level report usable for the Map view without restricted PII (CALC-111). (Brand Analytics / Brand Registry part closed — CON-03 omitted v0.3) | CON-01 | Integration eng | Reports reference |
| DISC-07 | Amazon Ads API official spec (reporting v3), versions, quotas, timezone, lookback windows for **spend** reports — official page did not render (S33/S34) | CON-02 (R1 spend via WP-37) | Integration eng | Apply for Ads reporting (read) access during R0; read docs once accessible; spend CSV fallback until approved |
| DISC-08 | Closed — omitted v0.3 (CON-26 Amazon Ads write is marketing scope) | — | — | — |
| DISC-09 | Closed — omitted v0.3 (CON-04 Amazon Attribution is marketing scope) | — | — | — |
| DISC-10 | Shopify plan per store (rate-limit tier); **current custom-app creation path** (e.g. developer dashboard vs legacy admin-created apps) and **how `read_all_orders` is approved for it**; approval outcome; L1 (and province-level address) availability for our app type | CON-05, CALC-111 | Integration eng | Confirm on the India store in WP-01; file the requests then |
| DISC-11 | Shopify Payments availability per store (esp. IN); payout object reference path; disputes fields | CON-06 | Finance | Check each shop's payments settings |
| DISC-12 | Razorpay / PayPal / Stripe API access, versions, fee fields | CON-07 | Integration eng | Gateway dashboards; default CSV |
| DISC-13 | Subscription app of record per store; its API/export format | CON-29 | Business owner | Inventory installed apps |
| DISC-14 | Amazon reimbursement policy windows (vendor UI shows L&D 60 d, returns 105 d, fee changes 18 m — OBS); official policy per marketplace | mb.reimbursement_candidate deadlines | Finance/ops | Seller Central policy pages |
| DISC-15 | Closed — omitted v0.3 (CON-24 Solicitations / review requests is marketing scope) | — | — | — |
| DISC-16 | Idempotency / client-token support on the Listings price patch | CON-25 | Backend | Reference docs; else read-back-before-retry |
| DISC-17 | Listings Items API version and limits; source for Buy Box / competitor price observations (Pricing API / notifications) | CON-25 | Integration eng | Reference docs |
| DISC-18 | Google Ads, Meta and (v0.3 rev 2) TikTok Ads: portals, API versions, read-only reporting scopes, developer-token / system-user / advertiser authorisation setup, quotas, restatement windows — for spend only (Microsoft, Snapchat, Pinterest, Taboola closed — omitted v0.3) | CON-08, CON-09 (R1 via WP-37); CON-11 (R2 via WP-23, CONDITIONAL) | Integration eng | Confirm before WP-37 (R1); TikTok Ads before WP-23 (R2), CSV ESTIMATE until then |
| DISC-19 | Superseded v0.3 — channel roadmap confirmed by the Owner 2026-10-10 (Walmart, eBay, TikTok Shop within 12 months → R2); details split into DISC-36..DISC-39 | — | — | — |
| DISC-20 | DPIA for EU personal data (Shopify UK/FR/DE L1 payloads) held in AWS ap-south-1 / ap-south-2 (DC-01 decided 2026-10-10) | Deployment §9.1, R2 UK/EU stores | Delivery lead + legal | Before UK/EU stores connect (R2) |
| DISC-21 | Amazon Data Protection Policy incident-notification SLA and audit obligations | §11 | Security | DPP text on registration |
| DISC-22 | Closed — omitted v0.3 (CON-15 Klaviyo is marketing scope) | — | — | — |
| DISC-23 | QuickBooks Online API version; Tally import XML format used by the accountant | CON-27 | Finance | Accountant interview |
| DISC-24 | Anthropic API data-retention / zero-data-retention terms, rate limits | CON-28 | Delivery lead | Anthropic terms review |
| DISC-25 | Fulfillment Inbound API version (v2024-03-20 vs v0) and shipment fields | CON-01 | Integration eng | Reference docs |
| DISC-26 | Notifications API (report processing finished, listing/price change) availability and delivery (SQS/EventBridge) | CON-01, CON-25 | Integration eng | Reference docs |
| DISC-27 | FX rate source (RBI reference rate / ECB / provider-implied) and policy sign-off | ws.currency_rate, CALC-026 | Finance | Decide in WP-07 |
| DISC-28 | Fulfillment Outbound (MCF) API version; whether removal/inbound commands require the restricted Direct-to-Consumer Shipping role | CON-31 (stub) | Integration eng | Only if CON-31 is ever scoped |
| DISC-29 (v0.2) | Shopify fields for order sales channel / originating app, draft-order linkage and name, PO / note reference, fulfillment tracking number and carrier | CON-05, CON-32, CALC-100 | Integration eng | Read the Order / DraftOrder / Fulfillment references for API 2026-07; verify on the India store in WP-12 |
| DISC-30 (v0.2) | Closed — omitted v0.3 (day parting is marketing scope) | — | — | — |
| DISC-31 (v0.2) | Intercompany unrealised-profit-in-stock elimination policy and FX translation policy for consolidation | WP-36, CALC-101 | Finance + CA | Decide before R2 consolidation sign-off |
| DISC-32 (v0.2) | DPDP notice / consent wording for B2B contacts and salespeople; retention period sign-off | spec §11 | Business owner + legal | Before R1 go-live |
| DISC-33 (v0.2) | Courier / 3PL providers in use per market, invoice file layouts, API availability, COD remittance reports | CON-32 | Logistics + Integration eng | Collect one month of sample invoices in WP-01/WP-35 |
| DISC-34 (v0.2) | Internal lead-pipeline export or API: format, fields, stage values, hosting, auth | CON-33 | Business owner + Integration eng | Before R5 scoping |
| DISC-35 (v0.3) | Marketplace master facts per Amazon marketplace: marketplace ids, region → SP-API endpoint mapping (US→NA, UK/FR/DE/IN→EU is a planning assumption), currency, default timezone, tax regime history per marketplace (`VAT_SELLER` | `GST_SELLER` | `CONSUMPTION_TAX` | `SALES_TAX_MF` | `MF_VAT`, valid_from / valid_to), fee-code coverage incl. Pan-EU / EFN and Remote Fulfillment fee codes, FBA stock-pool membership and stock-transfer VAT treatment (v0.3 rev 2, F-A12; ⚠ CA); per-region rate limits | CON-01, WP-38, CALC-113 | Integration eng + Finance/CA | SP-API reference pages after registration (DISC-01/02); CA confirms tax regimes; seed rows stay UNVERIFIED until then |
| DISC-36 (v0.3) | Walmart: developer portal path, API versions, quotas, history limits, settlement / reconciliation report names and fields, WFS fee types, Walmart Connect / SEM reporting API and access model, US vs CA vs MX differences | CON-16, WP-23, CALC-114 | Integration eng + Business owner | Open the Walmart seller / developer accounts (business action) and read the official docs; CSV fallback until then |
| DISC-37 (v0.3) | eBay: Sell Fulfillment / Sell Finances API names, versions, OAuth scopes, quotas, history limits, fee-type codes, payout fields per site | CON-17, WP-23, CALC-114 | Integration eng | Official developer docs once an eBay seller account exists; CSV fallback until then |
| DISC-38 (v0.3) | TikTok Shop: Partner/Open API names, versions, app authorisation and token refresh, request signing, regions, quotas, finance statement / settlement and fee types | CON-18, WP-23, CALC-114 | Integration eng | Official partner docs once a TikTok Shop seller account exists; CSV fallback until then |
| DISC-39 (v0.3) | Operations connectors (ShipStation, Flexport/SFN, Veeqo, CJ Dropshipping): which are used, access, API versions, file layouts | CON-19..CON-22, WP-39 | Logistics + Integration eng | Before R5 scoping; CSV/XLSX import first |
