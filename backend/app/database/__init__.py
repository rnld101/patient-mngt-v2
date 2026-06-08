from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.models import Base

engine = None
SessionLocal = None


def init_db():
    """Initialize database connection and create tables."""
    global engine, SessionLocal
    
    if not settings.database_url:
        raise ValueError("DATABASE_URL not set")
    
    engine = create_engine(
        settings.database_url,
        echo=False,
        pool_size=20,
        max_overflow=40,
        pool_recycle=3600
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create all tables automatically
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created (if not already exists)")


def get_db() -> Session:
    """Get database session dependency."""
    if SessionLocal is None:
        raise RuntimeError("Database not initialized")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
