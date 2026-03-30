import json
import logging
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import google.generativeai as genai
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from auth_utils import (
    decode_token,
    encode_token,
    get_bearer_token,
    hash_password,
    require_admin,
    require_auth,
    verify_password,
)
from llm_synthesis import (
    LLM_PROVIDER_MODELS,
    ensure_llm_settings_row,
    llm_options_for_admin,
    synthesize_chat_response,
)
from gurbani_content_quality import recompute_quality_for_stored_row
from models import Chat, LLMSettings, Message, Shabad, User, UserMemory, db
from prompts import (
    FALLBACK_RESPONSE,
    LANGUAGE_INSTRUCTIONS,
    _RELAXED_SAFETY,
    _safe_response_text,
    generate_chat_title,
    generate_opposite_theme_query,
    resolve_language,
)
from retrieval import (
    browse_shabads,
    find_similar_to_shabad,
    get_random_shabads,
    get_shabad_by_id,
    get_shabad_by_pk,
    search_similar_shabads,
)
from user_memory import (
    format_memory_context_for_prompt,
    load_active_memories_for_user,
    maybe_extract_and_save_after_guidance_turn,
)
from vector_utils import get_embedding
from feedback_github import (
    MAX_DESCRIPTION_LEN,
    MAX_RESPONSE_SNIPPET_LEN,
    create_feedback_issue,
    feedback_rate_limit_allows,
    parse_screenshot_base64,
    record_feedback_submission,
    sanitize_text,
    upload_feedback_screenshot,
)

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

query_assessment_model = None
ADMIN_EMAIL = (os.environ.get("ADMIN_EMAIL") or "").strip().lower()
INTERNAL_API_KEY = os.environ.get("FLASK_INTERNAL_API_KEY", "")

if not ADMIN_EMAIL:
    logger.warning(
        "ADMIN_EMAIL is not set; bootstrap admin (OAuth + register) will not grant is_admin. "
        "Set ADMIN_EMAIL on the Flask host (e.g. Railway) to your admin Gmail."
    )
if not INTERNAL_API_KEY:
    logger.warning(
        "FLASK_INTERNAL_API_KEY is not set; Next.js cannot call /api/auth/oauth-sync. "
        "Google sign-in will not receive a Flask JWT or admin flags from the API."
    )

# Parmaan: nearest-neighbor candidates shown before full retrieval (user must pick one).
PARMAAN_DISAMBIGUATION_TOP_N = 5
PARMAAN_ORIGINAL_QUERY_MAX_LEN = 4000

# Throttle global purge of stale chats (10-day retention) when listing chats.
_last_stale_chat_purge_utc: Optional[datetime] = None
CHAT_RETENTION_DAYS = 10
STALE_CHAT_PURGE_INTERVAL_SEC = 3600


def _maybe_purge_stale_chats_globally() -> None:
    """Delete chats not updated in CHAT_RETENTION_DAYS; throttled to avoid per-request heavy deletes."""
    global _last_stale_chat_purge_utc
    now = datetime.utcnow()
    if _last_stale_chat_purge_utc and (now - _last_stale_chat_purge_utc).total_seconds() < STALE_CHAT_PURGE_INTERVAL_SEC:
        return
    _last_stale_chat_purge_utc = now
    cutoff = now - timedelta(days=CHAT_RETENTION_DAYS)
    try:
        n = Chat.query.filter(Chat.updated_at < cutoff).delete(synchronize_session=False)
        if n:
            db.session.commit()
            logger.info("Purged %s chat(s) older than %s days (by updated_at)", n, CHAT_RETENTION_DAYS)
        else:
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.warning("Stale chat purge failed: %s", e)


def _parse_birth_year(data: dict) -> Optional[int]:
    raw = data.get("birth_year")
    if raw is None:
        return None
    try:
        y = int(raw)
    except (TypeError, ValueError):
        return None
    now_y = datetime.utcnow().year
    if y < 1900 or y > now_y:
        return None
    return y


def _persona_from_birth_year(birth_year: int) -> str:
    """Map age (from birth year) to child / teen / adult personas."""
    try:
        y = int(birth_year)
    except (TypeError, ValueError):
        return "adult"
    now_y = datetime.utcnow().year
    if y < 1900 or y > now_y:
        return "adult"
    age = now_y - y
    if age < 13:
        return "child"
    if age < 18:
        return "teen"
    return "adult"


def get_assessment_model():
    global query_assessment_model
    if query_assessment_model is None and GEMINI_API_KEY:
        query_assessment_model = genai.GenerativeModel("models/gemini-2.5-flash-lite")
    return query_assessment_model


def assess_query_clarity(
    query: str, persona: str = "adult", conversation_snippet: str = ""
) -> Tuple[bool, str]:
    model = get_assessment_model()
    if not model:
        return (False, "")

    prior = ""
    if conversation_snippet.strip():
        prior = f"\nRECENT CONVERSATION:\n{conversation_snippet}\n"

    assessment_prompt = f"""You are assessing whether a user's query has enough context to provide meaningful spiritual guidance from Sikh scripture (Guru Granth Sahib).
{prior}
LATEST USER MESSAGE: "{query}"
USER TYPE: {persona}

If there is prior conversation, treat follow-ups as clear if they build on that context (e.g. "tell me more" after a detailed share).

Analyze if this query:
1. Expresses a clear situation, problem, or question that can be addressed with scriptural wisdom
2. Has enough context to find relevant Gurbani verses
3. Or is too vague/ambiguous and would benefit from clarification

Respond with ONLY valid JSON (no markdown, no code blocks):
{{"needs_clarification": true/false, "reason": "brief explanation"}}"""

    try:
        response = model.generate_content(
            assessment_prompt,
            generation_config=genai.GenerationConfig(temperature=0.1, max_output_tokens=150),
            safety_settings=_RELAXED_SAFETY,
        )
        result_text = _safe_response_text(response).strip()
        if result_text.startswith("```"):
            result_text = result_text.split("\n", 1)[1] if "\n" in result_text else result_text
            result_text = result_text.rsplit("```", 1)[0] if "```" in result_text else result_text
        result_text = result_text.strip()
        result = json.loads(result_text)
        return (result.get("needs_clarification", False), result.get("reason", ""))
    except Exception as e:
        logger.warning("Query assessment failed, proceeding: %s", e)
        return (False, "")


app = Flask(__name__)
CORS(
    app,
    resources={
        r"/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Internal-Key"],
        }
    },
)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Internal-Key"
    return response


is_testing = os.environ.get("TESTING") == "true" or os.environ.get("FLASK_ENV") == "testing"

