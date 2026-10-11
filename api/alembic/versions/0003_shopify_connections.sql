CREATE SCHEMA IF NOT EXISTS ing;
CREATE TABLE IF NOT EXISTS ing.connector (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id UUID NOT NULL REFERENCES ws.workspace(id),
  -- Nullable until the WP-04 store/legal entity directory is implemented.
  store_id UUID,
  connector_code TEXT NOT NULL CHECK (connector_code = 'CON-05'),
  mode TEXT NOT NULL DEFAULT 'read' CHECK (mode = 'read'),
  status TEXT NOT NULL DEFAULT 'pending_auth'
    CHECK (status IN ('disconnected','pending_auth','connected','revoked','paused','killed')),
  kill_switch BOOLEAN NOT NULL DEFAULT false,
  api_version TEXT NOT NULL,
  config JSONB NOT NULL,
  credential_ref TEXT NOT NULL UNIQUE,
  last_success_at timestamptz, last_error_at timestamptz, last_error TEXT,
  revoked_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
  revision BIGINT NOT NULL DEFAULT 1,
  UNIQUE (workspace_id, id)
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_connector_shop
  ON ing.connector(workspace_id, connector_code, (config->>'shop_domain'));
CREATE TABLE IF NOT EXISTS ing.sync_job (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id UUID NOT NULL,
  connector_id UUID NOT NULL,
  job_type TEXT NOT NULL DEFAULT 'shopify.manual',
  params JSONB NOT NULL DEFAULT '{}'::jsonb,
  state TEXT NOT NULL DEFAULT 'queued'
    CHECK (state IN ('queued','running','succeeded','failed','cancelled')),
  queued_at timestamptz NOT NULL DEFAULT now(), started_at timestamptz,
  finished_at timestamptz,
  error_code TEXT, trace_id TEXT NOT NULL,
  produced_raw_count INT NOT NULL DEFAULT 0,
  FOREIGN KEY (workspace_id, connector_id) REFERENCES ing.connector(workspace_id,id)
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_shopify_sync_active ON ing.sync_job(connector_id)
  WHERE state IN ('queued','running');
CREATE TABLE IF NOT EXISTS ing.raw_payload (
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  workspace_id UUID NOT NULL, connector_id UUID NOT NULL,
  source_system TEXT NOT NULL DEFAULT 'shopify', object_type TEXT NOT NULL,
  external_id TEXT NOT NULL, external_version TEXT,
  idempotency_key TEXT NOT NULL, received_at timestamptz NOT NULL DEFAULT now(),
  source_ts timestamptz, content_hash TEXT NOT NULL,
  storage TEXT NOT NULL DEFAULT 'inline' CHECK (storage='inline'),
  body JSONB NOT NULL, pii_class TEXT NOT NULL DEFAULT 'none' CHECK (pii_class='none'),
  PRIMARY KEY (id, received_at),
  FOREIGN KEY (workspace_id, connector_id) REFERENCES ing.connector(workspace_id,id)
) PARTITION BY RANGE (received_at);
CREATE TABLE IF NOT EXISTS ing.raw_payload_default PARTITION OF ing.raw_payload DEFAULT;
-- Partition-independent idempotency claim; claim and payload commit together.
CREATE TABLE IF NOT EXISTS ing.raw_receipt (
  workspace_id UUID NOT NULL, connector_id UUID NOT NULL,
  idempotency_key TEXT NOT NULL, raw_id UUID NOT NULL, received_at timestamptz NOT NULL,
  PRIMARY KEY (connector_id,idempotency_key),
  FOREIGN KEY (workspace_id,connector_id) REFERENCES ing.connector(workspace_id,id)
);
GRANT USAGE ON SCHEMA ing TO app_rw;
GRANT SELECT, INSERT, UPDATE ON ing.connector, ing.sync_job TO app_rw;
GRANT SELECT, INSERT ON ing.raw_payload, ing.raw_receipt TO app_rw;
REVOKE UPDATE, DELETE, TRUNCATE ON ing.raw_payload, ing.raw_payload_default, ing.raw_receipt FROM app_rw;
DO $$ DECLARE tbl text; BEGIN
  FOREACH tbl IN ARRAY ARRAY['ing.connector','ing.sync_job','ing.raw_payload','ing.raw_payload_default','ing.raw_receipt'] LOOP
    EXECUTE format('ALTER TABLE %s ENABLE ROW LEVEL SECURITY', tbl);
    EXECUTE format('ALTER TABLE %s FORCE ROW LEVEL SECURITY', tbl);
    IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polrelid=tbl::regclass AND polname='workspace_isolation') THEN
      EXECUTE format('CREATE POLICY workspace_isolation ON %s TO app_rw USING
        (workspace_id=NULLIF(current_setting(''app.workspace_id'',true),'''')::uuid) WITH CHECK
        (workspace_id=NULLIF(current_setting(''app.workspace_id'',true),'''')::uuid)', tbl);
    END IF;
  END LOOP;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='raw_no_change' AND tgrelid='ing.raw_payload'::regclass) THEN
    CREATE TRIGGER raw_no_change BEFORE UPDATE OR DELETE ON ing.raw_payload
      FOR EACH ROW EXECUTE FUNCTION platform.reject_audit_mutation();
    CREATE TRIGGER raw_no_truncate BEFORE TRUNCATE ON ing.raw_payload
      FOR EACH STATEMENT EXECUTE FUNCTION platform.reject_audit_mutation();
    CREATE TRIGGER raw_no_truncate BEFORE TRUNCATE ON ing.raw_payload_default
      FOR EACH STATEMENT EXECUTE FUNCTION platform.reject_audit_mutation();
    CREATE TRIGGER receipt_no_change BEFORE UPDATE OR DELETE ON ing.raw_receipt
      FOR EACH ROW EXECUTE FUNCTION platform.reject_audit_mutation();
    CREATE TRIGGER receipt_no_truncate BEFORE TRUNCATE ON ing.raw_receipt
      FOR EACH STATEMENT EXECUTE FUNCTION platform.reject_audit_mutation();
  END IF;
END $$;
