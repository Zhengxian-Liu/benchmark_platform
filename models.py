"""Database models."""

from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from database import Base

class Session(Base):
    """Session model for tracking translation sessions."""
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_name: Mapped[str] = mapped_column(String, nullable=False)
    source_file_name: Mapped[str] = mapped_column(String)
    source_file_path: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    data: Mapped[Dict] = mapped_column(JSON)
    
    # Relationships
    languages = relationship("SessionLanguage", back_populates="session")
    texts = relationship("SessionText", back_populates="session")

class SessionLanguage(Base):
    """Language settings for a session."""
    __tablename__ = "session_languages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"))
    language_code: Mapped[str] = mapped_column(String)
    prompts: Mapped[Dict] = mapped_column(JSON)  # Store prompt config as JSON
    
    # Relationships
    session = relationship("Session", back_populates="languages")
    translations = relationship("Translation", back_populates="session_language")

class SessionText(Base):
    """Text segments in a session."""
    __tablename__ = "session_texts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"))
    text_id: Mapped[str] = mapped_column(String)  # Original text ID
    source_text: Mapped[str] = mapped_column(String)
    extra_data: Mapped[Dict] = mapped_column(JSON, nullable=True)  # Store extra data as JSON
    
    # Relationships
    session = relationship("Session", back_populates="texts")
    translations = relationship("Translation", back_populates="session_text")

class Translation(Base):
    """Translation results."""
    __tablename__ = "translations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_text_id: Mapped[int] = mapped_column(ForeignKey("session_texts.id"))
    session_language_id: Mapped[int] = mapped_column(ForeignKey("session_languages.id"))
    translated_text: Mapped[str] = mapped_column(String)
    metrics: Mapped[Dict] = mapped_column(JSON, nullable=True)  # Store metrics as JSON
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    # Relationships
    session_text = relationship("SessionText", back_populates="translations")
    session_language = relationship("SessionLanguage", back_populates="translations")
    evaluations = relationship("EvaluationResult", back_populates="translation")

class EvaluationResult(Base):
    """Evaluation results for translations."""
    __tablename__ = "evaluation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    translation_id: Mapped[int] = mapped_column(ForeignKey("translations.id"))
    score: Mapped[float] = mapped_column(Integer)  # Overall score
    segment_scores: Mapped[Dict] = mapped_column(JSON, nullable=True)  # Per-segment scores
    comments: Mapped[Dict] = mapped_column(JSON, nullable=True)  # Comments as JSON
    metrics: Mapped[Dict] = mapped_column(JSON, nullable=True)  # Additional metrics
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    # Relationships
    translation = relationship("Translation", back_populates="evaluations")

class StyleGuide(Base):
    """Style guide for translation projects."""
    __tablename__ = "style_guides"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_name: Mapped[str] = mapped_column(String, nullable=False)
    language_code: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)  # Store guide content
    version: Mapped[int] = mapped_column(Integer, default=1)
    source_file_name: Mapped[str] = mapped_column(String, nullable=False)  # Original file name
    guide_metadata: Mapped[Dict] = mapped_column(JSON, nullable=True)  # Store additional metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    created_by: Mapped[str] = mapped_column(String, nullable=False)  # Who created this guide
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

class Prompt(Base):
    """Translation prompts."""
    __tablename__ = "prompts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_name: Mapped[str] = mapped_column(String, nullable=False)
    language_code: Mapped[str] = mapped_column(String, nullable=False)
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_by: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_by: Mapped[str] = mapped_column(String, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
