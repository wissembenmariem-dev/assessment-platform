ALTER TABLE sessions
  ADD COLUMN IF NOT EXISTS consent_at      TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS consent_version TEXT,
  ADD COLUMN IF NOT EXISTS consent_ip      TEXT;

ALTER TABLE sessions
  ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ
    NOT NULL DEFAULT (NOW() + INTERVAL '12 months');

CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);
