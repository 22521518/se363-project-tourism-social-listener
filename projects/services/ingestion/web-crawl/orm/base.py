"""
SQLAlchemy Base - Database configuration for web crawl module.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Database URL from environment - supports both full URL and individual vars
def _get_database_url():
    """Build database URL from environment variables."""
    # Try individual env vars first (matching docker-compose)
    db_host = os.getenv("DB_HOST")
    if db_host:
        db_user = os.getenv("DB_USER", "airflow")
        db_pass = os.getenv("DB_PASSWORD", "airflow")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "airflow")
        return f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    
    # Fallback to full URL
    return os.getenv(
        "WEBCRAWL_DATABASE_URL",
        "postgresql://airflow:airflow@localhost:5432/airflow"
    )

DATABASE_URL = _get_database_url()

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=False,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base
Base = declarative_base()


def get_session():
    """Get a database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db():
    """Initialize the database (create all tables)."""
    Base.metadata.create_all(bind=engine)
