from typing import List, Optional

from models import Shabad
from sqlalchemy.exc import SQLAlchemyError


def find_similar_shabads(query_embedding: List[float], limit: int = 5, persona: Optional[str] = None):
    """Return top-k most similar Shabad rows by cosine similarity."""
    if not query_embedding:
        return []

    try:
        query = Shabad.query

        # Persona-based filtering: include specific persona matches and general 'any' category
        if persona:
            query = query.filter(Shabad.recommended_persona.in_([persona, 'any']))

        # Cosine distance based on pgvector; smaller is better
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
    """Return a shabad by its ID."""
    try:
        return Shabad.query.filter_by(shabad_id=shabad_id).first()
    except SQLAlchemyError as e:
        print(f"[retrieval] DB ID query failure: {e}")
        return None