db_url = os.environ.get("DATABASE_URL")
if db_url and db_url.startswith("postgresql://") and not db_url.startswith("postgresql+psycopg2://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

if is_testing:
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL_TEST", "sqlite:///:memory:")
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url or "postgresql+psycopg2://localhost/sikhsituationbot"

if "sqlite" in app.config["SQLALCHEMY_DATABASE_URI"]:
    logger.info("Database configured for LOCAL SQLITE")
else:
    target = (
        app.config["SQLALCHEMY_DATABASE_URI"].split("@")[-1]
        if "@" in app.config["SQLALCHEMY_DATABASE_URI"]
        else "local/postgres"
    )
    logger.info("Database configured for POSTGRES: %s", target)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

if is_testing:
    with app.app_context():
        try:
            db.create_all()
            ensure_llm_settings_row()
        except Exception as e:
            logger.warning("testing create_all: %s", e)

if not is_testing:
    with app.app_context():
        try:
            db.create_all()
            # Migration: add shabad count columns if they don't exist
            from sqlalchemy import text, inspect
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('llm_settings')]
            if 'guidance_shabad_count' not in columns:
                db.session.execute(text("ALTER TABLE llm_settings ADD COLUMN guidance_shabad_count INTEGER DEFAULT 3"))
                db.session.commit()
                logger.info("Added guidance_shabad_count column to llm_settings")
            if 'parmaan_shabad_count' not in columns:
                db.session.execute(text("ALTER TABLE llm_settings ADD COLUMN parmaan_shabad_count INTEGER DEFAULT 5"))
                db.session.commit()
                logger.info("Added parmaan_shabad_count column to llm_settings")
            # Shabad content quality (Parmaan search / Raag header stubs)
            if "shabads" in inspector.get_table_names():
                sh_cols = [c["name"] for c in inspector.get_columns("shabads")]
                if "is_header_only" not in sh_cols:
                    db.session.execute(text("ALTER TABLE shabads ADD COLUMN is_header_only BOOLEAN"))
                    db.session.commit()
                    logger.info("Added is_header_only column to shabads")
                if "verse_count" not in sh_cols:
                    db.session.execute(text("ALTER TABLE shabads ADD COLUMN verse_count INTEGER"))
                    db.session.commit()
                    logger.info("Added verse_count column to shabads")
                if "content_length" not in sh_cols:
                    db.session.execute(text("ALTER TABLE shabads ADD COLUMN content_length INTEGER"))
                    db.session.commit()
                    logger.info("Added content_length column to shabads")
            ensure_llm_settings_row()
        except Exception as e:
            logger.warning("create_all warning: %s", e)


def _coerce_synthesis_result(result: Any) -> Tuple[str, Optional[str], Optional[str]]:
    """Normalize synthesize_chat_response output; support legacy tests that return a plain str."""
    if result is None:
        return FALLBACK_RESPONSE, None, None
    if isinstance(result, str):
        r = result.strip()
        return (r if r else FALLBACK_RESPONSE), "gemini", None
    if not isinstance(result, (list, tuple)):
        return FALLBACK_RESPONSE, None, None
    a = result[0]
    b = result[1] if len(result) > 1 else None
    c = result[2] if len(result) > 2 else None
    if a is None or (isinstance(a, str) and not str(a).strip()):
        return FALLBACK_RESPONSE, b, c
    return str(a), b, c


