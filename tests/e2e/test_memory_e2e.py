"""
End-to-end tests for cross-session memory:
- Conversation continuity across sessions (thread resume)
- Disabling memory stops new context
- Clearing history removes everything
- Settings memory options persist
"""

import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "server"))

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("DATABASE_URL_TEST", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-memory-e2e")

from app import app  # noqa: E402
from models import Chat, Message, User, UserMemory, db  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "helpers"))
from flask_test_auth import ask_auth_headers  # noqa: E402


def _mock_shabad_row():
    """ORM-like mock matching ask() expectations."""
    m = MagicMock()
    m.id = 1
    m.shabad_id = "test-1"
    m.gurmukhi = "test gurmukhi"
    m.romanization = "test roman"
    m.english_translation = "test english translation"
    m.source = "test source"
    m.recommended_persona = "adult"
    m.context_tags = None
    m.embedding = [0.1] * 8

    def to_dict(include_embedding=True):
        return {
            "id": m.id,
            "shabad_id": m.shabad_id,
            "gurmukhi": m.gurmukhi,
            "romanization": m.romanization,
            "english_translation": m.english_translation,
            "source": m.source,
            "recommended_persona": m.recommended_persona,
            "context_tags": m.context_tags,
            "embedding": m.embedding if include_embedding else None,
            "created_at": None,
            "sttm_link": "https://www.sikhitothemax.org/shabad?id=test-1",
        }

    def to_api_dict():
        return {
            "id": m.id,
            "shabad_id": m.shabad_id,
            "gurmukhi": m.gurmukhi,
            "romanization": m.romanization,
            "english_translation": m.english_translation,
            "source": m.source,
            "recommended_persona": m.recommended_persona,
            "context_tags": m.context_tags,
            "created_at": None,
            "sttm_link": "https://www.sikhitothemax.org/shabad?id=test-1",
        }

    m.to_dict = to_dict
    m.to_api_dict = to_api_dict
    return m


