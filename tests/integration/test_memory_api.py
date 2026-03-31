"""
Integration tests for memory and thread-resume API routes.
Covers: POST /api/memory idempotency, GET /api/memory scoping,
DELETE /api/memory/<id>, POST /api/memory/clear, GET /api/threads/active,
PATCH /api/auth/me retention cap, graceful degradation.
"""

import json
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "server"))

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("DATABASE_URL_TEST", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-memory-int")

from app import app  # noqa: E402
from models import Chat, Message, User, UserMemory, db  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "helpers"))
from flask_test_auth import ask_auth_headers  # noqa: E402


def _ensure_user(app_instance, email, memory_enabled=True, memory_retention_days=90, birth_year=1990):
    """Create or fetch a user inside app context; returns (user_id, headers)."""
    with app_instance.app_context():
        u = User.query.filter_by(email=email).first()
        if not u:
            u = User(
                email=email,
                is_active=True,
                birth_year=birth_year,
                preferred_persona="adult",
                persona_source="profile",
                memory_enabled=memory_enabled,
                memory_retention_days=memory_retention_days,
            )
            db.session.add(u)
            db.session.commit()
        else:
            u.memory_enabled = memory_enabled
            u.memory_retention_days = memory_retention_days
            db.session.commit()
        uid = u.id
    headers = ask_auth_headers(app_instance, email=email, birth_year=birth_year)
    return uid, headers


