"""
End-to-end style tests against the Flask app (mocked LLM / retrieval).
Kept aligned with current /ask JSON shape and API routes.
"""

import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "server"))

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("DATABASE_URL_TEST", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-e2e")

from app import app  # noqa: E402


def _mock_shabad_row():
    m = MagicMock()
    m.id = 1
    m.shabad_id = "test-1"
    m.gurmukhi = "ਸਤਿਗੁਰੂ ਦੇ ਸਿਖ ਹੋਏ ਸਭ ਮਿਲ ਕੇ ਏਕ ਹੋਏ"
    m.romanization = "satigurū de sikh hoe sabh mil ke ek hoe"
    m.english_translation = "All Sikhs of the True Guru have become one united."
    m.source = "Guru Gobind Singh Ji"
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


class TestEndToEnd(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()
        self.app.config["TESTING"] = True

    def test_health_check_workflow(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "healthy")
        self.assertIn("timestamp", data)

    @patch("app.assess_query_clarity")
    @patch("app.get_embedding")
    @patch("app.search_similar_shabads")
    @patch("app.synthesize_chat_response")
    def test_complete_ask_workflow_success(self, mock_synthesize, mock_search, mock_emb, mock_assess):
        mock_assess.return_value = (False, "")
        mock_emb.return_value = [0.1] * 8
        mock_search.return_value = [_mock_shabad_row()]
        mock_synthesize.return_value = (
            "Based on Gurbani, unity among Sikhs brings peace. "
            "When we unite as one, there are no enemies.",
            "gemini",
            "models/gemini-flash-latest",
        )

        request_data = {"query": "How can I find peace when people around me are fighting?", "persona": "adult"}
        response = self.client.post("/ask", data=json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertIn("response", data)
        self.assertIn("shabad", data)
        self.assertIsNotNone(data["shabad"])
        self.assertEqual(data["persona"], "adult")
        self.assertFalse(data.get("is_clarification"))
        self.assertIn("sttm_link", data["shabad"])
        self.assertIn("unity", data["response"].lower())

    @patch("app.assess_query_clarity")
    @patch("app.get_embedding")
    @patch("app.search_similar_shabads")
    @patch("app.synthesize_chat_response")
    def test_ask_workflow_different_personas(self, mock_synthesize, mock_search, mock_emb, mock_assess):
        mock_assess.return_value = (False, "")
        mock_emb.return_value = [0.1] * 8
        mock_search.return_value = [_mock_shabad_row()]

        for persona, expected in [("child", "simple"), ("teen", "teen"), ("adult", "adult")]:
            mock_synthesize.return_value = (expected, "gemini", "models/gemini-flash-latest")
            response = self.client.post(
                "/ask",
                data=json.dumps({"query": "What is Sikhism?", "persona": persona}),
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data["persona"], persona)
            self.assertEqual(data["response"], expected)

    @patch("app.get_random_shabads")
    def test_random_shabads_workflow(self, mock_get_random):
        mock_get_random.return_value = [_mock_shabad_row()]
        response = self.client.get("/random-shabads?limit=5")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("shabads", data)
        self.assertEqual(len(data["shabads"]), 1)
        s0 = data["shabads"][0]
        self.assertIn("gurmukhi", s0)
        self.assertIn("english_translation", s0)
        self.assertIn("sttm_link", s0)

    def test_error_handling_workflow(self):
        response = self.client.post("/ask", data="invalid json", content_type="application/json")
        self.assertEqual(response.status_code, 400)

        response = self.client.post("/ask", data=json.dumps({"query": ""}), content_type="application/json")
        self.assertEqual(response.status_code, 400)

    @patch("app.assess_query_clarity")
    @patch("app.get_embedding")
    @patch("app.search_similar_shabads")
    def test_workflow_with_no_shabads_found(self, mock_search, mock_emb, mock_assess):
        mock_assess.return_value = (False, "")
        mock_emb.return_value = [0.1] * 8
        mock_search.return_value = []
        response = self.client.post(
            "/ask",
            data=json.dumps({"query": "Some very specific query with no matches", "persona": "adult"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn("error", data)

    @patch("app.assess_query_clarity")
    @patch("app.get_embedding")
    @patch("app.search_similar_shabads")
    @patch("app.synthesize_chat_response")
    def test_workflow_resilience_to_failures(self, mock_synthesize, mock_search, mock_emb, mock_assess):
        mock_assess.return_value = (False, "")
        mock_emb.return_value = [0.1] * 8
        mock_search.return_value = [_mock_shabad_row()]
        mock_synthesize.return_value = (None, "gemini", "models/gemini-flash-latest")
        response = self.client.post(
            "/ask", data=json.dumps({"query": "Test query", "persona": "adult"}), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("shabad", data)

    def test_cors_workflow(self):
        response = self.client.options("/ask")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Access-Control-Allow-Origin", response.headers)

    @patch("app.assess_query_clarity")
    @patch("app.get_embedding")
    @patch("app.search_similar_shabads")
    @patch("app.synthesize_chat_response")
    def test_workflow_data_integrity(self, mock_synthesize, mock_search, mock_emb, mock_assess):
        mock_assess.return_value = (False, "")
        mock_emb.return_value = [0.1] * 8
        mock_search.return_value = [_mock_shabad_row()]
        mock_synthesize.return_value = ("Test response", "gemini", "models/gemini-flash-latest")
        request_data = {"query": "ਦੁੱਖ ਦਾ ਕਾਰਨ ਕੀ ਹੈ?", "persona": "adult"}
        response = self.client.post("/ask", data=json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["persona"], request_data["persona"])
        sb = data["shabad"]
        self.assertIsInstance(sb.get("id"), int)
        self.assertIsInstance(sb.get("text"), str)

    def test_parmaans_categories_public(self):
        r = self.client.get("/api/parmaans/categories")
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        self.assertTrue(len(data.get("categories", [])) >= 1)


if __name__ == "__main__":
    unittest.main()
