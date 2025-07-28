import os
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
    """Get or create database engine with production-optimized configuration."""
    global engine
    if engine is None:
        try:
            logger.info("Initializing production database engine...")

            # Check if we're in production mode
            environment = os.getenv("ENVIRONMENT", "development")

            if environment == "production":
                # Use production database manager for optimal configuration
                from app.core.production_database import production_db_manager

                # Get number of workers from environment
                num_workers = int(os.getenv("GUNICORN_WORKERS", "1"))
                db_max_connections = int(os.getenv("DB_MAX_CONNECTIONS", "100"))

                # Update worker count and create optimized engine
                production_db_manager.num_workers = num_workers
                engine = production_db_manager.create_production_engine(db_max_connections)

                logger.info("Production database engine initialized with optimal pooling")
            else:
                # Development configuration (existing logic)
                engine = create_engine(
                    settings.database_url,
                    # Development pool settings
                    pool_size=5,                     # Smaller pool for development
                    max_overflow=10,                 # Limited overflow
                    pool_pre_ping=True,              # Verify connections before use
                    pool_recycle=3600,               # Recycle connections every hour
                    pool_timeout=30,                 # Wait up to 30 seconds for connection
                    echo=False,                      # Set to True for SQL debugging
                    poolclass=pool.QueuePool,
                    connect_args={
                        "charset": "utf8mb4",
                        "autocommit": False,
                        "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
                    }
                )
                logger.info("Development database engine initialized")

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
    cache = Cache('cache')
    return cache

def get_db_pool_status():
    """Get database connection pool status for monitoring."""
    environment = os.getenv("ENVIRONMENT", "development")

    if environment == "production":
        from app.core.production_database import production_db_manager
        return production_db_manager.get_pool_status()
    else:
        # Development pool status
        engine = get_engine()
        if hasattr(engine, 'pool'):
            pool = engine.pool
            return {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid(),
                "environment": "development"
            }
        return {"error": "Pool information not available"}

def perform_db_health_check():
    """Perform comprehensive database health check."""
    environment = os.getenv("ENVIRONMENT", "development")

    if environment == "production":
        from app.core.production_database import production_db_manager
        return production_db_manager.health_check()
    else:
        # Development health check
        try:
            db = next(get_db())
            from sqlalchemy import text
            result = db.execute(text("SELECT 1 as health_check")).fetchone()
            db.close()

            if result and result.health_check == 1:
                return True, {"status": "healthy", "environment": "development"}
            else:
                return False, {"error": "Health check query failed"}
        except Exception as e:
            return False, {"error": str(e)}

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