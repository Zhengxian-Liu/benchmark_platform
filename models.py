from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    source_file_name = Column(String)
    status = Column(String)  # "in_progress", "completed"

    # Relationship to texts in this session
    texts = relationship("SessionText", back_populates="session")

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

    # Relationship to translations using this prompt
    translations = relationship("Translation", back_populates="prompt")

class Translation(Base):
    __tablename__ = "translations"

    id = Column(Integer, primary_key=True, index=True)
    session_text_id = Column(Integer, ForeignKey("session_texts.id"))
    prompt_id = Column(Integer, ForeignKey("prompts.id"))
    translated_text = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metrics = Column(JSON)  # Store automated metrics

    # Relationships
    session_text = relationship("SessionText", back_populates="translations")
    prompt = relationship("Prompt", back_populates="translations")
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
    entries = Column(JSON)  # Store style guide entries
    timestamp = Column(DateTime, default=datetime.utcnow)