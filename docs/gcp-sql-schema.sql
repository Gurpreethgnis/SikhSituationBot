-- SQL Schema for Google Cloud SQL (PostgreSQL)
-- This schema supports pgvector for semantic search.

-- 1. Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Create the shabads table
CREATE TABLE IF NOT EXISTS shabads (
    id SERIAL PRIMARY KEY,
    shabad_id VARCHAR(50) UNIQUE NOT NULL,
    gurmukhi TEXT NOT NULL,
    romanization TEXT,
    english_translation TEXT NOT NULL,
    source VARCHAR(100),
    recommended_persona VARCHAR(20) DEFAULT 'any',
    context_tags TEXT[], -- Array of strings for quick filtering
    embedding vector(384), -- 384 dimensions for all-MiniLM-L6-v2, 768 for Gecko
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Create an index for faster vector search
-- Using IVFFlat or HNSW (HNSW is generally better for performance)
CREATE INDEX ON shabads USING hnsw (embedding vector_cosine_ops);

-- 4. Example search query
-- SELECT * FROM shabads 
-- ORDER BY embedding <=> '[your_query_vector]' 
-- LIMIT 5;
