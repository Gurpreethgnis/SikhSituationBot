-- Issue #42: cross-session user memory (run once on PostgreSQL)
-- After applying, restart the app. SQLite dev DBs can use db.create_all() on a fresh DB instead.

ALTER TABLE users
  ADD COLUMN IF NOT EXISTS memory_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  ADD COLUMN IF NOT EXISTS memory_retention_days INTEGER NOT NULL DEFAULT 90;

CREATE TABLE IF NOT EXISTS user_memories (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  fact_type VARCHAR(50) NOT NULL,
  content TEXT NOT NULL,
  source_chat_id INTEGER REFERENCES chats(id) ON DELETE SET NULL,
  source_user_message_id INTEGER REFERENCES messages(id) ON DELETE SET NULL,
  source_assistant_message_id INTEGER REFERENCES messages(id) ON DELETE SET NULL,
  importance INTEGER NOT NULL DEFAULT 5,
  is_pinned BOOLEAN NOT NULL DEFAULT FALSE,
  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
  updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE INDEX IF NOT EXISTS ix_user_memories_user_id ON user_memories (user_id);
CREATE INDEX IF NOT EXISTS ix_user_memories_user_active ON user_memories (user_id) WHERE is_deleted = FALSE;
