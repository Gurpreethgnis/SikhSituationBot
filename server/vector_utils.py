import os
import time
import logging
from typing import List, Optional, Dict, Any

import google.generativeai as genai
from dotenv import load_dotenv
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

# Import Google API exceptions
try:
    from google.api_core import exceptions as google_exceptions
except ImportError:
    # Fallback if google.api_core is not available
    google_exceptions = None

# Load environment variables from root .env
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# Configure logging
logger = logging.getLogger(__name__)

# Placeholder for tests that patch this module
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL')

def get_best_embedding_model():
    """Detect the best available embedding model from the API."""
    global EMBEDDING_MODEL
    if EMBEDDING_MODEL:
        return EMBEDDING_MODEL
        
    try:
        available_models = [
            m.name for m in genai.list_models() 
            if 'embedContent' in m.supported_generation_methods
        ]
        if available_models:
            # Prefer text-embedding-004 if available, else pick the first one
            best_model = 'models/text-embedding-004'
            if best_model in available_models:
                EMBEDDING_MODEL = best_model
            else:
                EMBEDDING_MODEL = available_models[0]
            logger.info(f"Auto-selected Gemini embedding model: {EMBEDDING_MODEL}")
            return EMBEDDING_MODEL
    except Exception as e:
        logger.error(f"Failed to list Gemini models: {e}")
        
    # Fallback to a known default if listing fails
    EMBEDDING_MODEL = 'models/text-embedding-004'
    return EMBEDDING_MODEL

LOCAL_EMBEDDING_MODEL = os.environ.get('LOCAL_EMBEDDING_MODEL', 'all-MiniLM-L6-v2')

# Retry configuration
MAX_RETRIES = 3
BASE_DELAY = 1.0  # seconds
MAX_DELAY = 10.0  # seconds

_local_model = None


def load_local_model() -> Optional[Any]:
    """Load the local sentence-transformers model with caching."""
    global _local_model
    if SentenceTransformer is None:
        logger.error("sentence-transformers package is not installed. Local embeddings unavailable.")
        return None
        
    if _local_model is None:
        logger.info(f"Loading local embedding model: {LOCAL_EMBEDDING_MODEL}")
        _local_model = SentenceTransformer(LOCAL_EMBEDDING_MODEL)
    return _local_model


def calculate_backoff_delay(attempt: int) -> float:
    """Calculate exponential backoff delay with jitter."""
    delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
    # Add jitter to prevent thundering herd (ensure it stays above the base delay for tests)
    jitter = delay * 0.1 * (time.time() % 1)  # Positive jitter between 0% and +10%
    return delay + jitter


def get_embedding_gemini(text: str, model: Optional[str] = None, timeout: float = 30.0) -> Optional[List[float]]:
    """Get embeddings from Gemini API with retry logic and timeout."""
    if not GEMINI_API_KEY:
        return None

    # Resolve the best model dynamically
    actual_model = model or get_best_embedding_model()

    for attempt in range(MAX_RETRIES):
        try:
            logger.debug(f"Gemini embedding attempt {attempt + 1}/{MAX_RETRIES} for text length {len(text)} using {actual_model}")

            result = genai.embed_content(
                model=actual_model,
                content=text,
                task_type='retrieval_document'
            )

            embedding = result.get('embedding') if isinstance(result, dict) else None
            if embedding and isinstance(embedding, list) and len(embedding) > 0:
                logger.debug(f"Gemini embedding successful, vector length: {len(embedding)}")
                return [float(v) for v in embedding]
            else:
                logger.warning(f"Gemini returned invalid embedding format: {type(embedding)}")

        except Exception as e:
            # Handle different types of exceptions
            if google_exceptions and hasattr(google_exceptions, 'ResourceExhausted') and isinstance(e, google_exceptions.ResourceExhausted):
                # Rate limit exceeded
                if attempt < MAX_RETRIES - 1:
                    delay = calculate_backoff_delay(attempt)
                    logger.warning(f"Gemini rate limit exceeded, retrying in {delay:.1f}s: {e}")
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"Gemini rate limit exceeded, max retries reached: {e}")
            elif google_exceptions and hasattr(google_exceptions, 'ServiceUnavailable') and isinstance(e, google_exceptions.ServiceUnavailable):
                # Service temporarily unavailable
                if attempt < MAX_RETRIES - 1:
                    delay = calculate_backoff_delay(attempt)
                    logger.warning(f"Gemini service unavailable, retrying in {delay:.1f}s: {e}")
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"Gemini service unavailable, max retries reached: {e}")
            elif google_exceptions and hasattr(google_exceptions, 'InvalidArgument') and isinstance(e, google_exceptions.InvalidArgument):
                # Invalid input (e.g., text too long)
                logger.error(f"Gemini invalid argument: {e}")
                break  # Don't retry for invalid input
            else:
                # Generic exception
                logger.error(f"Gemini embedding failure (attempt {attempt + 1}): {e}")
                if attempt < MAX_RETRIES - 1:
                    delay = calculate_backoff_delay(attempt)
                    time.sleep(delay)
                else:
                    logger.error("Gemini embedding failed after all retries")

    return None


def get_embedding_local(text: str) -> Optional[List[float]]:
    """Get embeddings from local sentence-transformers model."""
    try:
        local_model = load_local_model()
        if local_model is None:
            return None
            
        logger.debug(f"Generating local embedding for text length {len(text)}")
        emb = local_model.encode(text, normalize_embeddings=True)
        embedding = emb.tolist()
        logger.debug(f"Local embedding successful, vector length: {len(embedding)}")
        return embedding

    except Exception as exc:
        logger.error(f"Local embedding failure: {exc}")
        return None


def get_embedding(text: str, model: Optional[str] = None, prefer_gemini: bool = True) -> Optional[List[float]]:
    """Return vector embedding for input text, or None if the call failed.

    Args:
        text: The text to embed
        model: The Gemini model to use (if using Gemini)
        prefer_gemini: Whether to try Gemini first (True) or local model first (False)

    Returns:
        List of floats representing the embedding vector, or None if failed
    """
    if not text or not text.strip():
        logger.warning("Empty text provided for embedding")
        return None

    # Clean and truncate text if too long (Gemini has limits)
    text = text.strip()
    if len(text) > 10000:  # Conservative limit
        logger.warning(f"Text too long ({len(text)} chars), truncating to 10000 chars")
        text = text[:10000]

    if prefer_gemini:
        # Try Gemini first, then fallback to local
        embedding = get_embedding_gemini(text, model)
        if embedding:
            return embedding

        logger.info("Gemini embedding failed, falling back to local model")
        return get_embedding_local(text)
    else:
        # Try local first, then fallback to Gemini
        embedding = get_embedding_local(text)
        if embedding:
            return embedding

        logger.info("Local embedding failed, falling back to Gemini")
        return get_embedding_gemini(text, model)
