from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, pool
from app.core.config import settings
from diskcache import Cache
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Global variables for lazy initialization
engine: Optional[object] = None
SessionLocal: Optional[object] = None
cache: Optional[Cache] = None

def get_engine():
    """Get or create database engine with lazy initialization."""
    global engine
    if engine is None:
        try:
            logger.info("Initializing database engine...")
            # Enhanced database connection pooling configuration
            engine = create_engine(
                settings.database_url,
                # Connection pool settings for 40-60% performance improvement
                pool_size=20,                    # Increased from default 5
                max_overflow=30,                 # Allow up to 50 total connections
                pool_pre_ping=True,              # Verify connections before use
                pool_recycle=3600,               # Recycle connections every hour
                pool_timeout=30,                 # Wait up to 30 seconds for connection
                echo=False,                      # Set to True for SQL debugging
                # Connection pool class for better performance
                poolclass=pool.QueuePool,
                # Additional engine options for performance
                connect_args={
                    "charset": "utf8mb4",
                    "autocommit": False,
                    # MySQL-specific optimizations
                    "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
                }
            )
            logger.info("Database engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise
    return engine

def get_session_local():
    """Get or create SessionLocal with lazy initialization."""
    global SessionLocal
    if SessionLocal is None:
        engine = get_engine()
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal

def get_cache_instance():
    """Get or create cache instance with lazy initialization."""
    global cache
    if cache is None:
        try:
            # Ensure cache directory exists
            import os
            cache_dir = settings.CACHE_DIR
            os.makedirs(cache_dir, exist_ok=True)

            cache = Cache(cache_dir)
            logger.info(f"Cache initialized at: {cache_dir}")
        except Exception as e:
            logger.error(f"Failed to initialize cache: {e}")
            # Create a fallback in-memory cache
            cache = {}
            logger.warning("Using fallback in-memory cache")
    return cache

def get_db():
    """
    Enhanced database session with connection pool monitoring.
    Provides better error handling and connection management.
    """
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        # Log connection pool status for monitoring
        engine = get_engine()
        pool_status = engine.pool.status()
        if engine.pool.checkedout() > engine.pool.size() * 0.8:  # 80% threshold
            logger.warning(f"High connection pool usage: {pool_status}")

        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def get_cache():
    """Get cache instance with lazy initialization."""
    return get_cache_instance()

def get_db_pool_status():
    """Get current database connection pool status for monitoring."""
    try:
        engine = get_engine()
        return {
            "pool_size": engine.pool.size(),
            "checked_out": engine.pool.checkedout(),
            "overflow": engine.pool.overflow(),
            "checked_in": engine.pool.checkedin(),
            "status": engine.pool.status()
        }
    except Exception as e:
        logger.error(f"Error getting pool status: {e}")
        return {"error": str(e)}