"""
Production Database Connection Pooling
======================================

This module provides scientifically-optimized database connection pooling
for production environments with proper sizing calculations and monitoring.

Key Formula: num_workers * (pool_size + max_overflow) < db_max_connections
"""

import os
import logging
import time
from typing import Dict, Any, Optional, Tuple
from contextlib import contextmanager
from dataclasses import dataclass
from sqlalchemy import create_engine, event, text, pool
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool, StaticPool
import psutil

logger = logging.getLogger(__name__)

@dataclass
class PoolConfig:
    """Database connection pool configuration."""
    pool_size: int
    max_overflow: int
    pool_timeout: int
    pool_recycle: int
    pool_pre_ping: bool
    pool_reset_on_return: str
    total_connections: int
    workers: int
    connections_per_worker: int

class ProductionDatabaseManager:
    """Production-optimized database connection manager."""
    
    def __init__(self, database_url: str, num_workers: int = 1):
        self.database_url = database_url
        self.num_workers = num_workers
        self.engine: Optional[Engine] = None
        self.session_factory: Optional[sessionmaker] = None
        self.pool_config: Optional[PoolConfig] = None
        self._connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "pool_hits": 0,
            "pool_misses": 0,
            "connection_errors": 0,
            "slow_queries": 0
        }
    
    def calculate_optimal_pool_size(self, db_max_connections: int = 100) -> PoolConfig:
        """
        Calculate optimal connection pool size based on workers and database limits.
        
        Args:
            db_max_connections: Maximum connections allowed by database
            
        Returns:
            PoolConfig: Optimized pool configuration
        """
        # Conservative approach: leave 20% headroom for other connections
        available_connections = int(db_max_connections * 0.8)
        
        # Calculate connections per worker
        connections_per_worker = available_connections // self.num_workers
        
        # Ensure minimum viable pool size
        min_pool_size = 5
        max_pool_size = min(20, connections_per_worker)  # Cap at 20 per worker
        
        # Calculate pool_size and max_overflow
        if connections_per_worker >= 15:
            pool_size = 10
            max_overflow = min(10, connections_per_worker - pool_size)
        elif connections_per_worker >= 10:
            pool_size = 8
            max_overflow = connections_per_worker - pool_size
        else:
            pool_size = max(min_pool_size, connections_per_worker // 2)
            max_overflow = max(2, connections_per_worker - pool_size)
        
        total_connections = self.num_workers * (pool_size + max_overflow)
        
        # Validate against database limits
        if total_connections > available_connections:
            logger.warning(
                f"Calculated connections ({total_connections}) exceed available "
                f"({available_connections}). Reducing pool size."
            )
            # Recalculate with stricter limits
            pool_size = max(3, available_connections // (self.num_workers * 2))
            max_overflow = max(2, (available_connections // self.num_workers) - pool_size)
            total_connections = self.num_workers * (pool_size + max_overflow)
        
        config = PoolConfig(
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=30,          # Wait up to 30 seconds for connection
            pool_recycle=3600,        # Recycle connections every hour
            pool_pre_ping=True,       # Verify connections before use
            pool_reset_on_return='commit',  # Reset connections on return
            total_connections=total_connections,
            workers=self.num_workers,
            connections_per_worker=pool_size + max_overflow
        )
        
        self.pool_config = config
        return config
    
    def create_production_engine(self, db_max_connections: int = 100) -> Engine:
        """
        Create production-optimized SQLAlchemy engine.
        
        Args:
            db_max_connections: Maximum database connections
            
        Returns:
            Engine: Configured SQLAlchemy engine
        """
        if not self.pool_config:
            self.calculate_optimal_pool_size(db_max_connections)
        
        config = self.pool_config
        
        logger.info(f"Creating production database engine:")
        logger.info(f"  Workers: {config.workers}")
        logger.info(f"  Pool size: {config.pool_size}")
        logger.info(f"  Max overflow: {config.max_overflow}")
        logger.info(f"  Total connections: {config.total_connections}")
        logger.info(f"  Connections per worker: {config.connections_per_worker}")
        
        # Create engine with optimized settings
        self.engine = create_engine(
            self.database_url,
            
            # Connection pool settings
            poolclass=QueuePool,
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
            pool_timeout=config.pool_timeout,
            pool_recycle=config.pool_recycle,
            pool_pre_ping=config.pool_pre_ping,
            pool_reset_on_return=config.pool_reset_on_return,
            
            # Engine options for production
            echo=False,  # Disable SQL logging in production
            echo_pool=False,  # Disable pool logging
            future=True,  # Use SQLAlchemy 2.0 style
            
            # Connection arguments for MySQL optimization
            connect_args={
                "charset": "utf8mb4",
                "autocommit": False,
                "connect_timeout": 10,
                "read_timeout": 30,
                "write_timeout": 30,
                # MySQL-specific optimizations
                "init_command": (
                    "SET sql_mode='STRICT_TRANS_TABLES',"
                    "SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED,"
                    "SESSION wait_timeout=28800,"
                    "SESSION interactive_timeout=28800"
                ),
            }
        )
        
        # Set up event listeners for monitoring
        self._setup_event_listeners()
        
        # Create session factory
        self.session_factory = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )
        
        return self.engine
    
    def _setup_event_listeners(self):
        """Set up SQLAlchemy event listeners for monitoring."""
        
        @event.listens_for(self.engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            """Track new connections."""
            self._connection_stats["total_connections"] += 1
            logger.debug("New database connection established")
        
        @event.listens_for(self.engine, "checkout")
        def on_checkout(dbapi_connection, connection_record, connection_proxy):
            """Track connection checkouts."""
            self._connection_stats["active_connections"] += 1
            self._connection_stats["pool_hits"] += 1
        
        @event.listens_for(self.engine, "checkin")
        def on_checkin(dbapi_connection, connection_record):
            """Track connection checkins."""
            self._connection_stats["active_connections"] -= 1
        
        @event.listens_for(self.engine, "invalidate")
        def on_invalidate(dbapi_connection, connection_record, exception):
            """Track connection invalidations."""
            self._connection_stats["connection_errors"] += 1
            logger.warning(f"Database connection invalidated: {exception}")
        
        @event.listens_for(self.engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Track query start time."""
            context._query_start_time = time.time()
        
        @event.listens_for(self.engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Track slow queries."""
            if hasattr(context, '_query_start_time'):
                execution_time = time.time() - context._query_start_time
                if execution_time > 1.0:  # Log queries slower than 1 second
                    self._connection_stats["slow_queries"] += 1
                    logger.warning(f"Slow query ({execution_time:.2f}s): {statement[:100]}...")
    
    @contextmanager
    def get_session(self):
        """
        Get database session with proper error handling and cleanup.
        
        Yields:
            Session: SQLAlchemy database session
        """
        if not self.session_factory:
            raise RuntimeError("Database engine not initialized. Call create_production_engine() first.")
        
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def get_pool_status(self) -> Dict[str, Any]:
        """
        Get current connection pool status.
        
        Returns:
            Dict: Pool status information
        """
        if not self.engine:
            return {"error": "Engine not initialized"}
        
        pool = self.engine.pool
        
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
            "total_capacity": pool.size() + pool.overflow(),
            "utilization_percent": round(
                (pool.checkedout() / (pool.size() + pool.overflow())) * 100, 2
            ) if (pool.size() + pool.overflow()) > 0 else 0,
            "connection_stats": self._connection_stats.copy()
        }
    
    def health_check(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Perform database health check.
        
        Returns:
            Tuple: (is_healthy, health_info)
        """
        if not self.engine:
            return False, {"error": "Engine not initialized"}
        
        try:
            with self.get_session() as session:
                # Simple query to test connection
                result = session.execute(text("SELECT 1 as health_check")).fetchone()
                
                if result and result.health_check == 1:
                    pool_status = self.get_pool_status()
                    return True, {
                        "status": "healthy",
                        "pool_status": pool_status,
                        "timestamp": time.time()
                    }
                else:
                    return False, {"error": "Health check query failed"}
                    
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False, {"error": str(e)}
    
    def optimize_for_workload(self, workload_type: str = "mixed"):
        """
        Optimize database settings for specific workload types.
        
        Args:
            workload_type: Type of workload (read_heavy, write_heavy, mixed)
        """
        if not self.engine:
            logger.error("Engine not initialized")
            return
        
        optimization_queries = {
            "read_heavy": [
                "SET SESSION query_cache_type = ON",
                "SET SESSION query_cache_size = 67108864",  # 64MB
                "SET SESSION read_buffer_size = 2097152",   # 2MB
            ],
            "write_heavy": [
                "SET SESSION innodb_flush_log_at_trx_commit = 2",
                "SET SESSION sync_binlog = 0",
                "SET SESSION bulk_insert_buffer_size = 8388608",  # 8MB
            ],
            "mixed": [
                "SET SESSION query_cache_type = ON",
                "SET SESSION innodb_buffer_pool_size = 134217728",  # 128MB
            ]
        }
        
        queries = optimization_queries.get(workload_type, optimization_queries["mixed"])
        
        try:
            with self.get_session() as session:
                for query in queries:
                    session.execute(text(query))
                logger.info(f"Database optimized for {workload_type} workload")
        except Exception as e:
            logger.error(f"Failed to optimize database for {workload_type}: {e}")

# Global production database manager
production_db_manager = ProductionDatabaseManager(
    database_url=os.getenv("DATABASE_URL", "mysql+pymysql://user:pass@localhost/db"),
    num_workers=int(os.getenv("GUNICORN_WORKERS", "1"))
)
