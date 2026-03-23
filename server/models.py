import os
from flask_sqlalchemy import SQLAlchemy
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

db = SQLAlchemy()

class Shabad(db.Model):
    """
    Model for storing Gurbani verses with vector embeddings for semantic search.
    Designed for scalability on Google Cloud SQL (PostgreSQL).
    """
    __tablename__ = 'shabads'

    id = Column(Integer, primary_key=True)
    shabad_id = Column(String(50), unique=True, nullable=False)
    gurmukhi = Column(Text, nullable=False)
    romanization = Column(Text)
    english_translation = Column(Text, nullable=False)
    source = Column(String(100))
    recommended_persona = Column(String(20), default='any')
    
    # context_tags allows for quick metadata filtering (e.g. filter by 'child' persona)
    context_tags = Column(ARRAY(String))
    
    # embedding column stores the vector from Vertex AI (text-embedding-004 is 768 dims)
    # If using the base model, it might be 384 or 768. 768 is default for gecko/004.
    embedding = Column(Vector(768)) 
    
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Shabad {self.shabad_id}>'

    def to_dict(self):
        """Convert Shabad instance to dictionary."""
        return {
            'id': self.id,
            'shabad_id': self.shabad_id,
            'gurmukhi': self.gurmukhi,
            'romanization': self.romanization,
            'english_translation': self.english_translation,
            'source': self.source,
            'recommended_persona': self.recommended_persona,
            'context_tags': self.context_tags,
            'embedding': self.embedding,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
