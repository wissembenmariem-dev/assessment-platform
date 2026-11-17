CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_cron";

CREATE TABLE IF NOT EXISTS recruiters (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email       TEXT UNIQUE NOT NULL,
    name        TEXT NOT NULL,
    role        TEXT NOT NULL DEFAULT 'advisor',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sessions (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recruiter_id     UUID NOT NULL REFERENCES recruiters(id) ON DELETE CASCADE,
    candidate_name   TEXT NOT NULL,
    candidate_email  TEXT NOT NULL,
    level            TEXT NOT NULL CHECK (level IN ('bachelier', 'master')),
    modules          JSONB NOT NULL,
    position_visee   TEXT,
    entreprise_cible TEXT,
    lang             TEXT NOT NULL DEFAULT 'fr',
    token            TEXT UNIQUE NOT NULL,
    status           TEXT NOT NULL DEFAULT 'pending',
    score_global     INT,

    expires_at       TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '12 months'),

    consent_at       TIMESTAMPTZ,
    consent_version  TEXT,
    consent_ip       TEXT,

    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at       TIMESTAMPTZ,
    completed_at     TIMESTAMPTZ
);

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS sessions_updated_at ON sessions;
CREATE TRIGGER sessions_updated_at
    BEFORE UPDATE ON sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
CREATE INDEX IF NOT EXISTS idx_sessions_recruiter ON sessions(recruiter_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);

CREATE TABLE IF NOT EXISTS questions (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug        TEXT UNIQUE NOT NULL,
    module      INT NOT NULL,
    level       TEXT NOT NULL DEFAULT 'both',
    position    INT NOT NULL,
    type        TEXT NOT NULL,
    lang        TEXT NOT NULL,
    category    TEXT,
    text        TEXT NOT NULL,
    instruction TEXT,
    options     JSONB NOT NULL,
    correct     JSONB,
    difficulty  INT DEFAULT 1,
    meta        JSONB,
    scoring     JSONB
);

CREATE INDEX IF NOT EXISTS idx_questions_module_lang_level ON questions(module, lang, level);
CREATE INDEX IF NOT EXISTS idx_questions_level ON questions(level);

CREATE TABLE IF NOT EXISTS answers (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id    UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    question_id   UUID NOT NULL REFERENCES questions(id),
    module        INT NOT NULL,
    response      JSONB NOT NULL,
    answered_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_answers_session ON answers(session_id);

CREATE TABLE IF NOT EXISTS scores (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    session_id      UUID UNIQUE NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,

    m1_raw          INT,
    m1_level        TEXT,
    m1_by_section   JSONB,

    m2_ocean        JSONB,

    m3_raw          INT,
    m3_level        TEXT,
    m3_by_dim       JSONB,
    m3_style        TEXT,

    m4_engagement   INT,
    m4_values       JSONB,

    global          INT,
    global_label    TEXT,

    signals         JSONB,

    report_text     JSONB,

    model_used      TEXT,
    computed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE answers  ENABLE ROW LEVEL SECURITY;
ALTER TABLE scores   ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "recruiter_own_sessions" ON sessions;
CREATE POLICY "recruiter_own_sessions" ON sessions
    FOR ALL USING (recruiter_id = auth.uid());

DROP POLICY IF EXISTS "recruiter_own_scores" ON scores;
CREATE POLICY "recruiter_own_scores" ON scores
    FOR ALL USING (
        session_id IN (
            SELECT id FROM sessions WHERE recruiter_id = auth.uid()
        )
    );

SELECT cron.schedule(
    'purge-expired-sessions',
    '0 2 * * 0',
    $$
        DELETE FROM sessions WHERE expires_at < NOW();
    $$
);

INSERT INTO recruiters (email, name, role)
VALUES ('admin@example.com', 'Admin', 'admin')
ON CONFLICT (email) DO NOTHING;
