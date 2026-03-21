import os
from typing import List, Optional

import google.generativeai as genai
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Load environment variables from root .env
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL', 'models/text-embedding-004')
LOCAL_EMBEDDING_MODEL = os.environ.get('LOCAL_EMBEDDING_MODEL', 'all-MiniLM-L6-v2')

_local_model = None


def _load_local_model() -> SentenceTransformer:
    global _local_model
    if _local_model is None:
        _local_model = SentenceTransformer(LOCAL_EMBEDDING_MODEL)
    return _local_model


def get_embedding(text: str, model: str = EMBEDDING_MODEL) -> Optional[List[float]]:
    """Return vector embedding for input text, or None if the call failed."""
    if not text or not text.strip():
        return None

    # Primary path: Gemini embeddings when API key is provided
    if GEMINI_API_KEY:
        try:
            result = genai.embed_content(
                model=model,
                content=text,
                task_type='retrieval_document'
            )
            embedding = result.get('embedding') if isinstance(result, dict) else None
            if embedding and isinstance(embedding, list):
                return [float(v) for v in embedding]

        except Exception as exc:
            print(f"[vector_utils] Gemini embedding failure: {exc}")

    # Fallback path: local sentence-transformers model
    try:
        local_model = _load_local_model()
        emb = local_model.encode(text, normalize_embeddings=True)
        return emb.tolist()

    except Exception as exc:
        print(f"[vector_utils] Local embedding failure: {exc}")
        return None
