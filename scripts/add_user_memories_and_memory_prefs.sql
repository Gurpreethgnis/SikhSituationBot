-- Migration: user_memories table + memory preference columns on users.
-- Safe to re-run: IF NOT EXISTS / ADD COLUMN IF NOT EXISTS.
-- Run once against Railway Postgres (Query tab or psql).

-- 1. Memory preference columns on users (may already exist from models.py create_all)
ALTER TABLE users ADD COLUMN IF NOT EXISTS memory_enabled BOOLEAN DEFAULT TRUE NOT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS memory_retention_days INTEGER DEFAULT 90 NOT NULL;

-- 2. user_memories table
CREATE TABLE IF NOT EXISTS user_memories (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    fact_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    source_chat_id INTEGER REFERENCES chats(id) ON DELETE SET NULL,
    source_user_message_id INTEGER REFERENCES messages(id) ON DELETE SET NULL,
    source_assistant_message_id INTEGER REFERENCES messages(id) ON DELETE SET NULL,
    importance INTEGER DEFAULT 5 NOT NULL,
    is_pinned BOOLEAN DEFAULT FALSE NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Indexes for fast lookups
CREATE INDEX IF NOT EXISTS ix_user_memories_user_id ON user_memories (user_id);
CREATE INDEX IF NOT EXISTS ix_user_memories_user_deleted ON user_memories (user_id, is_deleted);

-- 4. Unique constraint to enforce idempotency (same user + same content = one row)
-- Uses a partial index so soft-deleted rows don't block re-insertion.
CREATE UNIQUE INDEX IF NOT EXISTS uq_user_memories_user_content
    ON user_memories (user_id, md5(content))
    WHERE is_deleted = FALSE;
