"""
Hermes Web Data API - Database Models
=====================================
SQLAlchemy models for audit logging and data classification.
"""

import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    Boolean,
    Enum,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship, Session
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from pydantic import BaseModel, Field
import uuid


# ============================================================================
# Base Model
# ============================================================================

Base = declarative_base()


# ============================================================================
# Audit Log Models
# ============================================================================

class AuditLog(Base):
    """
    Audit log for API requests.
    
    Tracks all API requests for compliance and security monitoring.
    """
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(36), index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(64), nullable=True)  # API key user
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    client_ip = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    details = Column(JSON, nullable=True)
    sanitized = Column(Boolean, default=True)  # Was content sanitized?
    
    __table_args__ = (
        Index("idx_request_id", "request_id"),
        Index("idx_created_at", "created_at"),
        Index("idx_endpoint", "endpoint"),
        Index("idx_user_id", "user_id"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "request_id": self.request_id,
            "user_id": self.user_id,
            "endpoint": self.endpoint,
            "method": self.method,
            "status_code": self.status_code,
            "duration_ms": self.duration_ms,
            "client_ip": self.client_ip,
            "user_agent": self.user_agent[:200] if self.user_agent else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "details": self.details,
            "sanitized": self.sanitized,
        }


class SecurityAlertLog(Base):
    """
    Security alert log.
    
    Records all security-related events and alerts.
    """
    __tablename__ = "security_alert_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(100), nullable=False)
    severity = Column(Enum("INFO", "WARNING", "ERROR", "CRITICAL"), nullable=False)
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    request_id = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        Index("idx_alert_type", "alert_type"),
        Index("idx_severity", "severity"),
        Index("idx_created_at", "created_at"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "alert_type": self.alert_type,
            "severity": self.severity.value,
            "message": self.message,
            "details": self.details,
            "request_id": self.request_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


# ============================================================================
# Data Classification Models
# ============================================================================

class DataClassificationLog(Base):
    """
    Data classification log for compliance.
    
    Tracks classification of extracted data.
    """
    __tablename__ = "data_classifications"
    
    id = Column(Integer, primary_key=True, index=True)
    data_hash = Column(String(64), unique=True, nullable=False, index=True)
    classification = Column(String(50), nullable=False)
    source_url = Column(String(500), nullable=True)
    extracted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    classification_metadata = Column(JSON, nullable=True)
    user_id = Column(String(64), nullable=True)
    retention_days = Column(Integer, nullable=True)
    
    __table_args__ = (
        Index("idx_classification", "classification"),
        Index("idx_source_url", "source_url"),
        Index("idx_user_id", "user_id"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "data_hash": self.data_hash,
            "classification": self.classification,
            "source_url": self.source_url,
            "extracted_at": self.extracted_at.isoformat() if self.extracted_at else None,
            "classification_metadata": self.classification_metadata,
            "user_id": self.user_id,
            "retention_days": self.retention_days,
        }


class DataExtractionLog(Base):
    """
    Data extraction log.
    
    Records details of data extraction operations.
    """
    __tablename__ = "data_extractions"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(36), nullable=False)
    url = Column(String(500), nullable=False)
    fields_extracted = Column(JSON, nullable=True)
    extraction_method = Column(String(50), nullable=False)
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    classification = Column(String(50), nullable=False)
    sanitized = Column(Boolean, default=True)
    
    __table_args__ = (
        Index("idx_request_id", "request_id"),
        Index("idx_url", "url"),
        Index("idx_classification", "classification"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "request_id": self.request_id,
            "url": self.url,
            "fields_extracted": self.fields_extracted,
            "extraction_method": self.extraction_method,
            "success": self.success,
            "error_message": self.error_message,
            "duration_ms": self.duration_ms,
            "created_at": self.created_at.isoformat() if self.extracted_at else None,
            "classification": self.classification,
            "sanitized": self.sanitized,
        }


# ============================================================================
# Conversation Models (for Hermes Chat)
# ============================================================================

class Conversation(Base):
    """
    Conversation history for Hermes chat.
    
    Stores chat history with Hermes AI assistant.
    """
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(String(64), nullable=True)
    message = Column(Text, nullable=False)
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    conversation_metadata = Column(JSON, nullable=True)
    sanitized = Column(Boolean, default=True)
    
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_created_at", "created_at"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
 "conversation_id": self.conversation_id,
    "user_id": self.user_id,
    "message": self.message[:5000],  # Truncate for safety
    "role": self.role,
    "created_at": self.created_at.isoformat() if self.created_at else None,
    "conversation_metadata": self.conversation_metadata,
    "sanitized": self.sanitized,
}


# ============================================================================
# Database Setup Functions
# ============================================================================

def create_database_engine(
    url: str = "postgresql://user:pass@localhost/hermes",
    pool_size: int = 5,
    max_overflow: int = 10,
    pool_recycle: int = 3600
) -> create_async_engine:
    """
    Create async database engine.
    
    Args:
        url: Database connection URL
        pool_size: Connection pool size
        max_overflow: Max overflow connections
        pool_recycle: Pool recycle time in seconds
    
    Returns:
        Configured async engine
    """
    engine = create_async_engine(
        url,
        poolclass=NullPool,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_recycle=pool_recycle,
        echo=False,  # Set to True for debugging
        future=True,
    )
    return engine


async def create_tables(engine: create_async_engine) -> None:
    """
    Create all tables in database.
    
    Use in migrations or initial setup.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("Database tables created successfully")


async def drop_tables(engine: create_async_engine) -> None:
    """
    Drop all tables (for testing).
    
    WARNING: This is destructive!
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    print("Database tables dropped successfully")


# ============================================================================
# Session Management
# ============================================================================

def get_session_maker(
    engine: create_async_engine,
    autocommit: bool = False,
    autoflush: bool = True
) -> async_sessionmaker:
    """
    Create session factory.
    
    Args:
        engine: Database engine
        autocommit: Auto-commit transactions
        autoflush: Auto-flush before queries
    
    Returns:
        Session factory
    """
    return async_sessionmaker(
        bind=engine,
        autocommit=autocommit,
        autoflush=autoflush,
        expire_on_commit=True,
    )


async def init_db(
    url: str = "postgresql://user:pass@localhost/hermes",
    pool_size: int = 5,
    max_overflow: int = 10
) -> tuple:
    """
    Initialize database connection.
    
    Args:
        url: Database connection URL
        pool_size: Connection pool size
        max_overflow: Max overflow connections
    
    Returns:
        Tuple of (engine, session_maker)
    """
    engine = create_database_engine(
        url=url,
        pool_size=pool_size,
        max_overflow=max_overflow,
    )
    
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        
        # Check if tables exist
        result = await conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table';"
        )
        tables = [row[0] for row in result.fetchall()]
    
    print(f"Database initialized: {len(tables)} tables created")
    
    return engine, get_session_maker(engine)


# ============================================================================
# Query Helpers
# ============================================================================

async def get_audit_logs(
    limit: int = 100,
    offset: int = 0,
    endpoint: Optional[str] = None,
    session: Optional[AsyncSession] = None
) -> List[Dict[str, Any]]:
    """
    Query audit logs.
    
    Args:
        limit: Number of records to return
        offset: Offset for pagination
        endpoint: Filter by endpoint
        session: Optional session (creates new if not provided)
    
    Returns:
        List of audit log records
    """
    if session is None:
        # Get engine from settings or environment
        import os
        db_url = os.getenv("DB_URL", "postgresql://user:pass@localhost/hermes")
        engine = create_async_engine(db_url)
        session = async_sessionmaker(bind=engine)()
    
    query = AuditLog.query.filter_by(endpoint=endpoint) if endpoint else AuditLog.query
    
    if limit:
        query = query.limit(limit).offset(offset)
    
    results = await session.execute(query.order_by(AuditLog.created_at.desc()))
    rows = results.all()
    
    return [row.to_dict() for row in rows]


async def get_security_alerts(
    limit: int = 50,
    severity: Optional[str] = None,
    session: Optional[AsyncSession] = None
) -> List[Dict[str, Any]]:
    """
    Query security alerts.
    
    Args:
        limit: Number of alerts to return
        severity: Filter by severity (INFO, WARNING, ERROR, CRITICAL)
        session: Optional session
    
    Returns:
        List of security alert records
    """
    if session is None:
        import os
        db_url = os.getenv("DB_URL", "postgresql://user:pass@localhost/hermes")
        engine = create_async_engine(db_url)
        session = async_sessionmaker(bind=engine)()
    
    query = SecurityAlertLog.query
    
    if severity:
        query = query.filter_by(severity=severity)
    
    if limit:
        query = query.limit(limit)
    
    results = await session.execute(query.order_by(SecurityAlertLog.created_at.desc()))
    rows = results.all()
    
    return [row.to_dict() for row in rows]


async def get_data_classifications(
    classification: Optional[str] = None,
    limit: int = 100,
    session: Optional[AsyncSession] = None
) -> List[Dict[str, Any]]:
    """
    Query data classifications.
    
    Args:
        classification: Filter by classification
        limit: Number of records to return
        session: Optional session
    
    Returns:
        List of classification records
    """
    if session is None:
        import os
        db_url = os.getenv("DB_URL", "postgresql://user:pass@localhost/hermes")
        engine = create_async_engine(db_url)
        session = async_sessionmaker(bind=engine)()
    
    query = DataClassificationLog.query
    
    if classification:
        query = query.filter_by(classification=classification)
    
    if limit:
        query = query.limit(limit)
    
    results = await session.execute(query.order_by(DataClassificationLog.extracted_at.desc()))
    rows = results.all()
    
    return [row.to_dict() for row in rows]


# ============================================================================
# Export/Import Helpers
# ============================================================================

def export_audit_logs(
    limit: int = 1000,
    format: str = "json"
) -> str:
    """
    Export audit logs for compliance reporting.
    
    Args:
        limit: Maximum records to export
        format: Output format (json, csv)
    
    Returns:
        Exported data as string
    """
    # Implementation would query database and format output
    return f"# Audit Logs Export\n# Limit: {limit}\n# Format: {format}\n"


def export_security_alerts(
    limit: int = 1000,
    format: str = "json"
) -> str:
    """
    Export security alerts for incident review.
    
    Args:
        limit: Maximum alerts to export
        format: Output format (json, csv)
    
    Returns:
        Exported data as string
    """
    return f"# Security Alerts Export\n# Limit: {limit}\n# Format: {format}\n"


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import asyncio
    
    async def main():
        print("Database Models Module Loaded")
        print("=" * 60)
        
        # Demo: Create tables
        print("\nCreating database engine...")
        engine = create_database_engine(
            url="sqlite+aiosqlite:///:memory:",  # Use SQLite for demo
            pool_size=1,
            max_overflow=0,
        )
        
        print("Creating tables...")
        await create_tables(engine)
        
        print("\nTesting query...")
        async with engine.begin() as conn:
            result = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table';"
            )
            tables = [row[0] for row in result.fetchall()]
        
        print(f"Created tables: {tables}")
        
        # Clean up
        print("\nCleaning up...")
        await drop_tables(engine)
        print("Done.")
    
    asyncio.run(main())