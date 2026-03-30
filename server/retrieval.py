import re
from typing import List, Optional, Tuple

from gurbani_content_quality import MIN_ENGLISH_CHARS_PARMAAN, MIN_GURMUKHI_CHARS_PARMAAN
from models import Shabad, db
from parmaan_search_normalize import latin_token_search_variants, token_has_gurmukhi
from sqlalchemy import func, or_
from sqlalchemy.exc import SQLAlchemyError


def _tokenize_search_words(query: str) -> List[str]:
    """Split query into non-trivial tokens for AND-style text match (Latin or Gurmukhi)."""
    q = (query or "").strip()
    if not q:
        return []
    parts = re.split(r"\s+", q)
    out: List[str] = []
    for p in parts:
        p = p.strip('.,;:!?|•·"\'()[]')
        if len(p) >= 2:
            out.append(p)
    return out


def _filter_shabad_matches_token(base, token: str):
    """
    AND-filter step: row must match this token in gurmukhi OR romanization OR english.
    Latin tokens expand via phonetic variants; Gurmukhi tokens match literally.
    """
    if token_has_gurmukhi(token):
        variants = [token]
    else:
        variants = latin_token_search_variants(token)
    token_clauses = []
    for v in variants:
        pattern = f"%{v}%"
        token_clauses.append(
            or_(
                Shabad.gurmukhi.ilike(pattern),
                Shabad.romanization.ilike(pattern),
                Shabad.english_translation.ilike(pattern),
            )
        )
    return base.filter(or_(*token_clauses))


def find_shabads_by_text_match(query: str, limit: int = 12) -> List[Shabad]:
    """
    Find shabads whose Gurmukhi, romanization, or English contains the search text.
    Uses AND across tokens when multiple words are present (narrower matches).
    Applies Parmaan quality filters (excludes header-only stubs and very short rows).
    """
    q = (query or "").strip()
    if len(q) < 3:
        return []
    words = _tokenize_search_words(q)
    if not words and len(q.strip()) >= 2:
        words = [q.strip()]
    if not words:
        return []
    try:
        base = Shabad.query.filter(Shabad.embedding.isnot(None))
        base = _apply_parmaan_quality_filters(base, True)
        for w in words:
            base = _filter_shabad_matches_token(base, w)
        rows = (
            base.order_by(func.coalesce(Shabad.content_length, 0).desc(), Shabad.id.asc())
            .limit(limit)
            .all()
        )
        return rows
    except SQLAlchemyError as e:
        print(f"[retrieval] text match failure: {e}")
        return []


def _apply_parmaan_quality_filters(query, exclude_parmaan_low_quality: bool):
    """
    Drop Raag/Mehla header stubs and overly short rows from Parmaan / discovery search.
    Rows with is_header_only IS NULL are kept (pre-backfill compatibility) unless
    they fail the length gate (headers are almost always short).
    """
    if not exclude_parmaan_low_quality:
        return query
    query = query.filter(Shabad.is_header_only.isnot(True))
    query = query.filter(func.length(Shabad.gurmukhi) >= MIN_GURMUKHI_CHARS_PARMAAN)
    query = query.filter(func.length(Shabad.english_translation) >= MIN_ENGLISH_CHARS_PARMAAN)
    return query


def find_similar_shabads(
    query_embedding: List[float],
    limit: int = 5,
    persona: Optional[str] = None,
    exclude_parmaan_low_quality: bool = False,
):
    """Return top-k most similar Shabad rows by cosine similarity."""
    if not query_embedding:
        return []

    try:
        query = Shabad.query

        if persona:
            query = query.filter(Shabad.recommended_persona.in_([persona, "any"]))

        query = _apply_parmaan_quality_filters(query, exclude_parmaan_low_quality)

        fetch_n = limit
        if exclude_parmaan_low_quality:
            # Nearest neighbors may be mostly header stubs; fetch extra then trim.
            fetch_n = min(max(limit * 8, 24), 120)

        rows = query.order_by(Shabad.embedding.cosine_distance(query_embedding)).limit(fetch_n).all()
        return rows[:limit]
    except SQLAlchemyError as e:
        print(f"[retrieval] DB query failure: {e}")
        return []


def search_similar_shabads(
    query_embedding: List[float],
    limit: int = 5,
    persona: Optional[str] = None,
    exclude_parmaan_low_quality: bool = False,
):
    """Alias for find_similar_shabads to match test expectations."""
    return find_similar_shabads(query_embedding, limit, persona, exclude_parmaan_low_quality)


def get_random_shabads(limit: int = 3):
    """Return a random selection of shabads."""
    try:
        from sqlalchemy.sql import func

        return Shabad.query.order_by(func.random()).limit(limit).all()
    except SQLAlchemyError as e:
        print(f"[retrieval] DB random query failure: {e}")
        return []


def get_shabad_by_id(shabad_id: str):
    """Return a shabad by its string shabad_id."""
    try:
        return Shabad.query.filter_by(shabad_id=shabad_id).first()
    except SQLAlchemyError as e:
        print(f"[retrieval] DB ID query failure: {e}")
        return None


def get_shabad_by_pk(pk: int):
    """Return a shabad by primary key."""
    try:
        return db.session.get(Shabad, pk)
    except SQLAlchemyError as e:
        print(f"[retrieval] DB pk query failure: {e}")
        return None


def browse_shabads(
    page: int = 1,
    per_page: int = 20,
    source: Optional[str] = None,
    search: Optional[str] = None,
    persona: Optional[str] = None,
) -> Tuple[List[Shabad], int]:
    """Paginated list with optional filters. Returns (items, total_count)."""
    try:
        q = Shabad.query
        if source:
            q = q.filter(Shabad.source.ilike(f"%{source}%"))
        if persona:
            q = q.filter(Shabad.recommended_persona.in_([persona, "any"]))
        if search:
            term = f"%{search}%"
            q = q.filter(
                or_(
                    Shabad.gurmukhi.ilike(term),
                    Shabad.english_translation.ilike(term),
                    Shabad.romanization.ilike(term),
                    Shabad.shabad_id.ilike(term),
                )
            )
        total = q.count()
        items = (
            q.order_by(Shabad.id.asc())
            .offset(max(0, (page - 1) * per_page))
            .limit(per_page)
            .all()
        )
        return items, total
    except SQLAlchemyError as e:
        print(f"[retrieval] browse failure: {e}")
        return [], 0


def find_similar_to_shabad(
    shabad: Shabad,
    limit: int = 6,
    exclude_self: bool = True,
    exclude_parmaan_low_quality: bool = False,
    persona: Optional[str] = None,
) -> List[Shabad]:
    """Neighbors in embedding space (excluding same row)."""
    # embedding may be a numpy vector from pgvector; never use `not embedding` (ambiguous truth value).
    if shabad is None or shabad.embedding is None:
        return []
    try:
        q = Shabad.query.filter(Shabad.embedding.isnot(None))
        if persona:
            q = q.filter(Shabad.recommended_persona.in_([persona, "any"]))
        if exclude_self:
            q = q.filter(Shabad.id != shabad.id)
        q = _apply_parmaan_quality_filters(q, exclude_parmaan_low_quality)
        fetch_n = limit
        if exclude_parmaan_low_quality:
            fetch_n = min(max(limit * 8, 24), 120)
        rows = q.order_by(Shabad.embedding.cosine_distance(shabad.embedding)).limit(fetch_n).all()
        return rows[:limit]
    except SQLAlchemyError as e:
        print(f"[retrieval] similar failure: {e}")
        return []
