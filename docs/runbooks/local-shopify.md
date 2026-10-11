# Connect multiple Shopify stores locally

This CON-05 slice supports independent connections for five or more stores. Each
connection has its own domain, country permission scope, credentials, currency,
timezone, sync jobs and append-only raw records. Stores may share a workspace or
use separate workspaces. Profit reporting and full WP-12 acceptance are pending.

## 1. Start the app

Keep PostgreSQL/Redis running. From the project root:

```powershell
uv run alembic -c api/alembic.ini upgrade head
uv run python scripts/initialize_shopify_workspace.py
uv run uvicorn app.main:app --app-dir api/src --host 127.0.0.1 --port 8000 --reload
```

The workspace helper only accepts localhost rci_local and a synthetic @example.test
user. It creates a separate non-demo workspace with connectors.manage and profit.read
permissions for the initialized local account. It preserves the existing read-only
demo workspace. It prints the integration workspace ID. It is idempotent for this
user/workspace and does not create Shopify apps or contact providers.

In another terminal:

```powershell
cd web
npm run dev
```

Open http://127.0.0.1:5173, sign in, select Local Shopify integrations (or the workspace ID
printed above), then open **Channels**. If signed in before the helper ran, refresh
the page to refresh your membership list. Current local password-only login is
an explicitly enabled local exception; no authenticator is needed while enabled.

## 2. Prepare the app for each store

Create and install a dedicated read-only app using Shopify's
[Dev Dashboard guide](https://shopify.dev/docs/apps/build/dev-dashboard/create-apps-using-dev-dashboard).
New apps are not created through the legacy admin custom-app flow.

Minimum permissions for this slice:

- read_orders
- read_products
- read_inventory
- read_locations

Do not give it write permissions. Verification rejects an installed app that has
any write_ scope. Customer identity fields are not queried. Order/customer-data
access approvals still need to be completed through the applicable Shopify setup;
this integration does not bypass approval. See
[access scopes](https://shopify.dev/docs/api/usage/access-scopes).

Choose authentication separately for each connection:

| Situation | Connection option | Local credentials |
|---|---|---|
| App and store belong to the same Shopify organization | Client credentials | App client ID and secret |
| Existing authorized installation supplies an offline Admin API token | Offline token | Installed app's token |

[Client credentials](https://shopify.dev/docs/apps/build/authentication-authorization/client-credentials-grant)
are only for your own organization's stores. The helper asks you to confirm this.
It obtains expiring access tokens per store when needed and keeps them in memory.
For a different merchant, obtain an offline token using Shopify's approved
[authorization code flow](https://shopify.dev/docs/apps/build/authentication-authorization)
before choosing the offline-token option. An OAuth installation/redirect UI and
refreshable offline-token adapter are **not implemented** in this slice. This
option also supports an existing legacy app's valid offline token. Re-enter the
token when it expires or is revoked. Collaborator access alone is not sufficient
for client credentials. Do not use a Storefront API token.

## 3. Add and verify all five stores

For each store:

1. Click **Add store** in Channels.
2. Enter its name.myshopify.com domain without a scheme/path. Enter the store's
   two-letter country code and choose its authentication method.
3. Click **Save store**. This stores metadata only, with status pending auth.
4. Copy that store card's setup command into a terminal at the project root:

   ```powershell
   uv run python scripts/setup_shopify_credentials.py CONNECTION_UUID
   ```

5. Enter credentials at the hidden terminal prompts. Never paste them into chat,
   code, application screenshots or logs.
6. Click **Verify connection**. It verifies store identity, configured country,
   granted read scopes, currency, timezone and API version.
7. Click **Sync now**. The card polls the job state and shows raw record counts.

Repeat for all five. A duplicate domain within the same workspace is rejected.
Each connection uses its own credential reference; there is no global Shopify
token or assumed currency/timezone. IDs, jobs and records are scoped by workspace
and connector. A user needs connectors.manage with wildcard product access and
the matching country or wildcard market scope. Demo workspaces reject mutations.

The local devfile adapter saves encrypted credential envelopes under
.tmp/connector-secrets, keyed by connection UUID and bound to that workspace/domain.
The key and encrypted files are git-ignored. Keep this directory private; chmod
permissions on Windows do not replace proper account/ACL protection. This local
adapter is not a production secret manager. AWS/Vault adapters remain fail-closed.

## 4. What sync currently imports

- Products and variants, including their inventory-item references.
- Inventory items and paginated quantities per location.
- Orders created in the last 60 days and their paginated line items.
- Selected order totals and refunded totals, preserving currency and exact decimal
  strings; these are source facts, not a reconciled profit calculation.

Provider queries and the raw-write allow-list exclude buyer names, email, phone,
shipping addresses, notes and customer records. Raw records have hashes and source
versions; inventory observations use the sync ID so quantity reversions are retained.
Order-line versions use the parent order update timestamp. Partition-independent
receipt claims avoid duplicate raw insertion within the same observation/version.

No imported financial figures are displayed on the profit dashboard yet. Ledger
normalization, COGS, tax/fee/refund reconciliation and calculation APIs are needed
before those figures are meaningful. The current currency stays attached to each
source amount; no client or backend FX aggregation is performed.

## Operational limits

Manual jobs run in the API process with persistent job records, a 10-minute deadline
and a pagination guard; this is a local slice, not the planned arq worker. Large
stores can exceed the deadline, leaving an explicitly failed partial import with
previous committed pages retained. Interrupted queued/running jobs become eligible
for manual retry after 15 minutes. There is no automatic resume/scheduler.

Pause stops subsequent page commits. **Disconnect locally** disables sync and
removes the local encrypted credential file. To revoke access at Shopify, uninstall
the dedicated app yourself. Re-enable requires credential setup and verification.
Failures expose stable codes, never provider bodies or secrets. A 401/403 response
marks access revoked. Throttling retries use bounded exponential backoff and the
GraphQL cost budget; redirects are never followed with credentials.

Bulk backfill, older orders, webhooks/HMAC/uninstall reception, Shopify Payments,
full refund/tax/shipping records, reconciliation, normalized product tables and
profit reports are pending. DISC-10 installation/approval facts and DISC-29 sales
channel/B2B dedup facts remain open; do not infer source attribution from this slice.

## Checks recorded

Migration upgrade applied locally; Alembic head is 0003_shopify_connections.
Frontend strict TypeScript/Vite build passed. Seven GraphQL queries were validated
against Shopify Admin 2026-07; Shop.billingAddress carries a deprecation warning
in that schema. No live store, credential or provider data was accessed by the agent.
Automated security/sync tests, migration round trip and browser/axe checks have
not been run for this slice and are required before acceptance.
