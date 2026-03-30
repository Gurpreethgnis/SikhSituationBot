-- If email/password registration returns 500, your `users` table may predate newer columns.
-- Run once against Railway Postgres (Query tab or psql). Safe to re-run: IF NOT EXISTS skips existing columns.

ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500);
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(512);
ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_language VARCHAR(10) DEFAULT 'en';
ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_persona VARCHAR(20) DEFAULT 'adult';
ALTER TABLE users ADD COLUMN IF NOT EXISTS persona_source VARCHAR(20) DEFAULT 'default';
ALTER TABLE users ADD COLUMN IF NOT EXISTS birth_year INTEGER;
ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_theme VARCHAR(20) DEFAULT 'saffron';
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT false;
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;
ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP;
