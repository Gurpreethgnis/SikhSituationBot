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

    @patch("app.find_shabads_by_first_letters")
    @patch("app.assess_query_clarity")
    @patch("app.get_embedding")
    @patch("app.search_similar_shabads")
    @patch("app.synthesize_chat_response")
    def test_ask_parmaan_skips_clarification_when_query_seems_vague(
        self, mock_synth, mock_search, mock_emb, mock_assess, mock_first_letters
    ):
        """Parmaan always returns top-5 disambiguation first; vague-query clarification is guidance-only."""
        mock_first_letters.return_value = []
        mock_assess.return_value = (True, "vague")
        mock_emb.return_value = [0.1] * 8
        mock_search.return_value = [_mock_shabad_row() for _ in range(5)]

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
        self.assertTrue(data.get("is_disambiguation"))
        self.assertEqual(data.get("guidance_mode"), "parmaan")
        self.assertEqual(len(data.get("disambiguation_candidates") or []), 5)
        mock_synth.assert_not_called()
        self.assertEqual(mock_search.call_args.kwargs.get("limit"), 5)

    @patch("app.find_similar_to_shabad")
    @patch("app.get_shabad_by_id")
    @patch("app.assess_query_clarity")
    @patch("app.get_embedding")
    @patch("app.search_similar_shabads")
    @patch("llm_synthesis._generate_gemini")
    def test_ask_parmaan_prepends_canonical_database_text(
        self, mock_gen, mock_search, mock_emb, mock_assess, mock_get_by_id, mock_find_sim
    ):
        """Issue #49: Parmaan replies must include server-built verbatim blocks before LLM prose."""
        mock_assess.return_value = (False, "")
        mock_emb.return_value = [0.1] * 8
        row = _mock_shabad_row()
        mock_get_by_id.return_value = row
        mock_find_sim.return_value = [row, row]
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
                    "anchor_shabad_id": "test-1",
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

    def test_ask_requires_birth_year(self):
        from models import User, db

        email = "itest-no-birthyear@example.com"
        with self.app.app_context():
            u = User.query.filter_by(email=email).first()
            if u:
                db.session.delete(u)
                db.session.commit()
            u = User(email=email, is_active=True, birth_year=None, preferred_persona="adult")
            db.session.add(u)
            db.session.commit()
            uid = u.id
        from auth_utils import encode_token

        token = encode_token(uid, email, False)
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        response = self.client.post("/ask", data=json.dumps(self.valid_ask_request), headers=headers)
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data)
        self.assertEqual(data.get("code"), "birth_year_required")

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

    @patch("search_routes.find_shabads_by_first_letters")
    def test_api_search_first_letter_mode(self, mock_fl):
        mock_fl.return_value = []
        r = self.client.get("/api/search?q=stm&mode=first_letter")
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        self.assertIn("results", data)
        mock_fl.assert_called_once_with("stm", limit=50)

    @patch("search_routes.find_shabads_by_text_match")
    def test_api_search_text_mode_short_query_returns_empty(self, mock_txt):
        r = self.client.get("/api/search?q=ab&mode=text")
        self.assertEqual(r.status_code, 200)
        mock_txt.assert_not_called()
        data = json.loads(r.data)
        self.assertEqual(data["results"], [])

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
