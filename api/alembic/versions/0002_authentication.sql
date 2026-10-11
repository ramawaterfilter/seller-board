ALTER TABLE ws."user" ADD COLUMN IF NOT EXISTS failed_attempts INT NOT NULL DEFAULT 0
  CHECK (failed_attempts >= 0);
ALTER TABLE ws."user" ADD COLUMN IF NOT EXISTS locked_until timestamptz;
ALTER TABLE ws.session ADD COLUMN IF NOT EXISTS last_seen_at timestamptz NOT NULL DEFAULT now();
CREATE TABLE IF NOT EXISTS ws.auth_challenge (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES ws."user"(id),
  method TEXT NOT NULL CHECK (method IN ('totp','email')),
  code_hash TEXT,
  attempts INT NOT NULL DEFAULT 0 CHECK (attempts >= 0),
  expires_at timestamptz NOT NULL,
  consumed_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (method <> 'email' OR code_hash IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS ix_auth_challenge_user ON ws.auth_challenge(user_id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_active_totp ON ws.mfa_secret(user_id)
  WHERE method='totp' AND consumed_at IS NULL;
GRANT SELECT, INSERT, UPDATE ON ws.auth_challenge TO app_rw;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polrelid='ws.permission_scope'::regclass
                 AND polname='identity_memberships') THEN
    CREATE POLICY identity_memberships ON ws.permission_scope FOR SELECT TO app_rw
      USING (user_id = NULLIF(current_setting('app.actor_id', true), '')::uuid);
  END IF;
END $$;
