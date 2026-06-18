import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from contextlib import contextmanager
from config import DATABASE_URL

logger = logging.getLogger(__name__)

# Fallback mechanism
try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    DATABASE_AVAILABLE = True
except Exception as e:
    logger.error(f"Failed to connect to database at {DATABASE_URL}: {e}")
    DATABASE_AVAILABLE = False
    engine = None
    SessionLocal = None

Base = declarative_base()

@contextmanager
def get_db_session():
    """
    Context manager for database sessions.
    Yields None if the database is not available.
    """
    if not DATABASE_AVAILABLE or not SessionLocal:
        yield None
        return

    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        yield None
    finally:
        session.close()

def init_db():
    """
    Initialize database tables.
    Safe to call multiple times.
    """
    global DATABASE_AVAILABLE
    if DATABASE_AVAILABLE and engine:
        try:
            # Import models here to ensure they are registered with Base
            from database.models import trip_cache, weather_cache, image_cache, chat_history
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables verified/created successfully.")
        except Exception as e:
            logger.error(f"Error initializing database tables: {e}")
            DATABASE_AVAILABLE = False