def _finalize_ask_response_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Never return HTTP 200 with an empty response string (the client shows 'no response')."""
    text = (payload.get("response") or "").strip()
    if text:
        return payload
    out = dict(payload)
    out["response"] = FALLBACK_RESPONSE
    return out


def _conversation_snippet_from_history(history: List[Dict[str, Any]], max_chars: int = 1200) -> str:
    if not history:
        return ""
    parts = []
    for turn in history[-8:]:
        role = turn.get("role", "")
        content = (turn.get("content") or "").strip()
        if not content:
            continue
        parts.append(f"{role.upper()}: {content}")
    text = "\n".join(parts)
    return text[:max_chars]


def _load_chat_history(chat: Chat) -> List[Dict[str, str]]:
    out = []
    for m in chat.messages.order_by(Message.created_at.asc()).all():
        out.append({"role": m.role, "content": m.content})
    return out


def _shabad_response_payload(row: Shabad) -> Dict[str, Any]:
    api = row.to_api_dict()
    return {
        "text": api["gurmukhi"],
        "title": api["english_translation"],
        "transliteration": api["romanization"],
        "sttm_link": api["sttm_link"],
        "shabad_id": api["shabad_id"],
        "id": api["id"],
    }


def _disambiguation_candidate_dict(row: Shabad) -> Dict[str, Any]:
    """Compact shabad row for Parmaan text-match disambiguation UI."""
    ang = None
    if row.source:
        m = re.search(r"Ang\s*(\d+)", str(row.source), re.I)
        if m:
            ang = int(m.group(1))
    return {
        "shabad_id": row.shabad_id,
        "gurmukhi": row.gurmukhi or "",
        "english_translation": row.english_translation or "",
        "romanization": row.romanization or "",
        "source": row.source or "",
        "ang": ang,
        "sttm_link": Shabad.sttm_url_for(row.shabad_id),
    }


# --- Health ---
@app.route("/health", methods=["GET"])
@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify(
        {
            "status": "healthy",
            "message": "SikhSituationBot backend is running!",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    ), 200


@app.route("/api/stats/knowledge", methods=["GET"])
def knowledge_stats():
    """Public count of shabads in the knowledge base (for UI / monitoring ingestion)."""
    try:
        n = Shabad.query.count()
        return jsonify({"shabad_count": n}), 200
    except Exception as e:
        logger.exception("knowledge_stats failed: %s", e)
        return jsonify({"error": "unavailable"}), 503


# --- Auth ---
@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    name = (data.get("name") or "").strip() or None
    if not email or not password or len(password) < 8:
        return jsonify({"error": "Valid email and password (8+ chars) required"}), 400

    existing = User.query.filter_by(email=email).first()
    if existing:
        if existing.password_hash:
            return jsonify({"error": "Email already registered"}), 409
        # Same email as Google (or other OAuth) sign-in: add a password to the existing account.
        try:
            existing.password_hash = hash_password(password)
            if name:
                existing.name = name
            by = _parse_birth_year(data)
            if by is not None and existing.birth_year is None:
                existing.birth_year = by
                existing.preferred_persona = _persona_from_birth_year(by)
                existing.persona_source = "profile"
            existing.last_login = datetime.utcnow()
            db.session.commit()
            token = encode_token(existing.id, existing.email, existing.is_admin)
            return jsonify({"token": token, "user": existing.to_dict()}), 201
        except SQLAlchemyError:
            db.session.rollback()
            logger.exception("register: failed to add password for oauth-only user %s", email)
            return jsonify({"error": "Could not complete registration. Please try again."}), 500

    is_admin = bool(ADMIN_EMAIL and email == ADMIN_EMAIL)
    by = _parse_birth_year(data)
    ps = "default"
    pref_p = "adult"
    if by is not None:
        ps = "profile"
        pref_p = _persona_from_birth_year(by)
    user = User(
        email=email,
        name=name,
        password_hash=hash_password(password),
        is_admin=is_admin,
        persona_source=ps,
        birth_year=by,
        preferred_persona=pref_p,
    )
    try:
        db.session.add(user)
        db.session.commit()
        token = encode_token(user.id, user.email, user.is_admin)
        return jsonify({"token": token, "user": user.to_dict()}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Email already registered"}), 409
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("register failed for email %s", email)
        return jsonify(
            {
                "error": "Registration failed. If you already signed in with Google using this email, "
                "use Google sign-in or choose a different email.",
            }
        ), 500


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    user = User.query.filter_by(email=email).first()
    if not user or not user.password_hash or not verify_password(password, user.password_hash):
        return jsonify({"error": "Invalid credentials"}), 401
    if not user.is_active:
        return jsonify({"error": "Account inactive"}), 403
    user.last_login = datetime.utcnow()
    db.session.commit()
    token = encode_token(user.id, user.email, user.is_admin)
    return jsonify({"token": token, "user": user.to_dict()}), 200


@app.route("/api/auth/oauth-sync", methods=["POST"])
def oauth_sync():
    """Called from Next.js server with X-Internal-Key to upsert OAuth users."""
    if not INTERNAL_API_KEY or request.headers.get("X-Internal-Key") != INTERNAL_API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    name = (data.get("name") or "").strip() or None
    avatar_url = (data.get("avatar_url") or data.get("image") or "").strip() or None
    by_raw = data.get("birth_year")
    iby: Optional[int] = None
    if by_raw is not None:
        try:
            iby = int(by_raw)
        except (TypeError, ValueError):
            iby = None
    now_y = datetime.utcnow().year
    if not email:
        return jsonify({"error": "email required"}), 400
    user = User.query.filter_by(email=email).first()
    is_admin = bool(ADMIN_EMAIL and email == ADMIN_EMAIL)
    if not user:
        user = User(
            email=email,
            name=name,
            avatar_url=avatar_url,
            is_admin=is_admin,
        )
        db.session.add(user)
    else:
        if name:
            user.name = name
        if avatar_url:
            user.avatar_url = avatar_url
        # Always upgrade bootstrap admin email (fixes users created before ADMIN_EMAIL was set).
        if ADMIN_EMAIL and email == ADMIN_EMAIL:
            user.is_admin = True
    if iby is not None and 1900 <= iby <= now_y:
        # Do not overwrite birth year the user set in-app (Settings / onboarding).
        if (user.persona_source or "default") != "profile":
            user.birth_year = iby
            user.preferred_persona = _persona_from_birth_year(iby)
            user.persona_source = "google"
    user.last_login = datetime.utcnow()
    db.session.commit()
    token = encode_token(user.id, user.email, user.is_admin)
    return jsonify({"token": token, "user": user.to_dict()}), 200


@app.route("/api/auth/me", methods=["GET"])
@require_auth
def me():
    return jsonify({"user": request.user.to_dict()}), 200


@app.route("/api/memory", methods=["GET"])
@require_auth
def list_user_memories():
    rows = (
        UserMemory.query.filter_by(user_id=request.user_id, is_deleted=False)
        .order_by(desc(UserMemory.created_at))
        .limit(50)
        .all()
    )
    return jsonify({"memories": [m.to_dict() for m in rows]}), 200


@app.route("/api/memory/<int:memory_id>", methods=["DELETE"])
@require_auth
def delete_user_memory(memory_id: int):
    row = UserMemory.query.filter_by(id=memory_id, user_id=request.user_id).first()
    if not row:
        return jsonify({"error": "Not found"}), 404
    row.is_deleted = True
    db.session.commit()
    return jsonify({"ok": True}), 200


@app.route("/api/memory/<int:memory_id>/pin", methods=["POST"])
@require_auth
def pin_user_memory(memory_id: int):
    row = UserMemory.query.filter_by(id=memory_id, user_id=request.user_id).first()
    if not row:
        return jsonify({"error": "Not found"}), 404
    row.is_pinned = not bool(row.is_pinned)
    db.session.commit()
    return jsonify({"pinned": row.is_pinned}), 200


@app.route("/api/memory/clear", methods=["POST"])
@require_auth
def clear_user_memories():
    UserMemory.query.filter_by(user_id=request.user_id).update({"is_deleted": True})
    db.session.commit()
    return jsonify({"ok": True}), 200


@app.route("/api/auth/me", methods=["PATCH"])
@require_auth
def patch_me():
    data = request.get_json(silent=True) or {}
    u = request.user
    if "preferred_language" in data:
        u.preferred_language = resolve_language(data.get("preferred_language"))
    if "birth_year" in data:
        by = _parse_birth_year(data)
        if by is None:
            return jsonify({"error": "Invalid birth_year (use a year between 1900 and the current year)"}), 400
        u.birth_year = by
        u.preferred_persona = _persona_from_birth_year(by)
        u.persona_source = "profile"
    if "preferred_theme" in data and data.get("preferred_theme"):
        u.preferred_theme = str(data["preferred_theme"])[:20]
    if "name" in data and data.get("name"):
        u.name = str(data["name"])[:100]
    if "memory_enabled" in data:
        u.memory_enabled = bool(data["memory_enabled"])
    if "memory_retention_days" in data:
        try:
            rd = int(data["memory_retention_days"])
            if 1 <= rd <= 3650:
                u.memory_retention_days = rd
        except (TypeError, ValueError):
            pass
    db.session.commit()
    return jsonify({"user": u.to_dict()}), 200


# --- Chats ---
@app.route("/api/chats", methods=["GET"])
@require_auth
def list_chats():
    _maybe_purge_stale_chats_globally()
    chats = (
        Chat.query.filter_by(user_id=request.user_id)
        .order_by(desc(Chat.updated_at), desc(Chat.created_at))
        .limit(100)
        .all()
    )
    return jsonify({"chats": [c.to_dict() for c in chats]}), 200


@app.route("/api/chats", methods=["POST"])
@require_auth
def create_chat():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "New chat").strip()[:200]
    chat = Chat(user_id=request.user_id, title=title)
    db.session.add(chat)
    db.session.commit()
    return jsonify({"chat": chat.to_dict()}), 201


@app.route("/api/chats/<int:chat_id>", methods=["GET"])
@require_auth
def get_chat(chat_id: int):
    chat = Chat.query.filter_by(id=chat_id, user_id=request.user_id).first()
    if not chat:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"chat": chat.to_dict(include_messages=True)}), 200


@app.route("/api/chats/<int:chat_id>", methods=["DELETE"])
@require_auth
def delete_chat(chat_id: int):
    chat = Chat.query.filter_by(id=chat_id, user_id=request.user_id).first()
    if not chat:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(chat)
    db.session.commit()
    return jsonify({"ok": True}), 200


@app.route("/api/chats/<int:chat_id>/share", methods=["POST"])
@require_auth
def share_chat(chat_id: int):
    chat = Chat.query.filter_by(id=chat_id, user_id=request.user_id).first()
    if not chat:
        return jsonify({"error": "Not found"}), 404
    if not chat.share_id:
        chat.share_id = str(uuid.uuid4())
    chat.is_shared = True
    db.session.commit()
    base = os.environ.get("PUBLIC_APP_URL", "http://localhost:3000")
    url = f"{base.rstrip('/')}/shared/{chat.share_id}"
    return jsonify({"share_id": chat.share_id, "url": url}), 200


@app.route("/api/shared/<share_id>", methods=["GET"])
def get_shared(share_id: str):
    chat = Chat.query.filter_by(share_id=share_id, is_shared=True).first()
    if not chat:
        return jsonify({"error": "Not found"}), 404
    return jsonify(
        {
            "chat": {
                "title": chat.title,
                "messages": [m.to_dict() for m in chat.messages.order_by(Message.created_at.asc()).all()],
            }
        }
    ), 200


@app.route("/api/feedback", methods=["POST"])
@require_auth
def submit_feedback():
    """
    Create a GitHub issue from authenticated user feedback (requires GITHUB_TOKEN on server).
    """
    gh_token = (os.environ.get("GITHUB_TOKEN") or "").strip()
    if not gh_token:
        return jsonify({"error": "Feedback is not configured on this server."}), 503

    repo_full = (os.environ.get("GITHUB_FEEDBACK_REPO") or "Gurpreethgnis/SikhSituationBot").strip()
    if "/" not in repo_full:
        logger.error("GITHUB_FEEDBACK_REPO must be owner/repo")
        return jsonify({"error": "Server feedback configuration error."}), 500
    owner, repo = repo_full.split("/", 1)
    branch = (os.environ.get("GITHUB_FEEDBACK_BRANCH") or "main").strip() or "main"

    allowed, rate_err = feedback_rate_limit_allows(request.user_id)
    if not allowed:
        return jsonify({"error": rate_err}), 429

    data = request.get_json(silent=True) or {}
    fb_type = (data.get("type") or "other").strip().lower()
    description = sanitize_text(data.get("description") or "", MAX_DESCRIPTION_LEN)
    response_content = sanitize_text(data.get("response_content") or "", MAX_RESPONSE_SNIPPET_LEN)
    if not description:
        return jsonify({"error": "Description is required."}), 400

    chat_id_raw = data.get("chat_id")
    chat_id: Optional[int] = None
    if chat_id_raw is not None and chat_id_raw != "":
        try:
            chat_id = int(chat_id_raw)
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid chat_id."}), 400
        chat = Chat.query.filter_by(id=chat_id, user_id=request.user_id).first()
        if not chat:
            return jsonify({"error": "Chat not found."}), 404

    screenshot_url: Optional[str] = None
    screenshot_b64 = data.get("screenshot_base64")
    if screenshot_b64:
        try:
            parsed = parse_screenshot_base64(screenshot_b64)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        if parsed:
            raw_bytes, ext = parsed
            screenshot_url = upload_feedback_screenshot(gh_token, owner, repo, branch, raw_bytes, ext)
            if not screenshot_url:
                return jsonify(
                    {"error": "Could not upload screenshot. Try again without an image or later."}
                ), 502

    user = request.user
    issue_url, gh_err = create_feedback_issue(
        token=gh_token,
        owner=owner,
        repo=repo,
        branch=branch,
        feedback_type=fb_type,
        description=description,
        response_snippet=response_content,
        reporter_user_id=user.id,
        reporter_email=user.email or "",
        screenshot_url=screenshot_url,
        chat_id=chat_id,
    )
    if not issue_url:
        return jsonify({"error": gh_err or "Failed to create GitHub issue"}), 502

    record_feedback_submission(request.user_id)
    return jsonify({"ok": True, "issue_url": issue_url}), 201


# --- Parmaans / discovery ---
PARMAAN_CATEGORIES = [
    {"id": "peace", "label": "Peace & calm", "hints": ["peace", "calm", "anxiety", "stress"]},
    {"id": "grief", "label": "Grief & loss", "hints": ["loss", "death", "grief", "mourning"]},
    {"id": "anger", "label": "Anger & forgiveness", "hints": ["anger", "forgive", "resentment"]},
    {"id": "faith", "label": "Faith & doubt", "hints": ["faith", "doubt", "trust", "waheguru"]},
    {"id": "love", "label": "Love & compassion", "hints": ["love", "compassion", "kindness"]},
    {"id": "humility", "label": "Humility & ego", "hints": ["ego", "humility", "pride", "naam"]},
]


@app.route("/api/parmaans/categories", methods=["GET"])
def parmaans_categories():
    return jsonify({"categories": PARMAAN_CATEGORIES}), 200


@app.route("/api/parmaans/search", methods=["POST"])
def parmaans_search():
    data = request.get_json(silent=True) or {}
    q = (data.get("query") or "").strip()
    limit = min(int(data.get("limit") or 10), 30)
    persona = data.get("persona")
    if not q:
        return jsonify({"error": "query required"}), 400
    vec = get_embedding(q)
    if not vec:
        return jsonify({"error": "embedding failed"}), 500
    rows = search_similar_shabads(
        vec, limit=limit, persona=persona, exclude_parmaan_low_quality=True
    )
    if not rows:
        rows = search_similar_shabads(vec, limit=limit, exclude_parmaan_low_quality=True)
    return jsonify({"shabads": [r.to_api_dict() for r in rows]}), 200


@app.route("/api/parmaans/browse", methods=["GET"])
def parmaans_browse():
    page = max(1, request.args.get("page", 1, type=int))
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    source = request.args.get("source")
    search = request.args.get("q")
    persona = request.args.get("persona")
    items, total = browse_shabads(page=page, per_page=per_page, source=source, search=search, persona=persona)
    return jsonify(
        {
            "shabads": [s.to_api_dict() for s in items],
            "page": page,
            "per_page": per_page,
            "total": total,
        }
    ), 200


@app.route("/api/parmaans/by-key/<path:key>", methods=["GET"])
def parmaans_by_key(key: str):
    s = get_shabad_by_id(key)
    if not s:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"shabad": s.to_api_dict()}), 200


@app.route("/api/parmaans/<int:pk>/similar", methods=["GET"])
def parmaans_similar(pk: int):
    s = get_shabad_by_pk(pk)
    if not s:
        return jsonify({"error": "Not found"}), 404
    limit = min(request.args.get("limit", 8, type=int), 20)
    rows = find_similar_to_shabad(s, limit=limit, exclude_parmaan_low_quality=True)
    return jsonify({"shabads": [r.to_api_dict() for r in rows]}), 200


@app.route("/api/parmaans/<int:pk>/opposite", methods=["GET"])
def parmaans_opposite(pk: int):
    s = get_shabad_by_pk(pk)
    if not s:
        return jsonify({"error": "Not found"}), 404
    summary = f"{s.english_translation}\n{s.gurmukhi[:200]}"
    phrase = generate_opposite_theme_query(summary)
    vec = get_embedding(phrase)
    if not vec:
        return jsonify({"error": "embedding failed"}), 500
    limit = min(request.args.get("limit", 8, type=int), 20)
    rows = search_similar_shabads(vec, limit=limit + 2, exclude_parmaan_low_quality=True)
    rows = [r for r in rows if r.id != s.id][:limit]
    return jsonify({"query": phrase, "shabads": [r.to_api_dict() for r in rows]}), 200


# --- Admin ---
@app.route("/api/admin/users", methods=["GET"])
@require_admin
def admin_users():
    page = max(1, request.args.get("page", 1, type=int))
    per_page = min(request.args.get("per_page", 30, type=int), 100)
    q = User.query.order_by(User.created_at.desc())
    total = q.count()
    users = q.offset((page - 1) * per_page).limit(per_page).all()
    return jsonify(
        {
            "users": [u.to_dict(include_sensitive=True) for u in users],
            "page": page,
            "per_page": per_page,
            "total": total,
        }
    ), 200


@app.route("/api/admin/users/<int:user_id>", methods=["PATCH"])
@require_admin
def admin_patch_user(user_id: int):
    u = db.session.get(User, user_id)
    if not u:
        return jsonify({"error": "Not found"}), 404
    data = request.get_json(silent=True) or {}
    if "is_admin" in data:
        u.is_admin = bool(data["is_admin"])
    if "is_active" in data:
        u.is_active = bool(data["is_active"])
    db.session.commit()
    return jsonify({"user": u.to_dict(include_sensitive=True)}), 200


@app.route("/api/admin/users/<int:user_id>", methods=["DELETE"])
@require_admin
def admin_delete_user(user_id: int):
    if user_id == request.user_id:
        return jsonify({"error": "Cannot delete self"}), 400
    u = db.session.get(User, user_id)
    if not u:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(u)
    db.session.commit()
    return jsonify({"ok": True}), 200


@app.route("/api/admin/shabads", methods=["GET"])
@require_admin
def admin_list_shabads():
    page = max(1, request.args.get("page", 1, type=int))
    per_page = min(request.args.get("per_page", 30, type=int), 100)
    search = request.args.get("q")
    items, total = browse_shabads(page=page, per_page=per_page, search=search)
    return jsonify(
        {
            "shabads": [s.to_api_dict() for s in items],
            "page": page,
            "per_page": per_page,
            "total": total,
        }
    ), 200


@app.route("/api/admin/shabads", methods=["POST"])
@require_admin
def admin_create_shabad():
    data = request.get_json(silent=True) or {}
    sid = (data.get("shabad_id") or "").strip()
    gurmukhi = (data.get("gurmukhi") or "").strip()
    eng = (data.get("english_translation") or "").strip()
    if not sid or not gurmukhi or not eng:
        return jsonify({"error": "shabad_id, gurmukhi, english_translation required"}), 400
    if Shabad.query.filter_by(shabad_id=sid).first():
        return jsonify({"error": "shabad_id exists"}), 409
    text_for_emb = f"{gurmukhi}\n{eng}\n{(data.get('romanization') or '')}"
    emb = get_embedding(text_for_emb)
    quality = recompute_quality_for_stored_row(
        gurmukhi,
        eng,
        data.get("verse_count") if isinstance(data.get("verse_count"), int) else None,
    )
    s = Shabad(
        shabad_id=sid,
        gurmukhi=gurmukhi,
        english_translation=eng,
        romanization=(data.get("romanization") or "").strip() or None,
        source=(data.get("source") or "").strip() or None,
        recommended_persona=(data.get("recommended_persona") or "any")[:20],
        context_tags=data.get("context_tags") if isinstance(data.get("context_tags"), list) else None,
        is_header_only=quality["is_header_only"],
        verse_count=quality["verse_count"],
        content_length=quality["content_length"],
        embedding=emb,
    )
    db.session.add(s)
    db.session.commit()
    return jsonify({"shabad": s.to_api_dict()}), 201


@app.route("/api/admin/shabads/<int:pk>", methods=["PUT"])
@require_admin
def admin_put_shabad(pk: int):
    s = get_shabad_by_pk(pk)
    if not s:
        return jsonify({"error": "Not found"}), 404
    data = request.get_json(silent=True) or {}
    if "gurmukhi" in data:
        s.gurmukhi = data["gurmukhi"]
    if "english_translation" in data:
        s.english_translation = data["english_translation"]
    if "romanization" in data:
        s.romanization = data["romanization"]
    if "source" in data:
        s.source = data["source"]
    if "recommended_persona" in data:
        s.recommended_persona = str(data["recommended_persona"])[:20]
    if "context_tags" in data and isinstance(data["context_tags"], list):
        s.context_tags = data["context_tags"]
    text_for_emb = f"{s.gurmukhi}\n{s.english_translation}\n{s.romanization or ''}"
    s.embedding = get_embedding(text_for_emb)
    quality = recompute_quality_for_stored_row(s.gurmukhi, s.english_translation, s.verse_count)
    s.is_header_only = quality["is_header_only"]
    s.verse_count = quality["verse_count"]
    s.content_length = quality["content_length"]
    db.session.commit()
    return jsonify({"shabad": s.to_api_dict()}), 200


@app.route("/api/admin/shabads/<int:pk>", methods=["DELETE"])
@require_admin
def admin_delete_shabad(pk: int):
    s = get_shabad_by_pk(pk)
    if not s:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(s)
    db.session.commit()
    return jsonify({"ok": True}), 200


@app.route("/api/admin/analytics", methods=["GET"])
@require_admin
def admin_analytics():
    nu = User.query.count()
    nc = Chat.query.count()
    nm = Message.query.count()
    ns = Shabad.query.count()
    return jsonify(
        {
            "users": nu,
            "chats": nc,
            "messages": nm,
            "shabads": ns,
            "languages_supported": list(LANGUAGE_INSTRUCTIONS.keys()),
        }
    ), 200


@app.route("/api/admin/llm-settings", methods=["GET"])
@require_admin
def admin_get_llm_settings():
    ensure_llm_settings_row()
    row = LLMSettings.query.get(1)
    opts = llm_options_for_admin()
    return jsonify(
        {
            "provider": row.provider if row else "gemini",
            "model_id": row.model_id if row else LLM_PROVIDER_MODELS["gemini"][0],
            "guidance_shabad_count": getattr(row, 'guidance_shabad_count', 3) if row else 3,
            "parmaan_shabad_count": getattr(row, 'parmaan_shabad_count', 5) if row else 5,
            "options": opts,
        }
    ), 200


@app.route("/api/admin/llm-settings", methods=["PATCH"])
@require_admin
def admin_patch_llm_settings():
    data = request.get_json(silent=True) or {}
    ensure_llm_settings_row()
    row = LLMSettings.query.get(1)

    # Handle provider/model updates
    prov = data.get("provider")
    mid = data.get("model_id")
    if prov is not None or mid is not None:
        prov = (prov or row.provider or "").strip().lower()
        mid = (mid or row.model_id or "").strip()
        if prov not in LLM_PROVIDER_MODELS:
            return jsonify({"error": f"Invalid provider. Use one of: {list(LLM_PROVIDER_MODELS)}"}), 400
        allowed = LLM_PROVIDER_MODELS[prov]
        if mid not in allowed:
            return jsonify({"error": f"model_id must be one of {allowed} for provider {prov}"}), 400
        if not row:
            row = LLMSettings(id=1, provider=prov, model_id=mid)
            db.session.add(row)
        else:
            row.provider = prov
            row.model_id = mid

    # Handle shabad count updates
    guidance_count = data.get("guidance_shabad_count")
    parmaan_count = data.get("parmaan_shabad_count")
    if guidance_count is not None:
        try:
            guidance_count = int(guidance_count)
            if 1 <= guidance_count <= 10:
                row.guidance_shabad_count = guidance_count
            else:
                return jsonify({"error": "guidance_shabad_count must be between 1 and 10"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "guidance_shabad_count must be an integer"}), 400
    if parmaan_count is not None:
        try:
            parmaan_count = int(parmaan_count)
            if 1 <= parmaan_count <= 15:
                row.parmaan_shabad_count = parmaan_count
            else:
                return jsonify({"error": "parmaan_shabad_count must be between 1 and 15"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "parmaan_shabad_count must be an integer"}), 400

    db.session.commit()
    return jsonify({
        "provider": row.provider,
        "model_id": row.model_id,
        "guidance_shabad_count": getattr(row, 'guidance_shabad_count', 3),
        "parmaan_shabad_count": getattr(row, 'parmaan_shabad_count', 5),
    }), 200


@app.route("/api/admin/interactions", methods=["GET"])
@require_admin
def admin_interactions():
    page = max(request.args.get("page", default=1, type=int), 1)
    per_page = min(max(request.args.get("per_page", default=50, type=int), 1), 200)
    full = request.args.get("full", default="", type=str).lower() in ("1", "true", "yes")
    user_email = (request.args.get("user_email") or "").strip().lower()

    q = (
        Message.query.join(Chat, Message.chat_id == Chat.id)
        .join(User, Chat.user_id == User.id)
        .order_by(desc(Message.created_at))
    )
    if user_email:
        q = q.filter(User.email.ilike(f"%{user_email}%"))

    total = q.count()
    rows = q.offset((page - 1) * per_page).limit(per_page).all()

    def row_to_dict(m: Message) -> Dict[str, Any]:
        chat = m.chat
        usr = chat.user if chat else None
        content = (
            m.content
            if full
            else ((m.content[:500] + "…") if len(m.content or "") > 500 else m.content)
        )
        shabad_summary = None
        if m.shabad:
            shabad_summary = {
                "id": m.shabad.id,
                "shabad_id": m.shabad.shabad_id,
                "english_translation": (m.shabad.english_translation or "")[:200],
            }
        return {
            "message_id": m.id,
            "role": m.role,
            "content": content,
            "content_truncated": (not full) and len(m.content or "") > 500,
            "persona": m.persona,
            "language": m.language,
            "llm_provider": m.llm_provider,
            "llm_model": m.llm_model,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "chat_id": m.chat_id,
            "chat_title": chat.title if chat else None,
            "user_email": usr.email if usr else None,
            "user_id": usr.id if usr else None,
            "shabad": shabad_summary,
            "shabad_row_id": m.shabad_row_id,
        }

    return jsonify(
        {
            "total": total,
            "page": page,
            "per_page": per_page,
            "items": [row_to_dict(m) for m in rows],
        }
    ), 200


def _normalize_parmaan_discovery(raw: Optional[str]) -> str:
    """Map client/UI values to prompts retrieval types: similar | topic | dissimilar."""
    s = (raw or "similar").strip().lower()
    if s in ("dissimilar", "opposite", "contrasts", "contrast"):
        return "dissimilar"
    if s == "topic":
        return "topic"
    return "similar"


def _retrieve_parmaan_shabads_for_chat(
    query_vector: List[float],
    discovery_type: str,
    limit: int,
    persona: str,
    anchor_shabad: Optional[Shabad] = None,
) -> List[Shabad]:
    """
    Parmaan chat retrieval: similar/topic use semantic search on the user query embedding,
    or neighbors of an explicit anchor shabad when the user chose one after disambiguation;
    dissimilar finds the closest verse to the query (or uses the explicit anchor), then
    searches using an opposite-theme phrase.
    """
    limit = max(1, min(int(limit), 15))
    if anchor_shabad is not None and anchor_shabad.embedding is None:
        return []

    if discovery_type == "dissimilar":
        if anchor_shabad is not None:
            anchor = anchor_shabad
        else:
            anchors = search_similar_shabads(
                query_embedding=query_vector,
                limit=1,
                persona=persona,
                exclude_parmaan_low_quality=True,
            )
            if not anchors:
                anchors = search_similar_shabads(
                    query_embedding=query_vector, limit=1, exclude_parmaan_low_quality=True
                )
            if not anchors:
                return []
            anchor = anchors[0]
        summary = f"{anchor.english_translation or ''}\n{(anchor.gurmukhi or '')[:200]}"
        phrase = generate_opposite_theme_query(summary)
        opp_vec = get_embedding(phrase)
        if not opp_vec:
            return []
        rows = search_similar_shabads(
            query_embedding=opp_vec,
            limit=limit + 2,
            persona=persona,
            exclude_parmaan_low_quality=True,
        )
        if not rows:
            rows = search_similar_shabads(
                query_embedding=opp_vec, limit=limit + 2, exclude_parmaan_low_quality=True
            )
        return [r for r in rows if r.id != anchor.id][:limit]

    if anchor_shabad is not None:
        return find_similar_to_shabad(
            anchor_shabad,
            limit=limit,
            exclude_parmaan_low_quality=True,
            persona=persona,
        )

    rows = search_similar_shabads(
        query_embedding=query_vector,
        limit=limit,
        persona=persona,
        exclude_parmaan_low_quality=True,
    )
    if not rows:
        rows = search_similar_shabads(
            query_embedding=query_vector, limit=limit, exclude_parmaan_low_quality=True
        )
    return rows


# --- Main ask ---
@app.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.get_json(silent=True)
        if data is None:
            return jsonify({"error": "Request must be JSON"}), 400
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400

    query_text = (data.get("query") or "").strip()
    parmaan_original_query = (data.get("parmaan_original_query") or "").strip()
    if len(parmaan_original_query) > PARMAAN_ORIGINAL_QUERY_MAX_LEN:
        parmaan_original_query = parmaan_original_query[:PARMAAN_ORIGINAL_QUERY_MAX_LEN]
    language = resolve_language(data.get("language"))
    chat_id = data.get("chat_id")
    client_history = data.get("message_history") or []
    gm_raw = (data.get("guidance_mode") or data.get("response_mode") or "guidance").strip().lower()
    guidance_mode = gm_raw if gm_raw in ("guidance", "parmaan") else "guidance"

    if not query_text:
        return jsonify({"error": "No query provided"}), 400

    valid_personas = ["child", "teen", "adult"]

    token = get_bearer_token()
    if not token:
        return jsonify({"error": "Authentication required"}), 401
    tok_payload = decode_token(token)
    if not tok_payload or not tok_payload.get("sub"):
        return jsonify({"error": "Invalid or expired token"}), 401
    user = User.query.get(int(tok_payload["sub"]))
    if not user or not user.is_active:
        return jsonify({"error": "User not found or inactive"}), 401
    request.user_id = user.id
    request.user = user

    if user.birth_year is None:
        return (
            jsonify(
                {
                    "error": "Please add your year of birth in Settings or onboarding to continue.",
                    "code": "birth_year_required",
                }
            ),
            403,
        )

    persona_db = (user.preferred_persona or "adult").lower().strip()
    persona = persona_db if persona_db in valid_personas else _persona_from_birth_year(int(user.birth_year))

    message_history: List[Dict[str, str]] = []
    active_chat: Optional[Chat] = None

    if user and chat_id:
        active_chat = Chat.query.filter_by(id=int(chat_id), user_id=user.id).first()
        if active_chat:
            message_history = _load_chat_history(active_chat)
    if not message_history and isinstance(client_history, list):
        message_history = [
            {"role": h.get("role", ""), "content": (h.get("content") or "").strip()}
            for h in client_history
            if isinstance(h, dict) and (h.get("content") or "").strip()
        ]

    snippet = _conversation_snippet_from_history(message_history)
    needs_clarification, _reason = assess_query_clarity(query_text, persona, snippet)

    logger.info("Processing query: '%s' persona=%s lang=%s chat=%s", query_text, persona, language, chat_id)

    user_memory_for_prompt = None
    if guidance_mode != "parmaan" and getattr(user, "memory_enabled", True):
        _mem_block = format_memory_context_for_prompt(load_active_memories_for_user(user))
        if _mem_block.strip():
            user_memory_for_prompt = _mem_block

    # Parmaan search: short lines and themes are expected; do not run guidance-style clarification.
    if needs_clarification and guidance_mode != "parmaan":
        raw = synthesize_chat_response(
            query_text,
            None,
            persona,
            language=language,
            message_history=message_history,
            guidance_mode="guidance",
            user_memory_context=user_memory_for_prompt,
        )
        ai_response, llm_provider, llm_model = _coerce_synthesis_result(raw)
        payload = {
            "response": ai_response,
            "shabad": None,
            "persona": persona,
            "language": language,
            "is_clarification": True,
        }
        msg_ids = _persist_messages(
            active_chat, query_text, ai_response, None, persona, language, llm_provider, llm_model
        )
        if msg_ids and getattr(user, "memory_enabled", True):
            umid, amid = msg_ids
            maybe_extract_and_save_after_guidance_turn(
                user,
                active_chat.id if active_chat else None,
                query_text,
                ai_response,
                umid,
                amid,
            )
        if active_chat and (not active_chat.title or active_chat.title == "New chat"):
            active_chat.title = generate_chat_title(query_text)
            db.session.commit()
            payload["chat_title"] = active_chat.title
        return jsonify(_finalize_ask_response_payload(payload)), 200

    # Configurable shabad counts (needed before Parmaan text-match disambiguation branch)
    llm_settings = LLMSettings.query.get(1)
    guidance_shabad_count = getattr(llm_settings, "guidance_shabad_count", 3) if llm_settings else 3
    parmaan_shabad_count = getattr(llm_settings, "parmaan_shabad_count", 5) if llm_settings else 5

    parmaan_discovery = _normalize_parmaan_discovery(data.get("parmaan_discovery_type"))
    effective_parmaan_count = parmaan_shabad_count
    try:
        pc_raw = data.get("parmaan_shabad_count")
        if pc_raw is not None:
            pc = int(pc_raw)
            if 1 <= pc <= 15:
                effective_parmaan_count = pc
    except (TypeError, ValueError):
        pass

    anchor_raw = (data.get("anchor_shabad_id") or "").strip()
    anchor_row: Optional[Shabad] = get_shabad_by_id(anchor_raw) if anchor_raw else None
    if anchor_raw and anchor_row is None:
        return jsonify({"error": "Unknown shabad id for anchor selection"}), 400

    query_vector: Optional[List[float]] = None

    # Parmaan without anchor: always confirm intent — show top-N nearest shabads to the question embedding.
    if guidance_mode == "parmaan" and anchor_row is None:
        query_vector = get_embedding(query_text)
        if not query_vector:
            logger.error("Embedding generation failed")
            return jsonify({"error": "Failed to process query embedding"}), 500
        candidate_rows = search_similar_shabads(
            query_embedding=query_vector,
            limit=PARMAAN_DISAMBIGUATION_TOP_N,
            persona=persona,
            exclude_parmaan_low_quality=True,
        )
        if not candidate_rows:
            candidate_rows = search_similar_shabads(
                query_embedding=query_vector,
                limit=PARMAAN_DISAMBIGUATION_TOP_N,
                exclude_parmaan_low_quality=True,
            )
        if not candidate_rows:
            return jsonify({"error": "No matching shabads found for this topic"}), 404

        n = len(candidate_rows)
        if n >= PARMAAN_DISAMBIGUATION_TOP_N:
            dis_msg = (
                f"Here are the {PARMAAN_DISAMBIGUATION_TOP_N} shabads in our database closest to your search. "
                "Which one did you mean? Tap a choice below to see related verses and commentary."
            )
        else:
            dis_msg = (
                f"Here are the {n} closest shabads we found. "
                "Which one did you mean? Tap below to see related verses and commentary."
            )
        candidates = [_disambiguation_candidate_dict(r) for r in candidate_rows]
        payload = {
            "response": dis_msg,
            "is_disambiguation": True,
            "is_clarification": False,
            "disambiguation_candidates": candidates,
            "original_query": query_text,
            "shabad": None,
            "shabads": [],
            "persona": persona,
            "language": language,
            "guidance_mode": guidance_mode,
            "parmaan_discovery_type": parmaan_discovery,
            "parmaan_shabad_count": effective_parmaan_count,
        }
        _persist_messages(active_chat, query_text, dis_msg, None, persona, language, None, None)
        if active_chat:
            active_chat.updated_at = datetime.utcnow()
            if not active_chat.title or active_chat.title == "New chat":
                active_chat.title = generate_chat_title(query_text)
            db.session.commit()
            payload["chat_title"] = active_chat.title
        return jsonify(_finalize_ask_response_payload(payload)), 200

    if query_vector is None:
        query_vector = get_embedding(query_text)
    if not query_vector:
        logger.error("Embedding generation failed")
        return jsonify({"error": "Failed to process query embedding"}), 500

    try:
        if guidance_mode == "parmaan":
            # Parmaan mode: similar / by-topic / dissimilar; optional explicit anchor after disambiguation
            similar_shabads = _retrieve_parmaan_shabads_for_chat(
                query_vector,
                parmaan_discovery,
                effective_parmaan_count,
                persona,
                anchor_shabad=anchor_row,
            )
            if not similar_shabads:
                return jsonify({"error": "No matching shabads found for this topic"}), 404

            # Format shabads for display
            shabads_list = []
            for shabad in similar_shabads:
                shabads_list.append(_shabad_response_payload(shabad))

            # After disambiguation, client may send "Selected: …" as query_text; use original search for LLM context.
            synthesis_user_query = query_text
            if anchor_row is not None and parmaan_original_query:
                synthesis_user_query = parmaan_original_query

            # Generate a brief intro about the shabads found
            raw = synthesize_chat_response(
                synthesis_user_query,
                [s.to_dict(include_embedding=True) for s in similar_shabads],
                persona,
                language=language,
                message_history=message_history,
                guidance_mode="parmaan",
                parmaan_discovery_type=parmaan_discovery,
                user_memory_context=None,
            )
            ai_response, llm_provider, llm_model = _coerce_synthesis_result(raw)

            payload = {
                "response": ai_response,
                "shabads": shabads_list,
                "shabad": shabads_list[0] if shabads_list else None,
                "persona": persona,
                "language": language,
                "is_clarification": False,
                "guidance_mode": guidance_mode,
                "parmaan_discovery_type": parmaan_discovery,
                "parmaan_shabad_count": effective_parmaan_count,
            }
            _persist_messages(
                active_chat, query_text, ai_response, similar_shabads[0].id if similar_shabads else None,
                persona, language, llm_provider, llm_model
            )
            if active_chat:
                active_chat.updated_at = datetime.utcnow()
                if not active_chat.title or active_chat.title == "New chat":
                    active_chat.title = generate_chat_title(query_text)
                db.session.commit()
                payload["chat_title"] = active_chat.title
            return jsonify(_finalize_ask_response_payload(payload)), 200

        # Default: Guidance mode - retrieve top shabads and provide guidance with summary
        similar_shabads = search_similar_shabads(query_embedding=query_vector, limit=guidance_shabad_count, persona=persona)
        if not similar_shabads:
            similar_shabads = search_similar_shabads(query_embedding=query_vector, limit=guidance_shabad_count)
        if not similar_shabads:
            return jsonify({"error": "No matching wisdom found in database"}), 404

        # Use all retrieved shabads for context
        shabad_list = [s.to_dict(include_embedding=True) for s in similar_shabads]
        raw = synthesize_chat_response(
            query_text,
            shabad_list,
            persona,
            language=language,
            message_history=message_history,
            guidance_mode="guidance",
            user_memory_context=user_memory_for_prompt,
        )
        ai_response, llm_provider, llm_model = _coerce_synthesis_result(raw)

        # Return the primary shabad in response, plus all shabads used for synthesis
        top_shabad = similar_shabads[0]
        shabad_payload = _shabad_response_payload(top_shabad)
        shabads_list = [_shabad_response_payload(s) for s in similar_shabads]
        payload = {
            "response": ai_response,
            "shabad": shabad_payload,
            "shabads": shabads_list,
            "persona": persona,
            "language": language,
            "is_clarification": False,
            "guidance_mode": guidance_mode,
        }
        msg_ids = _persist_messages(
            active_chat,
            query_text,
            ai_response,
            top_shabad.id,
            persona,
            language,
            llm_provider,
            llm_model,
        )
        if msg_ids and getattr(user, "memory_enabled", True):
            umid, amid = msg_ids
            maybe_extract_and_save_after_guidance_turn(
                user,
                active_chat.id if active_chat else None,
                query_text,
                ai_response,
                umid,
                amid,
            )
        if active_chat:
            active_chat.updated_at = datetime.utcnow()
            if not active_chat.title or active_chat.title == "New chat":
                active_chat.title = generate_chat_title(query_text)
            db.session.commit()
            payload["chat_title"] = active_chat.title

        return jsonify(_finalize_ask_response_payload(payload)), 200

    except Exception as e:
        logger.error("Error during retrieval or synthesis: %s", e)
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


def _persist_messages(
    chat: Optional[Chat],
    user_text: str,
    assistant_text: str,
    shabad_row_id: Optional[int],
    persona: str,
    language: str,
    llm_provider: Optional[str] = None,
    llm_model: Optional[str] = None,
) -> Optional[Tuple[int, int]]:
    """Persist user + assistant turns; returns (user_message_id, assistant_message_id) when chat exists."""
    if not chat:
        return None
    try:
        user_msg = Message(
            chat_id=chat.id,
            role="user",
            content=user_text,
            persona=persona,
            language=language,
        )
        asst_msg = Message(
            chat_id=chat.id,
            role="assistant",
            content=assistant_text,
            shabad_row_id=shabad_row_id,
            persona=persona,
            language=language,
            llm_provider=llm_provider,
            llm_model=llm_model,
        )
        db.session.add(user_msg)
        db.session.add(asst_msg)
        db.session.flush()
        uid, aid = user_msg.id, asst_msg.id
        db.session.commit()
        return (uid, aid)
    except Exception as e:
        logger.warning("Failed to persist messages: %s", e)
        db.session.rollback()
        return None


@app.route("/random-shabads", methods=["GET"])
def random_shabads():
    limit = request.args.get("limit", default=3, type=int)
    shabads = get_random_shabads(limit=limit)
    return jsonify({"shabads": [s.to_api_dict() for s in shabads]}), 200


if __name__ == "__main__":
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"Warning: Could not create tables: {e}")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