class TestMemoryAPI(unittest.TestCase):
    """Integration tests for memory REST routes."""

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

    # --- POST /api/memory (idempotent write) ---

    def test_create_memory_success(self):
        uid, headers = _ensure_user(self.app, "int-mem-create@test.com")
        payload = {"fact_type": "situation", "content": "User is dealing with stress at work."}
        r = self.client.post("/api/memory", data=json.dumps(payload), headers=headers)
        self.assertIn(r.status_code, (200, 201))
        data = json.loads(r.data)
        self.assertIn("memory", data)
        self.assertEqual(data["memory"]["fact_type"], "situation")

    def test_create_memory_idempotent(self):
        """Writing the same content twice returns 200, not a second row."""
        uid, headers = _ensure_user(self.app, "int-mem-idem@test.com")
        payload = {"fact_type": "topic", "content": "Interested in meditation practices."}

        r1 = self.client.post("/api/memory", data=json.dumps(payload), headers=headers)
        self.assertIn(r1.status_code, (200, 201))
        d1 = json.loads(r1.data)

        r2 = self.client.post("/api/memory", data=json.dumps(payload), headers=headers)
        self.assertEqual(r2.status_code, 200)
        d2 = json.loads(r2.data)
        self.assertFalse(d2.get("created"))
        self.assertEqual(d1["memory"]["id"], d2["memory"]["id"])

    def test_create_memory_requires_content(self):
        uid, headers = _ensure_user(self.app, "int-mem-nocont@test.com")
        r = self.client.post("/api/memory", data=json.dumps({"fact_type": "topic", "content": ""}), headers=headers)
        self.assertEqual(r.status_code, 400)

    def test_create_memory_rejects_bad_fact_type(self):
        uid, headers = _ensure_user(self.app, "int-mem-badft@test.com")
        r = self.client.post("/api/memory", data=json.dumps({"fact_type": "invalid", "content": "Some valid content here."}), headers=headers)
        self.assertEqual(r.status_code, 400)

    def test_create_memory_blocked_when_disabled(self):
        uid, headers = _ensure_user(self.app, "int-mem-dis@test.com", memory_enabled=False)
        r = self.client.post("/api/memory", data=json.dumps({"fact_type": "topic", "content": "Should be blocked entirely."}), headers=headers)
        self.assertEqual(r.status_code, 403)

    def test_create_memory_requires_auth(self):
        r = self.client.post("/api/memory", data=json.dumps({"content": "Hello world content."}), content_type="application/json")
        self.assertEqual(r.status_code, 401)

    # --- GET /api/memory (user scoping) ---

    def test_list_memories_only_own(self):
        """A user should only see their own memories."""
        uid_a, headers_a = _ensure_user(self.app, "int-scope-a@test.com")
        uid_b, headers_b = _ensure_user(self.app, "int-scope-b@test.com")

        self.client.post("/api/memory", data=json.dumps({"fact_type": "topic", "content": "Memory from user A visible."}), headers=headers_a)
        self.client.post("/api/memory", data=json.dumps({"fact_type": "topic", "content": "Memory from user B visible."}), headers=headers_b)

        r_a = self.client.get("/api/memory", headers=headers_a)
        data_a = json.loads(r_a.data)
        contents_a = [m["content"] for m in data_a["memories"]]
        self.assertTrue(any("user A" in c for c in contents_a))
        self.assertFalse(any("user B" in c for c in contents_a))

    # --- DELETE /api/memory/<id> ---

    def test_delete_memory(self):
        uid, headers = _ensure_user(self.app, "int-mem-del@test.com")
        r = self.client.post("/api/memory", data=json.dumps({"fact_type": "topic", "content": "To be deleted in this test."}), headers=headers)
        mem_id = json.loads(r.data)["memory"]["id"]

        rd = self.client.delete(f"/api/memory/{mem_id}", headers=headers)
        self.assertEqual(rd.status_code, 200)

        # Should no longer appear in list
        rl = self.client.get("/api/memory", headers=headers)
        ids = [m["id"] for m in json.loads(rl.data)["memories"]]
        self.assertNotIn(mem_id, ids)

    def test_delete_other_users_memory_404(self):
        uid_a, headers_a = _ensure_user(self.app, "int-del-a@test.com")
        uid_b, headers_b = _ensure_user(self.app, "int-del-b@test.com")
        r = self.client.post("/api/memory", data=json.dumps({"fact_type": "topic", "content": "User A memory for delete test."}), headers=headers_a)
        mem_id = json.loads(r.data)["memory"]["id"]

        # User B tries to delete user A's memory
        rd = self.client.delete(f"/api/memory/{mem_id}", headers=headers_b)
        self.assertEqual(rd.status_code, 404)

    # --- POST /api/memory/clear ---

    def test_clear_memories(self):
        uid, headers = _ensure_user(self.app, "int-mem-clr@test.com")
        self.client.post("/api/memory", data=json.dumps({"fact_type": "topic", "content": "Memory one to clear in bulk."}), headers=headers)
        self.client.post("/api/memory", data=json.dumps({"fact_type": "situation", "content": "Memory two to clear in bulk."}), headers=headers)

        rc = self.client.post("/api/memory/clear", headers=headers)
        self.assertEqual(rc.status_code, 200)

        rl = self.client.get("/api/memory", headers=headers)
        self.assertEqual(len(json.loads(rl.data)["memories"]), 0)

    # --- GET /api/threads/active ---

    def test_active_thread_returns_latest(self):
        uid, headers = _ensure_user(self.app, "int-thread@test.com")
        # Create a chat
        rc = self.client.post("/api/chats", data=json.dumps({"title": "My latest chat"}), headers=headers)
        self.assertEqual(rc.status_code, 201)
        chat_id = json.loads(rc.data)["chat"]["id"]

        rt = self.client.get("/api/threads/active", headers=headers)
        self.assertEqual(rt.status_code, 200)
        data = json.loads(rt.data)
        self.assertIsNotNone(data["thread"])
        self.assertEqual(data["thread"]["id"], chat_id)

    def test_active_thread_no_chats(self):
        """User with no chats should get thread: null."""
        uid, headers = _ensure_user(self.app, "int-thread-empty@test.com")
        # Ensure no chats exist for this user
        with self.app.app_context():
            Chat.query.filter_by(user_id=uid).delete()
            db.session.commit()

        rt = self.client.get("/api/threads/active", headers=headers)
        self.assertEqual(rt.status_code, 200)
        data = json.loads(rt.data)
        self.assertIsNone(data["thread"])

    def test_active_thread_includes_messages(self):
        uid, headers = _ensure_user(self.app, "int-thread-msg@test.com")
        rc = self.client.post("/api/chats", data=json.dumps({"title": "Chat with msgs"}), headers=headers)
        chat_id = json.loads(rc.data)["chat"]["id"]

        # Insert a message directly
        with self.app.app_context():
            msg = Message(chat_id=chat_id, role="user", content="Hello from test", persona="adult", language="en")
            db.session.add(msg)
            db.session.commit()

        rt = self.client.get("/api/threads/active", headers=headers)
        data = json.loads(rt.data)
        self.assertIsNotNone(data["thread"])
        self.assertTrue(len(data["thread"].get("messages", [])) >= 1)

    def test_active_thread_requires_auth(self):
        rt = self.client.get("/api/threads/active")
        self.assertEqual(rt.status_code, 401)

    # --- PATCH /api/auth/me retention cap ---

    def test_retention_capped_at_365(self):
        uid, headers = _ensure_user(self.app, "int-ret-cap@test.com")
        r = self.client.patch(
            "/api/auth/me",
            data=json.dumps({"memory_retention_days": 9999}),
            headers=headers,
        )
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        # Value > 365 should have been ignored (not applied)
        self.assertLessEqual(data["user"]["memory_retention_days"], 365)

    def test_retention_valid_value_accepted(self):
        uid, headers = _ensure_user(self.app, "int-ret-ok@test.com")
        r = self.client.patch(
            "/api/auth/me",
            data=json.dumps({"memory_retention_days": 180}),
            headers=headers,
        )
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        self.assertEqual(data["user"]["memory_retention_days"], 180)


if __name__ == "__main__":
    unittest.main()
