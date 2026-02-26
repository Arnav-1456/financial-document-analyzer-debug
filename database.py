"""Database integration for storing analysis results and user data using SQLAlchemy + SQLite."""
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./financial_analyzer.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class AnalysisResult(Base):
    """Stores each financial document analysis result."""
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(String(36), unique=True, index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    query = Column(Text, nullable=False)
    status = Column(String(20), default="pending")  # pending | processing | success | failed
    analysis = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class UserQuery(Base):
    """Stores user query history for analytics."""
    __tablename__ = "user_queries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    query = Column(Text, nullable=False)
    filename = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# Create all tables
Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def save_analysis_result(task_id: str, filename: str, query: str, status: str = "pending"):
    """Create a new analysis result record."""
    db = SessionLocal()
    try:
        result = AnalysisResult(
            task_id=task_id,
            filename=filename,
            query=query,
            status=status,
        )
        db.add(result)
        db.commit()
        db.refresh(result)
        return result
    finally:
        db.close()


def update_analysis_result(task_id: str, status: str, analysis: str = None, error: str = None):
    """Update an existing analysis result."""
    db = SessionLocal()
    try:
        result = db.query(AnalysisResult).filter(AnalysisResult.task_id == task_id).first()
        if result:
            result.status = status
            if analysis:
                result.analysis = analysis
            if error:
                result.error = error
            if status in ("success", "failed"):
                result.completed_at = datetime.utcnow()
            db.commit()
            db.refresh(result)
        return result
    finally:
        db.close()


def get_analysis_result(task_id: str):
    """Retrieve an analysis result by task_id."""
    db = SessionLocal()
    try:
        return db.query(AnalysisResult).filter(AnalysisResult.task_id == task_id).first()
    finally:
        db.close()


def log_user_query(query: str, filename: str = None):
    """Log a user query for analytics."""
    db = SessionLocal()
    try:
        entry = UserQuery(query=query, filename=filename)
        db.add(entry)
        db.commit()
    finally:
        db.close()
