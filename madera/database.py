"""
MADERA MCP - Database Models
SQLAlchemy async models + session management
"""
from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, ForeignKey, LargeBinary
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from datetime import datetime
from typing import Optional, Dict, Any
from madera.config import settings


# ==================== BASE ====================
class Base(DeclarativeBase):
    """Base model for all tables"""
    pass


# ==================== ENGINE & SESSION ====================
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db_session() -> AsyncSession:
    """Dependency for FastAPI routes"""
    async with async_session_maker() as session:
        yield session


# Alias for compatibility
get_db = get_db_session


# ==================== MODELS ====================

class ToolClass(Base):
    """Tool categories (hypothecaire, all_around, avocat, comptable)"""
    __tablename__ = "tool_classes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )

    def __repr__(self):
        return f"<ToolClass {self.name}>"


class ToolTemplate(Base):
    """Templates for logo/zone matching"""
    __tablename__ = "tool_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tool_name: Mapped[str] = mapped_column(String(100), index=True)
    document_type: Mapped[str] = mapped_column(String(100), index=True)
    logo_name: Mapped[str] = mapped_column(String(100))
    logo_image: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)

    # JSONB fields
    zones: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    thresholds: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    precision_rate: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )

    def __repr__(self):
        return f"<ToolTemplate {self.tool_name}/{self.document_type}>"


class ToolExecution(Base):
    """Log of tool executions for analytics"""
    __tablename__ = "tool_executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tool_name: Mapped[str] = mapped_column(String(100), index=True)
    tool_class: Mapped[str] = mapped_column(String(100))

    success: Mapped[bool] = mapped_column(Boolean, index=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)
    execution_time_ms: Mapped[int] = mapped_column(Integer)

    # JSONB fields
    inputs: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    outputs: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    trained: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<ToolExecution {self.tool_name} - {self.created_at}>"


class TrainingQueue(Base):
    """Queue for async learning"""
    __tablename__ = "training_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tool_name: Mapped[str] = mapped_column(String(100), index=True)
    execution_id: Mapped[int] = mapped_column(ForeignKey("tool_executions.id"))
    pdf_url: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float)

    processed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationship
    execution: Mapped["ToolExecution"] = relationship("ToolExecution")

    def __repr__(self):
        return f"<TrainingQueue {self.tool_name} - processed={self.processed}>"


class SystemSettings(Base):
    """System-wide settings"""
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    value: Mapped[str] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<SystemSettings {self.key}={self.value}>"



class TrainingSession(Base):
    """Training session for AI learning"""
    __tablename__ = "training_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    mode: Mapped[str] = mapped_column(String(50))  # logo_detection, zone_extraction, etc.
    file_count: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(50), index=True)  # uploaded, analyzed, completed

    # JSONB for results
    results: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def __repr__(self):
        return f"<TrainingSession {self.session_id} - {self.status}>"


# ==================== HELPER FUNCTIONS ====================

async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def seed_tool_classes():
    """Seed initial tool classes"""
    async with async_session_maker() as session:
        classes = [
            ToolClass(
                name="hypothecaire",
                display_name="Hypothécaire",
                description="Tools spécifiques au domaine hypothécaire"
            ),
            ToolClass(
                name="all_around",
                display_name="Général",
                description="Tools génériques (PDF, validation, etc.)"
            ),
            ToolClass(
                name="avocat",
                display_name="Avocat",
                description="Tools pour le domaine juridique (futur)"
            ),
            ToolClass(
                name="comptable",
                display_name="Comptable",
                description="Tools pour la comptabilité (futur)"
            ),
        ]

        for tool_class in classes:
            session.add(tool_class)

        await session.commit()