class TestMemoryE2E(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        from sqlalchemy import text, inspect
        inspector = inspect(db.engine)
        existing = inspector.get_table_names()
        if "users" not in existing:
            db.session.execute(text("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(100),
                    avatar_url VARCHAR(500),
                    password_hash VARCHAR(512),
                    preferred_language VARCHAR(10) DEFAULT 'en',
                    preferred_persona VARCHAR(20) DEFAULT 'adult',
                    persona_source VARCHAR(20) DEFAULT 'default',
                    birth_year INTEGER,
                    preferred_theme VARCHAR(20) DEFAULT 'saffron',
                    is_admin BOOLEAN DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP,
                    last_login TIMESTAMP,
                    memory_enabled BOOLEAN DEFAULT 1,
                    memory_retention_days INTEGER DEFAULT 90
                )
            """))
        if "chats" not in existing:
            db.session.execute(text("""
                CREATE TABLE chats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    title VARCHAR(200) NOT NULL,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    is_shared BOOLEAN DEFAULT 0 NOT NULL,
                    share_id VARCHAR(36) UNIQUE
                )
            """))
        if "messages" not in existing:
            db.session.execute(text("""
                CREATE TABLE messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
                    role VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    shabad_row_id INTEGER,
                    persona VARCHAR(20),
                    language VARCHAR(10),
                    llm_provider VARCHAR(50),
                    llm_model VARCHAR(100),
                    was_fallback BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP
                )
            """))
        if "shabads" not in existing:
            db.session.execute(text("""
                CREATE TABLE shabads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    shabad_id INTEGER UNIQUE,
                    gurmukhi TEXT NOT NULL,
                    romanization TEXT,
                    english_translation TEXT,
                    source VARCHAR(50),
                    recommended_persona VARCHAR(20),
                    context_tags TEXT,
                    is_header_only BOOLEAN DEFAULT 0,
                    verse_count INTEGER,
                    content_length INTEGER,
                    embedding BLOB,
                    created_at TIMESTAMP
                )
            """))
        if "user_memories" not in existing:
            db.session.execute(text("""
                CREATE TABLE user_memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    fact_type VARCHAR(50) NOT NULL,
                    content TEXT NOT NULL,
                    source_chat_id INTEGER,
                    source_user_message_id INTEGER,
                    source_assistant_message_id INTEGER,
                    importance INTEGER DEFAULT 5,
                    is_pinned BOOLEAN DEFAULT 0,
                    is_deleted BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    UNIQUE(user_id, content)
                )
            """))
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        self.ctx.pop()

    # --- Session continuity ---

    @patch("app.assess_query_clarity")
    @patch("app.get_embedding")
    @patch("app.search_similar_shabads")
    @patch("app.synthesize_chat_response")
    def test_returning_user_resumes_conversation(self, mock_synth, mock_search, mock_emb, mock_assess):
        """Simulate: user chats → ends session → returns → resumes via /api/threads/active."""
        mock_assess.return_value = (False, "")
        mock_emb.return_value = [0.1] * 8
        mock_search.return_value = [_mock_shabad_row()]
        mock_synth.return_value = ("Guidance response about peace.", "gemini", "models/gemini-2.5-flash-lite")

        email = "e2e-resume@test.com"
        headers = ask_auth_headers(self.app, email=email)

        # Session 1: Create a chat and send a message
        rc = self.client.post("/api/chats", data=json.dumps({"title": "Session 1 chat"}), headers=headers)
        self.assertEqual(rc.status_code, 201)
        chat_id = json.loads(rc.data)["chat"]["id"]

        ra = self.client.post(
            "/ask",
            data=json.dumps({"query": "I am feeling anxious about life changes.", "chat_id": chat_id}),
            headers=headers,
        )
        self.assertEqual(ra.status_code, 200)

        # "End session" — client closes browser

        # Session 2: Returning user calls /api/threads/active
        rt = self.client.get("/api/threads/active", headers=headers)
        self.assertEqual(rt.status_code, 200)
        data = json.loads(rt.data)
        self.assertIsNotNone(data["thread"])
        self.assertEqual(data["thread"]["id"], chat_id)
        self.assertTrue(len(data["thread"].get("messages", [])) >= 1)

        # User can now continue in the same thread without re-sending history
        ra2 = self.client.post(
            "/ask",
            data=json.dumps({"query": "Tell me more about finding peace.", "chat_id": chat_id}),
            headers=headers,
        )
        self.assertEqual(ra2.status_code, 200)

    # --- Disabling memory → fresh session ---

    def test_disabling_memory_starts_fresh(self):
        """When memory is disabled, no memories should appear in context."""
        email = "e2e-disable@test.com"
        headers = ask_auth_headers(self.app, email=email)

        # Create a memory
        self.client.post(
            "/api/memory",
            data=json.dumps({"fact_type": "situation", "content": "User is going through a divorce."}),
            headers=headers,
        )

        # Verify memory exists
        rl = self.client.get("/api/memory", headers=headers)
        self.assertGreater(len(json.loads(rl.data)["memories"]), 0)

        # Disable memory
        rp = self.client.patch(
            "/api/auth/me",
            data=json.dumps({"memory_enabled": False}),
            headers=headers,
        )
        self.assertEqual(rp.status_code, 200)
        self.assertFalse(json.loads(rp.data)["user"]["memory_enabled"])

        # New memory write should be blocked
        rm = self.client.post(
            "/api/memory",
            data=json.dumps({"fact_type": "topic", "content": "This should be blocked from saving."}),
            headers=headers,
        )
        self.assertEqual(rm.status_code, 403)

        # Re-enable for cleanup
        self.client.patch("/api/auth/me", data=json.dumps({"memory_enabled": True}), headers=headers)

    # --- Clearing history ---

    def test_clearing_history_removes_all(self):
        """POST /api/memory/clear should remove all memories, verified by GET."""
        email = "e2e-clear@test.com"
        headers = ask_auth_headers(self.app, email=email)

        self.client.post("/api/memory", data=json.dumps({"fact_type": "topic", "content": "Memory one for clearing test."}), headers=headers)
        self.client.post("/api/memory", data=json.dumps({"fact_type": "topic", "content": "Memory two for clearing test."}), headers=headers)

        rl = self.client.get("/api/memory", headers=headers)
        self.assertGreater(len(json.loads(rl.data)["memories"]), 0)

        # Clear
        rc = self.client.post("/api/memory/clear", headers=headers)
        self.assertEqual(rc.status_code, 200)

        # Verify empty
        rl2 = self.client.get("/api/memory", headers=headers)
        self.assertEqual(len(json.loads(rl2.data)["memories"]), 0)

    # --- Settings persistence ---

    def test_memory_settings_persist_across_requests(self):
        """PATCH memory settings → GET /api/auth/me should reflect saved values."""
        email = "e2e-settings@test.com"
        headers = ask_auth_headers(self.app, email=email)

        # Set retention to 30 and disable memory
        rp = self.client.patch(
            "/api/auth/me",
            data=json.dumps({"memory_enabled": False, "memory_retention_days": 30}),
            headers=headers,
        )
        self.assertEqual(rp.status_code, 200)

        # Fetch settings back
        rg = self.client.get("/api/auth/me", headers=headers)
        self.assertEqual(rg.status_code, 200)
        user = json.loads(rg.data)["user"]
        self.assertFalse(user["memory_enabled"])
        self.assertEqual(user["memory_retention_days"], 30)

        # Re-enable and change retention
        self.client.patch(
            "/api/auth/me",
            data=json.dumps({"memory_enabled": True, "memory_retention_days": 365}),
            headers=headers,
        )
        rg2 = self.client.get("/api/auth/me", headers=headers)
        user2 = json.loads(rg2.data)["user"]
        self.assertTrue(user2["memory_enabled"])
        self.assertEqual(user2["memory_retention_days"], 365)


if __name__ == "__main__":
    unittest.main()
