import json
import os
import sys
import unittest
import uuid
from unittest.mock import MagicMock, patch

# Add server directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "server"))

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("DATABASE_URL_TEST", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-for-integration")

from app import app  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "helpers"))
from flask_test_auth import ask_auth_headers  # noqa: E402


def _reg_test_password_primary() -> str:
    """8+ chars for /api/auth/register tests; not a real credential."""
    return bytes.fromhex("6162636465666768").decode("ascii")


def _reg_test_password_alt() -> str:
    """Distinct 8+ char value for conflict-path assertions in register tests."""
    return bytes.fromhex("78797a3132333435").decode("ascii")


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


class TestAppIntegration(unittest.TestCase):
    """Integration tests for Flask application endpoints."""

    def setUp(self):
        self.app = app
        self.client = self.app.test_client()
        self.app.config["TESTING"] = True

        self.valid_ask_request = {
            "query": "What does Gurbani say about finding peace after loss?",
            "persona": "adult",
        }

        self.invalid_ask_request = {"query": "", "persona": "adult"}

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "healthy")

    def test_cors_headers(self):
        response = self.client.get("/health")
        self.assertIn("Access-Control-Allow-Origin", response.headers)

    @patch("app.Shabad")
    def test_knowledge_stats_endpoint(self, mock_shabad):
        mock_shabad.query.count.return_value = 42
        response = self.client.get("/api/stats/knowledge")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("shabad_count", data)
        self.assertEqual(data["shabad_count"], 42)

    @patch("app.assess_query_clarity")
    @patch("app.get_embedding")
    @patch("app.search_similar_shabads")
    @patch("app.synthesize_chat_response")
    def test_ask_endpoint_success(self, mock_synth, mock_search, mock_emb, mock_assess):
        mock_assess.return_value = (False, "")
        mock_emb.return_value = [0.1] * 8
        mock_search.return_value = [_mock_shabad_row()]
        mock_synth.return_value = (
            "Synthesized guidance.\n\n[SUGGESTIONS]\n- a\n- b\n- c",
            "gemini",
            "models/gemini-2.5-flash-lite",
        )

        response = self.client.post(
            "/ask",
            data=json.dumps(self.valid_ask_request),
            headers=ask_auth_headers(self.app, email="itest-ask@example.com"),
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("response", data)
        self.assertIn("persona", data)
        self.assertEqual(data["persona"], "adult")
        self.assertFalse(data.get("is_clarification"))
        self.assertIn("shabad", data)
        self.assertIsNotNone(data["shabad"])
        self.assertIn("sttm_link", data["shabad"])

    @patch("app.assess_query_clarity")
    @patch("app.get_embedding")
    @patch("app.search_similar_shabads")
    @patch("app.synthesize_chat_response")
    def test_ask_parmaan_skips_clarification_when_query_seems_vague(
        self, mock_synth, mock_search, mock_emb, mock_assess
    ):
        """Short Gurbani-style lines must not trigger guidance clarification in Parmaan mode."""
        mock_assess.return_value = (True, "vague")
        mock_emb.return_value = [0.1] * 8
        mock_search.return_value = [_mock_shabad_row()]
        mock_synth.return_value = (
            "Here is verse #1… [Open on SikhiToTheMax](https://example)\n\n[SUGGESTIONS]\n- a\n- b\n- c",
            "gemini",
            "models/gemini-2.5-flash-lite",
        )

        response = self.client.post(
            "/ask",
            data=json.dumps(
                {
                    "query": "sukh tera ditta lahiye",
                    "persona": "adult",
                    "guidance_mode": "parmaan",
                    "parmaan_discovery_type": "similar",
                    "parmaan_shabad_count": 3,
                }
            ),
            headers=ask_auth_headers(self.app, email="itest-ask@example.com"),
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertFalse(data.get("is_clarification"))
        self.assertEqual(data.get("guidance_mode"), "parmaan")
        mock_synth.assert_called_once()
        kwargs = mock_synth.call_args.kwargs
        self.assertEqual(kwargs.get("guidance_mode"), "parmaan")
        self.assertEqual(kwargs.get("parmaan_discovery_type"), "similar")

    @patch("app.assess_query_clarity")
    @patch("app.get_embedding")
    @patch("app.search_similar_shabads")
    @patch("llm_synthesis._generate_gemini")
    def test_ask_parmaan_prepends_canonical_database_text(
        self, mock_gen, mock_search, mock_emb, mock_assess
    ):
        """Issue #49: Parmaan replies must include server-built verbatim blocks before LLM prose."""
        mock_assess.return_value = (False, "")
        mock_emb.return_value = [0.1] * 8
        mock_search.return_value = [_mock_shabad_row()]
        mock_gen.return_value = "Theme commentary only.\n\n[SUGGESTIONS]\n- a\n- b\n- c"

        response = self.client.post(
            "/ask",
            data=json.dumps(
                {
                    "query": "Satgur teri aasa",
                    "persona": "adult",
                    "guidance_mode": "parmaan",
                    "parmaan_discovery_type": "similar",
                    "parmaan_shabad_count": 2,
                }
            ),
            headers=ask_auth_headers(self.app, email="itest-ask@example.com"),
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("response", data)
        self.assertIn("Retrieved Gurbani (verbatim from database)", data["response"])
        self.assertIn("test gurmukhi", data["response"])
        self.assertIn("test english translation", data["response"])
        self.assertIn("Theme commentary only.", data["response"])
        mock_gen.assert_called()

    @patch("app.assess_query_clarity")
    @patch("app.get_embedding")
    @patch("app.search_similar_shabads")
    def test_ask_endpoint_no_shabads_found(self, mock_search, mock_emb, mock_assess):
        mock_assess.return_value = (False, "")
        mock_emb.return_value = [0.1] * 8
        mock_search.return_value = []

        response = self.client.post(
            "/ask",
            data=json.dumps(self.valid_ask_request),
            headers=ask_auth_headers(self.app, email="itest-ask@example.com"),
        )
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn("error", data)

    def test_ask_endpoint_invalid_json(self):
        response = self.client.post("/ask", data="invalid json", content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_ask_endpoint_empty_query(self):
        response = self.client.post(
            "/ask",
            data=json.dumps(self.invalid_ask_request),
            headers=ask_auth_headers(self.app, email="itest-ask@example.com"),
        )
        self.assertEqual(response.status_code, 400)

    def test_ask_requires_authentication(self):
        response = self.client.post(
            "/ask",
            data=json.dumps(self.valid_ask_request),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn("error", data)

    @patch("app.assess_query_clarity")
    @patch("app.get_embedding")
    @patch("app.search_similar_shabads")
    @patch("app.synthesize_chat_response")
    def test_ask_invalid_persona_defaults(self, mock_synth, mock_search, mock_emb, mock_assess):
        mock_assess.return_value = (False, "")
        mock_emb.return_value = [0.1] * 8
        mock_search.return_value = [_mock_shabad_row()]
        mock_synth.return_value = ("ok", "gemini", "models/gemini-2.5-flash-lite")

        response = self.client.post(
            "/ask",
            data=json.dumps({"query": "clear specific question about grief", "persona": "invalid"}),
            headers=ask_auth_headers(self.app, email="itest-ask@example.com"),
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["persona"], "adult")

    @patch("app.get_random_shabads")
    def test_random_shabads_endpoint_success(self, mock_get_random):
        mock_get_random.return_value = [_mock_shabad_row()]

        response = self.client.get("/random-shabads?limit=3")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("shabads", data)
        self.assertEqual(len(data["shabads"]), 1)
        self.assertIn("sttm_link", data["shabads"][0])

    @patch("app.get_random_shabads")
    def test_random_shabads_empty(self, mock_get_random):
        mock_get_random.return_value = []
        response = self.client.get("/random-shabads?limit=3")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["shabads"], [])

    def test_parmaans_categories(self):
        r = self.client.get("/api/parmaans/categories")
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        self.assertIn("categories", data)

    @patch("app.get_embedding")
    @patch("app.search_similar_shabads")
    def test_parmaans_search(self, mock_search, mock_emb):
        mock_emb.return_value = [0.1] * 8
        mock_search.return_value = [_mock_shabad_row()]
        r = self.client.post(
            "/api/parmaans/search",
            data=json.dumps({"query": "peace"}),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        self.assertTrue(data["shabads"])

    def test_register_new_user(self):
        email = f"reg-{uuid.uuid4().hex[:10]}@example.com"
        r = self.client.post(
            "/api/auth/register",
            data=json.dumps(
                {"email": email, "password": _reg_test_password_primary(), "name": "New"}
            ),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 201, r.data)
        data = json.loads(r.data)
        self.assertIn("token", data)
        self.assertEqual(data["user"]["email"], email)

    def test_register_oauth_only_adds_password(self):
        from models import User, db

        oemail = f"oauth-{uuid.uuid4().hex[:10]}@example.com"
        with app.app_context():
            db.session.add(User(email=oemail, name="O", password_hash=None))
            db.session.commit()

        r = self.client.post(
            "/api/auth/register",
            data=json.dumps({"email": oemail, "password": _reg_test_password_primary()}),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 201, r.data)
        self.assertIn("token", json.loads(r.data))

        r2 = self.client.post(
            "/api/auth/register",
            data=json.dumps({"email": oemail, "password": _reg_test_password_alt()}),
            content_type="application/json",
        )
        self.assertEqual(r2.status_code, 409)


if __name__ == "__main__":
    unittest.main()
