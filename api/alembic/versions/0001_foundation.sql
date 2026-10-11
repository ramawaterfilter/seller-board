CREATE EXTENSION IF NOT EXISTS citext;
CREATE SCHEMA IF NOT EXISTS ws;
CREATE SCHEMA IF NOT EXISTS platform;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_rw') THEN
    CREATE ROLE app_rw NOLOGIN NOSUPERUSER NOBYPASSRLS;
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_rw' AND (rolsuper OR rolbypassrls)) THEN
    RAISE EXCEPTION 'app_rw must not bypass row security';
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS ws.workspace (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  reporting_currency CHAR(3) NOT NULL DEFAULT 'INR',
  fx_policy TEXT NOT NULL DEFAULT 'order' CHECK (fx_policy IN ('order','posted','settlement')),
  retention_months INT NOT NULL DEFAULT 60 CHECK (retention_months > 0),
  demo_mode BOOLEAN NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  revision BIGINT NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS ws."user" (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email CITEXT NOT NULL UNIQUE,
  display_name TEXT NOT NULL,
  password_hash TEXT,
  mfa_totp_secret_enc BYTEA,
  mfa_email_enabled BOOLEAN NOT NULL DEFAULT true,
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('invited','active','disabled')),
  locale TEXT NOT NULL DEFAULT 'en-IN',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  revision BIGINT NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS ws.role (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id UUID NOT NULL REFERENCES ws.workspace(id),
  name TEXT NOT NULL,
  is_system BOOLEAN NOT NULL DEFAULT false,
  UNIQUE (workspace_id, name),
  UNIQUE (workspace_id, id)
);
CREATE TABLE IF NOT EXISTS ws.permission_scope (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id UUID NOT NULL REFERENCES ws.workspace(id),
  user_id UUID NOT NULL REFERENCES ws."user"(id),
  role_id UUID NOT NULL,
  function_code TEXT NOT NULL,
  product_scope TEXT NOT NULL DEFAULT '*',
  market_scope TEXT NOT NULL DEFAULT '*',
  granted_by UUID REFERENCES ws."user"(id),
  granted_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz,
  FOREIGN KEY (workspace_id, role_id) REFERENCES ws.role(workspace_id, id),
  UNIQUE (workspace_id, user_id, function_code, product_scope, market_scope)
);
CREATE INDEX IF NOT EXISTS ix_permission_scope_user ON ws.permission_scope(user_id, workspace_id);
CREATE TABLE IF NOT EXISTS ws.session (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES ws."user"(id),
  token_hash TEXT NOT NULL UNIQUE,
  created_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL,
  revoked_at timestamptz,
  mfa_verified_at timestamptz,
  CHECK (expires_at > created_at)
);
CREATE INDEX IF NOT EXISTS ix_session_user ON ws.session(user_id);
CREATE TABLE IF NOT EXISTS ws.mfa_secret (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES ws."user"(id),
  method TEXT NOT NULL CHECK (method IN ('totp','email')),
  secret_enc BYTEA,
  challenge_hash TEXT,
  expires_at timestamptz,
  attempts INT NOT NULL DEFAULT 0 CHECK (attempts >= 0),
  last_verified_step BIGINT,
  consumed_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK ((method = 'totp' AND secret_enc IS NOT NULL) OR
         (method = 'email' AND challenge_hash IS NOT NULL AND expires_at IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS ix_mfa_user ON ws.mfa_secret(user_id);
CREATE TABLE IF NOT EXISTS platform.job (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id UUID NOT NULL REFERENCES ws.workspace(id),
  kind TEXT NOT NULL,
  idempotency_key TEXT NOT NULL,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  status TEXT NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending','running','succeeded','failed')),
  attempts INT NOT NULL DEFAULT 0 CHECK (attempts >= 0),
  run_after timestamptz NOT NULL DEFAULT now(),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz,
  error_code TEXT,
  UNIQUE (workspace_id, idempotency_key)
);
CREATE INDEX IF NOT EXISTS ix_job_pending ON platform.job(status, run_after);
CREATE TABLE IF NOT EXISTS platform.audit_log (
  id BIGSERIAL,
  workspace_id UUID REFERENCES ws.workspace(id),
  actor_user_id UUID REFERENCES ws."user"(id),
  actor_kind TEXT NOT NULL CHECK (actor_kind IN ('user','system','connector','ai')),
  action TEXT NOT NULL,
  entity_type TEXT,
  entity_id TEXT,
  before JSONB,
  after JSONB,
  ip INET,
  user_agent TEXT,
  trace_id TEXT NOT NULL,
  occurred_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id, occurred_at)
) PARTITION BY RANGE (occurred_at);
-- Initial catch-all partition; scheduled monthly partition creation comes with the worker.
CREATE TABLE IF NOT EXISTS platform.audit_log_default
  PARTITION OF platform.audit_log DEFAULT;
CREATE INDEX IF NOT EXISTS ix_audit_entity
  ON platform.audit_log(entity_type, entity_id, occurred_at DESC);

CREATE OR REPLACE FUNCTION platform.reject_audit_mutation() RETURNS trigger
LANGUAGE plpgsql AS $$ BEGIN
  RAISE EXCEPTION 'AUDIT_APPEND_ONLY' USING ERRCODE = '42501';
END $$;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'audit_no_change'
                 AND tgrelid = 'platform.audit_log'::regclass) THEN
    CREATE TRIGGER audit_no_change BEFORE UPDATE OR DELETE ON platform.audit_log
      FOR EACH ROW EXECUTE FUNCTION platform.reject_audit_mutation();
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'audit_no_truncate'
                 AND tgrelid = 'platform.audit_log'::regclass) THEN
    CREATE TRIGGER audit_no_truncate BEFORE TRUNCATE ON platform.audit_log
      FOR EACH STATEMENT EXECUTE FUNCTION platform.reject_audit_mutation();
    CREATE TRIGGER audit_no_truncate BEFORE TRUNCATE ON platform.audit_log_default
      FOR EACH STATEMENT EXECUTE FUNCTION platform.reject_audit_mutation();
  END IF;
END $$;

GRANT USAGE ON SCHEMA ws, platform TO app_rw;
GRANT SELECT, INSERT, UPDATE ON ws."user", ws.session, ws.mfa_secret TO app_rw;
GRANT SELECT, INSERT, UPDATE ON ws.workspace, ws.role, ws.permission_scope TO app_rw;
GRANT SELECT, INSERT, UPDATE ON platform.job TO app_rw;
GRANT SELECT, INSERT ON platform.audit_log TO app_rw;
GRANT USAGE ON SEQUENCE platform.audit_log_id_seq TO app_rw;
GRANT SELECT ON public.alembic_version TO app_rw;
REVOKE UPDATE, DELETE, TRUNCATE ON platform.audit_log, platform.audit_log_default FROM app_rw;

DO $$ DECLARE tbl text; predicate text; BEGIN
  FOREACH tbl IN ARRAY ARRAY['ws.workspace', 'ws.role', 'ws.permission_scope', 'platform.job'] LOOP
    predicate := CASE WHEN tbl = 'ws.workspace' THEN 'id' ELSE 'workspace_id' END
                 || ' = NULLIF(current_setting(''app.workspace_id'', true), '''')::uuid';
    EXECUTE format('ALTER TABLE %s ENABLE ROW LEVEL SECURITY', tbl);
    EXECUTE format('ALTER TABLE %s FORCE ROW LEVEL SECURITY', tbl);
    IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polrelid = tbl::regclass
                   AND polname = 'workspace_isolation') THEN
      EXECUTE format('CREATE POLICY workspace_isolation ON %s TO app_rw USING (%s) WITH CHECK (%s)',
                     tbl, predicate, predicate);
    END IF;
  END LOOP;
END $$;
ALTER TABLE platform.audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE platform.audit_log FORCE ROW LEVEL SECURITY;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polrelid = 'platform.audit_log'::regclass
                 AND polname = 'audit_read_scope') THEN
    CREATE POLICY audit_read_scope ON platform.audit_log FOR SELECT TO app_rw
      USING (workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid);
    CREATE POLICY audit_insert_scope ON platform.audit_log FOR INSERT TO app_rw
      WITH CHECK (workspace_id IS NULL OR
        workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid);
  END IF;
END $$;
