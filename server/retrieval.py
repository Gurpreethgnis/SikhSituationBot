from typing import List, Optional, Tuple

from gurbani_content_quality import MIN_ENGLISH_CHARS_PARMAAN, MIN_GURMUKHI_CHARS_PARMAAN
from models import Shabad, db
from sqlalchemy import func, or_
from sqlalchemy.exc import SQLAlchemyError


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
) -> List[Shabad]:
    """Neighbors in embedding space (excluding same row)."""
    # embedding may be a numpy vector from pgvector; never use `not embedding` (ambiguous truth value).
    if shabad is None or shabad.embedding is None:
        return []
    try:
        q = Shabad.query.filter(Shabad.embedding.isnot(None))
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
