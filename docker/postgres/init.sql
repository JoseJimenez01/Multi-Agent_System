CREATE TABLE IF NOT EXISTS task_log (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL DEFAULT gen_random_uuid(),
    task_type VARCHAR(100) NOT NULL,
    input_text TEXT,
    agent_used VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    result_text TEXT,
    confidence REAL,
    tokens_used INTEGER DEFAULT 0,
    cost_usd REAL DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS agent_registry (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    capabilities JSONB,
    model_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS knowledge_base_metadata (
    id SERIAL PRIMARY KEY,
    collection_name VARCHAR(100) NOT NULL,
    source VARCHAR(255),
    chunk_count INTEGER DEFAULT 0,
    embedding_model VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_task_log_session ON task_log(session_id);
CREATE INDEX idx_task_log_created ON task_log(created_at DESC);
CREATE INDEX idx_task_log_type ON task_log(task_type);
