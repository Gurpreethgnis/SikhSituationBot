import os
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

db = SQLAlchemy()


class User(db.Model):
    """Registered user (email/password or OAuth-linked)."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(100))
    avatar_url = Column(String(500))
    password_hash = Column(String(256))  # null for OAuth-only accounts
    preferred_language = Column(String(10), default="en")
    preferred_persona = Column(String(20), default="adult")
    preferred_theme = Column(String(20), default="saffron")
    is_admin = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    chats = relationship("Chat", back_populates="user", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self, include_sensitive=False):
        d = {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "avatar_url": self.avatar_url,
            "preferred_language": self.preferred_language,
            "preferred_persona": self.preferred_persona,
            "preferred_theme": self.preferred_theme,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
        if include_sensitive:
            d["is_active"] = self.is_active
        return d


class Chat(db.Model):
    """A conversation thread owned by a user."""

    __tablename__ = "chats"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), default="New chat")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_shared = Column(Boolean, default=False, nullable=False)
    share_id = Column(String(36), unique=True, index=True)

    user = relationship("User", back_populates="chats")
    messages = relationship("Message", back_populates="chat", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self, include_messages=False):
        d = {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_shared": self.is_shared,
            "share_id": self.share_id,
        }
        if include_messages:
            d["messages"] = [m.to_dict() for m in self.messages.order_by(Message.created_at.asc()).all()]
        return d


class Message(db.Model):
    """Single turn in a chat."""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user | assistant
    content = Column(Text, nullable=False)
    shabad_row_id = Column(Integer, ForeignKey("shabads.id", ondelete="SET NULL"), nullable=True)
    persona = Column(String(20))
    language = Column(String(10), default="en")
    llm_provider = Column(String(32), nullable=True)
    llm_model = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    chat = relationship("Chat", back_populates="messages")
    shabad = relationship("Shabad", backref="linked_messages")

    def to_dict(self):
        out = {
            "id": self.id,
            "chat_id": self.chat_id,
            "role": self.role,
            "content": self.content,
            "persona": self.persona,
            "language": self.language,
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if self.shabad:
            out["shabad"] = self.shabad.to_api_dict()
        else:
            out["shabad"] = None
        return out


class LLMSettings(db.Model):
    """Singleton row (id=1): active chat synthesis provider and model for /ask."""

    __tablename__ = "llm_settings"

    id = Column(Integer, primary_key=True)
    provider = Column(String(32), nullable=False, default="gemini")
    model_id = Column(String(128), nullable=False, default="models/gemini-flash-latest")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Shabad(db.Model):
    """
    Model for storing Gurbani verses with vector embeddings for semantic search.
    Designed for scalability on Google Cloud SQL (PostgreSQL).
    """

    __tablename__ = "shabads"

    id = Column(Integer, primary_key=True)
    shabad_id = Column(String(50), unique=True, nullable=False)
    gurmukhi = Column(Text, nullable=False)
    romanization = Column(Text)
    english_translation = Column(Text, nullable=False)
    source = Column(String(100))
    recommended_persona = Column(String(20), default="any")

    context_tags = Column(ARRAY(String))

    embedding = Column(Vector())

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Shabad {self.shabad_id}>"

    @staticmethod
    def sttm_url_for(shabad_id: str) -> str:
        """Public SikhiToTheMax link for this verse identifier."""
        if not shabad_id:
            return ""
        from urllib.parse import quote

        return f"https://www.sikhitothemax.org/shabad?id={quote(str(shabad_id), safe='')}"

    def to_dict(self, include_embedding=True):
        """Full dict including embedding (for internal RAG / tests)."""
        return {
            "id": self.id,
            "shabad_id": self.shabad_id,
            "gurmukhi": self.gurmukhi,
            "romanization": self.romanization,
            "english_translation": self.english_translation,
            "source": self.source,
            "recommended_persona": self.recommended_persona,
            "context_tags": self.context_tags,
            "embedding": self.embedding if include_embedding else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "sttm_link": self.sttm_url_for(self.shabad_id),
        }

    def to_api_dict(self):
        """Safe JSON for clients (no embedding)."""
        return {
            "id": self.id,
            "shabad_id": self.shabad_id,
            "gurmukhi": self.gurmukhi,
            "romanization": self.romanization,
            "english_translation": self.english_translation,
            "source": self.source,
            "recommended_persona": self.recommended_persona,
            "context_tags": self.context_tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "sttm_link": self.sttm_url_for(self.shabad_id),
        }
