from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, JSON
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class TaskLog(Base):
    __tablename__ = "task_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), nullable=False, index=True)
    task_type = Column(String(100), nullable=False)
    input_text = Column(Text, nullable=True)
    agent_used = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    result_text = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    tokens_used = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)


class AgentRegistry(Base):
    __tablename__ = "agent_registry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    capabilities = Column(JSON, nullable=True)
    model_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class KnowledgeBaseMetadata(Base):
    __tablename__ = "knowledge_base_metadata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    collection_name = Column(String(100), nullable=False)
    source = Column(String(255), nullable=True)
    chunk_count = Column(Integer, default=0)
    embedding_model = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
