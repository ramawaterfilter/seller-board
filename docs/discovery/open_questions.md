# Discovery questions — human review required
Prepared 2026-10-12. WP-01 remains IN PROGRESS. The rows below are copied from
integration/connector_contracts.md; owner roles are proposed responsibilities, not
confirmed assignments. Closed/omitted rows retain their source status. Open rows
have not been resolved by this implementation session.

| ID | Question | Scope | Owner role | Next evidence |
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
