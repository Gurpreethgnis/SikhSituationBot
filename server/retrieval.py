from typing import List, Optional, Tuple

from models import Shabad, db
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError


def find_similar_shabads(query_embedding: List[float], limit: int = 5, persona: Optional[str] = None):
    """Return top-k most similar Shabad rows by cosine similarity."""
    if not query_embedding:
        return []

    try:
        query = Shabad.query

        if persona:
            query = query.filter(Shabad.recommended_persona.in_([persona, "any"]))

        return query.order_by(Shabad.embedding.cosine_distance(query_embedding)).limit(limit).all()
    except SQLAlchemyError as e:
        print(f"[retrieval] DB query failure: {e}")
        return []


def search_similar_shabads(query_embedding: List[float], limit: int = 5, persona: Optional[str] = None):
    """Alias for find_similar_shabads to match test expectations."""
    return find_similar_shabads(query_embedding, limit, persona)


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


def find_similar_to_shabad(shabad: Shabad, limit: int = 6, exclude_self: bool = True) -> List[Shabad]:
    """Neighbors in embedding space (excluding same row)."""
    if not shabad or not shabad.embedding:
        return []
    try:
        q = Shabad.query.filter(Shabad.embedding.isnot(None))
        if exclude_self:
            q = q.filter(Shabad.id != shabad.id)
        return q.order_by(Shabad.embedding.cosine_distance(shabad.embedding)).limit(limit).all()
    except SQLAlchemyError as e:
        print(f"[retrieval] similar failure: {e}")
        return []
