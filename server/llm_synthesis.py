"""
Multi-provider chat synthesis for /ask. Admin-configured via LLMSettings (DB).
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import google.generativeai as genai

from models import LLMSettings, db
from prompts import (
    FALLBACK_RESPONSE,
    SYSTEM_PROMPT,
    build_gemini_response_prompt,
    synthesize_gemini_response,
)

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# Curated options for admin UI (model IDs are provider-native strings)
LLM_PROVIDER_MODELS: Dict[str, List[str]] = {
    "gemini": [
        "models/gemini-flash-latest",
        "models/gemini-2.0-flash",
        "models/gemini-2.5-flash",
        "models/gemini-1.5-flash",
        "models/gemini-1.5-pro",
    ],
    "openai": [
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-4-turbo",
        "o1-mini",
        "o1-preview",
    ],
    "anthropic": [
        "claude-sonnet-4-20250514",
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
        "claude-3-opus-20240229",
    ],
}

DEFAULT_PROVIDER = os.environ.get("DEFAULT_LLM_PROVIDER", "gemini").strip().lower()
DEFAULT_MODEL = os.environ.get("DEFAULT_LLM_MODEL", "models/gemini-flash-latest").strip()


def ensure_llm_settings_row() -> None:
    if LLMSettings.query.get(1) is not None:
        return
    prov = DEFAULT_PROVIDER if DEFAULT_PROVIDER in LLM_PROVIDER_MODELS else "gemini"
    mid = DEFAULT_MODEL
    if mid not in LLM_PROVIDER_MODELS.get(prov, []):
        mid = LLM_PROVIDER_MODELS[prov][0]
    row = LLMSettings(id=1, provider=prov, model_id=mid, guidance_shabad_count=3, parmaan_shabad_count=5)
    db.session.add(row)
    try:
        db.session.commit()
    except Exception as e:
        logger.warning("ensure_llm_settings_row: %s", e)
        db.session.rollback()


def get_llm_settings() -> Tuple[str, str]:
    ensure_llm_settings_row()
    row = LLMSettings.query.get(1)
    if not row:
        return ("gemini", LLM_PROVIDER_MODELS["gemini"][0])
    prov = (row.provider or "gemini").lower()
    if prov not in LLM_PROVIDER_MODELS:
        prov = "gemini"
    mid = row.model_id or LLM_PROVIDER_MODELS[prov][0]
    return (prov, mid)


def llm_options_for_admin() -> Dict[str, Any]:
    return {"providers": list(LLM_PROVIDER_MODELS.keys()), "models_by_provider": LLM_PROVIDER_MODELS}


def _normalize_gemini_model_id(model_id: str) -> str:
    if not model_id:
        return "models/gemini-flash-latest"
    if model_id.startswith("models/"):
        return model_id
    return f"models/{model_id}"


def _generate_gemini(model_id: str, prompt: str) -> Optional[str]:
    if not GEMINI_API_KEY:
        return None
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        mid = _normalize_gemini_model_id(model_id)
        m = genai.GenerativeModel(mid, system_instruction=SYSTEM_PROMPT)
        response = m.generate_content(prompt)
        if not response.text or not str(response.text).strip():
            return None
        return response.text
    except Exception as e:
        logger.error("Gemini generation failed: %s", e)
        return None


def _generate_openai(model_id: str, prompt: str) -> Optional[str]:
    if not OPENAI_API_KEY:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY)
        r = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=8192,
        )
        choice = r.choices[0].message.content if r.choices else None
        if not choice or not str(choice).strip():
            return None
        return choice
    except ImportError:
        logger.error("openai package not installed")
        return None
    except Exception as e:
        logger.error("OpenAI generation failed: %s", e)
        return None


def _generate_anthropic(model_id: str, prompt: str) -> Optional[str]:
    if not ANTHROPIC_API_KEY:
        return None
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model=model_id,
            max_tokens=8192,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        parts = []
        for b in msg.content:
            if hasattr(b, "text"):
                parts.append(b.text)
        text = "".join(parts).strip()
        return text or None
    except ImportError:
        logger.error("anthropic package not installed")
        return None
    except Exception as e:
        logger.error("Anthropic generation failed: %s", e)
        return None


def synthesize_chat_response(
    user_query: str,
    shabads: Optional[list] = None,
    persona: str = "adult",
    language: str = "en",
    message_history: Any = None,
    guidance_mode: str = "guidance",
) -> Tuple[str, str, str]:
    """
    Build the RAG prompt and call the configured provider.
    Returns (response_text, provider_used, model_id_used).
    """
    prompt = build_gemini_response_prompt(
        user_query,
        shabads,
        persona,
        language=language,
        message_history=message_history,
        guidance_mode=guidance_mode,
    )
    provider, model_id = get_llm_settings()

    text: Optional[str] = None
    if provider == "gemini":
        text = _generate_gemini(model_id, prompt)
    elif provider == "openai":
        text = _generate_openai(model_id, prompt)
    elif provider == "anthropic":
        anthropic_user_prompt = prompt
        if SYSTEM_PROMPT and prompt.startswith(SYSTEM_PROMPT):
            anthropic_user_prompt = prompt[len(SYSTEM_PROMPT) :].lstrip()
        text = _generate_anthropic(model_id, anthropic_user_prompt)
    else:
        provider = "gemini"
        model_id = LLM_PROVIDER_MODELS["gemini"][0]
        text = _generate_gemini(model_id, prompt)

    if text is None or not str(text).strip():
        fb = synthesize_gemini_response(
            user_query,
            shabads,
            persona,
            language=language,
            message_history=message_history,
            guidance_mode=guidance_mode,
        )
        if fb is None or (isinstance(fb, str) and not fb.strip()):
            fb = FALLBACK_RESPONSE
        return (fb, "gemini-fallback", "synthesize_gemini_response")

    return (text, provider, model_id)
