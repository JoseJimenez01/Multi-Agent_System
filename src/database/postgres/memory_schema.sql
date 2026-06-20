-- Memoria conversacional e histórica (III-J de la especificación).
-- Vive en un schema separado ("memory") dentro del mismo Postgres que ya usa
-- el MCP Server para el schema "banco", para no colisionar con esos datos.
-- Idempotente: seguro de correr varias veces sin perder datos existentes.

CREATE SCHEMA IF NOT EXISTS memory;

CREATE TABLE IF NOT EXISTS memory.sessions (
    session_id  VARCHAR(64) PRIMARY KEY,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    summary     TEXT
);

CREATE TABLE IF NOT EXISTS memory.messages (
    id          BIGSERIAL PRIMARY KEY,
    session_id  VARCHAR(64) NOT NULL REFERENCES memory.sessions(session_id) ON DELETE CASCADE,
    timestamp   TIMESTAMPTZ NOT NULL DEFAULT now(),
    role        VARCHAR(16) NOT NULL CHECK (role IN ('user', 'assistant')),
    content     TEXT NOT NULL,
    agent_used  VARCHAR(32),
    metadata    JSONB
);

CREATE INDEX IF NOT EXISTS idx_memory_messages_session   ON memory.messages(session_id);
CREATE INDEX IF NOT EXISTS idx_memory_messages_timestamp ON memory.messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_memory_messages_agent     ON memory.messages(agent_used);
