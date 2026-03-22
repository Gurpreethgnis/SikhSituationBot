from typing import List, Optional

from models import Shabad
from sqlalchemy.exc import SQLAlchemyError


def find_similar_shabads(query_embedding: List[float], limit: int = 5, persona: Optional[str] = None):
    """Return top-k most similar Shabad rows by cosine similarity."""
    if not query_embedding:
        return []

    try:
        query = Shabad.query

        # Optional persona-based pre-filtering (if persona is stored)
        if persona:
            query = query.filter(Shabad.recommended_persona == persona)

        # Cosine distance based on pgvector; smaller is better
        return query.order_by(Shabad.embedding.cosine_distance(query_embedding)).limit(limit).all()

    except SQLAlchemyError as e:
        print(f"[retrieval] DB query failure: {e}")
        return []
