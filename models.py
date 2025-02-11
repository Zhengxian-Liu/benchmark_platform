from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    source_file_path = Column(String)  # Full path to source file
    source_file_name = Column(String)
    status = Column(String)  # "in_progress", "completed"
    data = Column(JSON)  # Store session snapshot

    # Relationship to texts in this session
    texts = relationship("SessionText", back_populates="session")
    # Relationship to selected languages
    languages = relationship("SessionLanguage", back_populates="session")
    # Relationship to style guides
    style_guides = relationship("StyleGuide",
                              secondary="session_style_guides",
                              back_populates="sessions")

class SessionLanguage(Base):
    __tablename__ = "session_languages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    language_code = Column(String, index=True)
    prompts = Column(JSON)  # Stores prompt versions used {"prompt_id": 123, "version": 2}
    
    # Relationships
    session = relationship("Session", back_populates="languages")
    translations = relationship("Translation", back_populates="session_language")

class SessionText(Base):
    __tablename__ = "session_texts"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    text_id = Column(String, nullable=False)  # ID from the source Excel
    __table_args__ = (
        Index('ix_session_texts_session_text_id', session_id, text_id, unique=True, postgresql_using='btree'),
    )
    source_text = Column(Text)
    extra_data = Column(Text)
    ground_truth = Column(JSON)  # {"language_code": "ground truth text"}
    # Add index for text_id to improve lookup performance
    # Existing installations need manual migration
    # __table_args__ = (Index('ix_session_texts_text_id', "text_id"),)

    # Relationship to parent session
    session = relationship("Session", back_populates="texts")
    # Relationship to translations
    translations = relationship("Translation", back_populates="session_text")

class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String, index=True)
    language_code = Column(String, index=True)
    prompt_text = Column(Text)
    version = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)
    change_log = Column(Text)

class Translation(Base):
    __tablename__ = "translations"

    id = Column(Integer, primary_key=True, index=True)
    session_text_id = Column(Integer, ForeignKey("session_texts.id"))
    session_language_id = Column(Integer, ForeignKey("session_languages.id"))
    translated_text = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metrics = Column(JSON)  # Store automated metrics

    # Relationships
    session_text = relationship("SessionText", back_populates="translations")
    session_language = relationship("SessionLanguage", back_populates="translations")
    evaluations = relationship("EvaluationResult", back_populates="translation")

class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id = Column(Integer, primary_key=True, index=True)
    translation_id = Column(Integer, ForeignKey("translations.id"))
    score = Column(Integer)  # Overall score
    segment_scores = Column(JSON)  # Per-segment scores
    comments = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationship to translation
    translation = relationship("Translation", back_populates="evaluations")

class StyleGuide(Base):
    __tablename__ = "style_guides"

    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String, index=True)
    language_code = Column(String, index=True)
    version = Column(Integer)
    entries = Column(JSON)  # Store style guide entries as {"chinese_name": {"gender": "...", "speaking_style": "..."}}
    file_name = Column(String)  # Original uploaded file name
    file_hash = Column(String)  # Hash of file content to detect changes
    status = Column(String)  # "active", "archived"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)  # User who uploaded the guide
    
    __table_args__ = (
        Index('ix_style_guides_project_lang_ver',
              project_name, language_code, version,
              unique=True),
    )

    # Relationship to sessions using this style guide
    sessions = relationship("Session",
                          secondary="session_style_guides",
                          back_populates="style_guides")

class SessionStyleGuide(Base):
    """Association table for sessions and style guides"""
    __tablename__ = "session_style_guides"

    session_id = Column(Integer, ForeignKey("sessions.id"), primary_key=True)
    style_guide_id = Column(Integer, ForeignKey("style_guides.id"), primary_key=True)
    applied_at = Column(DateTime, default=datetime.utcnow)