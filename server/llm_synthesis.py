"""
Multi-provider chat synthesis for /ask. Admin-configured via LLMSettings (DB).
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional, Tuple, cast

import google.generativeai as genai

from gurbani_display import (
    ensure_guidance_grounded,
    guidance_grounding_ok,
    parmaan_canonical_section,
)
from models import LLMSettings, db
from prompts import (
    FALLBACK_RESPONSE,
    SYSTEM_PROMPT,
    _RELAXED_SAFETY,
    _safe_response_text,
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
        "models/gemini-2.5-flash-lite",
        "models/gemini-2.5-flash",
        "models/gemini-2.5-pro",
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
DEFAULT_MODEL = os.environ.get("DEFAULT_LLM_MODEL", "models/gemini-2.5-flash-lite").strip()


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


_GEMINI_DEPRECATED_MODELS: Dict[str, str] = {
    "models/gemini-2.0-flash-lite": "models/gemini-2.5-flash-lite",
    "models/gemini-flash-latest": "models/gemini-2.5-flash-lite",
    "models/gemini-2.0-flash": "models/gemini-2.5-flash",
    "models/gemini-1.5-flash": "models/gemini-2.5-flash-lite",
    "models/gemini-1.5-pro": "models/gemini-2.5-pro",
}


def resolve_gemini_model_id(model_id: str) -> str:
    """Normalize and migrate deprecated Gemini model IDs to current successors."""
    if not model_id:
        return "models/gemini-2.5-flash-lite"
    mid = model_id if model_id.startswith("models/") else f"models/{model_id}"
    replacement = _GEMINI_DEPRECATED_MODELS.get(mid)
    if replacement:
        logger.warning("Migrating deprecated Gemini model %s -> %s", mid, replacement)
        return replacement
    return mid


def _generate_gemini(model_id: str, prompt: str) -> Optional[str]:
    if not GEMINI_API_KEY:
        return None
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        mid = resolve_gemini_model_id(model_id)
        m = genai.GenerativeModel(mid, system_instruction=SYSTEM_PROMPT)
        config = genai.GenerationConfig(
            temperature=0.1,
            top_p=0.8,
            top_k=80,
            presence_penalty=0.0,
            frequency_penalty=0.0
        )
        response = m.generate_content(prompt, safety_settings=_RELAXED_SAFETY, generation_config=config)
        text = _safe_response_text(response)
        if not text.strip():
            return None
        return text
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
            temperature=0.1,
            top_p=0.8,
            presence_penalty=0.0,
            frequency_penalty=0.0,
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
            temperature=0.1,
            top_p=0.8,
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


def _shabads_as_dicts(shabads: Optional[list]) -> Optional[List[Dict[str, Any]]]:
    if not shabads:
        return None
    out: List[Dict[str, Any]] = []
    for s in shabads:
        if isinstance(s, dict):
            d = dict(cast(Dict[str, Any], s))
            d.pop("embedding", None)
            out.append(d)
        elif hasattr(s, "to_dict"):
            out.append(cast(Any, s).to_dict(include_embedding=False))
        else:
            out.append({})
    return out or None


def _generate_with_provider(prompt: str) -> Tuple[Optional[str], str, str]:
    """Run configured LLM on a single prompt. Returns (text, provider, model_id)."""
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
    return text, provider, model_id


def synthesize_chat_response(
    user_query: str,
    shabads: Optional[list] = None,
    persona: str = "adult",
    language: str = "en",
    message_history: Any = None,
    guidance_mode: str = "guidance",
    parmaan_discovery_type: str = "similar",
    user_memory_context: Any = None,
) -> Tuple[str, str, str]:
    """
    Build the RAG prompt and call the configured provider.
    Returns (response_text, provider_used, model_id_used).
    """
    gm = (guidance_mode or "guidance").strip().lower()
    shabad_dicts = _shabads_as_dicts(shabads)

    prompt = build_gemini_response_prompt(
        user_query,
        shabads,
        persona,
        language=language,
        message_history=message_history,
        guidance_mode=guidance_mode,
        parmaan_discovery_type=parmaan_discovery_type,
        grounding_retry=False,
        user_memory_context=user_memory_context,
    )
    text, provider, model_id = _generate_with_provider(prompt)

    if text and shabad_dicts and gm == "guidance" and not guidance_grounding_ok(text, shabad_dicts):
        retry_prompt = build_gemini_response_prompt(
            user_query,
            shabads,
            persona,
            language=language,
            message_history=message_history,
            guidance_mode=guidance_mode,
            parmaan_discovery_type=parmaan_discovery_type,
            grounding_retry=True,
            user_memory_context=user_memory_context,
        )
        text2, provider2, model_id2 = _generate_with_provider(retry_prompt)
        if text2 and guidance_grounding_ok(text2, shabad_dicts):
            text, provider, model_id = text2, provider2, model_id2

    if text and shabad_dicts and gm == "guidance":
        text = ensure_guidance_grounded(text, shabad_dicts)

    if text and shabad_dicts and gm == "parmaan":
        text = parmaan_canonical_section(shabad_dicts) + "\n\n---\n\n" + str(text).strip()

    if text and "[INSUFFICIENT_EVIDENCE]" in text:
        logger.warning(f"METRIC: fallback_triggered | reason: model_refusal | [INSUFFICIENT_EVIDENCE] detected")
        text = None

    if text is None or not str(text).strip():
        fb = synthesize_gemini_response(
            user_query,
            shabads,
            persona,
            language=language,
            message_history=message_history,
            guidance_mode=guidance_mode,
            parmaan_discovery_type=parmaan_discovery_type,
            user_memory_context=user_memory_context,
        )
        if fb is None or (isinstance(fb, str) and not fb.strip()):
            fb = FALLBACK_RESPONSE
        if shabad_dicts and gm == "parmaan" and isinstance(fb, str):
            fb = parmaan_canonical_section(shabad_dicts) + "\n\n---\n\n" + fb.strip()
        return (fb, "gemini-fallback", "synthesize_gemini_response")

    return (text, provider, model_id)
