"""
Production Environment Configuration
===================================

This module provides comprehensive production environment configuration
with automatic optimization based on system resources and deployment requirements.
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import json

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database configuration for production."""
    url: str
    pool_size: int
    max_overflow: int
    pool_timeout: int
    pool_recycle: int
    max_connections: int
    connection_timeout: int
    query_timeout: int

@dataclass
class RedisConfig:
    """Redis configuration for caching and sessions."""
    url: str
    max_connections: int
    socket_timeout: int
    socket_connect_timeout: int
    retry_on_timeout: bool
    health_check_interval: int

@dataclass
class SecurityConfig:
    """Security configuration for production."""
    secret_key: str
    jwt_secret_key: str
    jwt_algorithm: str
    jwt_expire_minutes: int
    cors_origins: list
    allowed_hosts: list
    rate_limit_per_minute: int
    max_request_size: int

@dataclass
class LoggingConfig:
    """Logging configuration for production."""
    level: str
    format: str
    file_path: str
    max_file_size: int
    backup_count: int
    json_format: bool

@dataclass
class ProductionConfig:
    """Complete production configuration."""
    environment: str
    debug: bool
    testing: bool
    workers: int
    worker_class: str
    bind: str
    timeout: int
    database: DatabaseConfig
    redis: RedisConfig
    security: SecurityConfig
    logging: LoggingConfig
    monitoring: Dict[str, Any]

class ProductionConfigManager:
    """Manages production configuration with environment-based optimization."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "production.json"
        self.config: Optional[ProductionConfig] = None
        
    def generate_config(self, 
                       workers: int,
                       db_max_connections: int = 100,
                       redis_url: Optional[str] = None) -> ProductionConfig:
        """
        Generate optimized production configuration.
        
        Args:
            workers: Number of Gunicorn workers
            db_max_connections: Maximum database connections
            redis_url: Redis connection URL
            
        Returns:
            ProductionConfig: Complete production configuration
        """
        # Database configuration
        database_url = os.getenv("DATABASE_URL", "mysql+pymysql://user:pass@localhost/lawvriksh")
        
        # Calculate optimal database pool settings
        connections_per_worker = db_max_connections // workers
        pool_size = min(10, max(5, connections_per_worker // 2))
        max_overflow = min(20, max(5, connections_per_worker - pool_size))
        
        database_config = DatabaseConfig(
            url=database_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=30,
            pool_recycle=3600,
            max_connections=db_max_connections,
            connection_timeout=10,
            query_timeout=30
        )
        
        # Redis configuration
        redis_config = RedisConfig(
            url=redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            max_connections=workers * 10,  # 10 connections per worker
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30
        )
        
        # Security configuration
        security_config = SecurityConfig(
            secret_key=os.getenv("SECRET_KEY", self._generate_secret_key()),
            jwt_secret_key=os.getenv("JWT_SECRET_KEY", self._generate_secret_key()),
            jwt_algorithm="HS256",
            jwt_expire_minutes=int(os.getenv("JWT_EXPIRE_MINUTES", "1440")),  # 24 hours
            cors_origins=self._parse_list(os.getenv("CORS_ORIGINS", "*")),
            allowed_hosts=self._parse_list(os.getenv("ALLOWED_HOSTS", "*")),
            rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
            max_request_size=int(os.getenv("MAX_REQUEST_SIZE", "16777216"))  # 16MB
        )
        
        # Logging configuration
        logging_config = LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            file_path=os.getenv("LOG_FILE", "/var/log/lawvriksh/app.log"),
            max_file_size=int(os.getenv("LOG_MAX_FILE_SIZE", "104857600")),  # 100MB
            backup_count=int(os.getenv("LOG_BACKUP_COUNT", "5")),
            json_format=os.getenv("LOG_JSON_FORMAT", "true").lower() == "true"
        )
        
        # Monitoring configuration
        monitoring_config = {
            "prometheus_enabled": os.getenv("PROMETHEUS_ENABLED", "true").lower() == "true",
            "prometheus_port": int(os.getenv("PROMETHEUS_PORT", "9090")),
            "health_check_interval": int(os.getenv("HEALTH_CHECK_INTERVAL", "30")),
            "metrics_retention_days": int(os.getenv("METRICS_RETENTION_DAYS", "7")),
            "alert_webhook_url": os.getenv("ALERT_WEBHOOK_URL"),
            "sentry_dsn": os.getenv("SENTRY_DSN"),
            "datadog_api_key": os.getenv("DATADOG_API_KEY")
        }
        
        # Complete configuration
        self.config = ProductionConfig(
            environment="production",
            debug=False,
            testing=False,
            workers=workers,
            worker_class="uvicorn.workers.UvicornWorker",
            bind=os.getenv("BIND_ADDRESS", "0.0.0.0:8000"),
            timeout=int(os.getenv("WORKER_TIMEOUT", "30")),
            database=database_config,
            redis=redis_config,
            security=security_config,
            logging=logging_config,
            monitoring=monitoring_config
        )
        
        return self.config
    
    def save_config(self, config: ProductionConfig, file_path: Optional[str] = None):
        """Save configuration to JSON file."""
        file_path = file_path or self.config_file
        
        # Convert to dictionary
        config_dict = asdict(config)
        
        # Create directory if it doesn't exist
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save to file
        with open(file_path, 'w') as f:
            json.dump(config_dict, f, indent=2, default=str)
        
        logger.info(f"Production configuration saved to {file_path}")
    
    def load_config(self, file_path: Optional[str] = None) -> ProductionConfig:
        """Load configuration from JSON file."""
        file_path = file_path or self.config_file
        
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            config_dict = json.load(f)
        
        # Reconstruct nested objects
        config_dict['database'] = DatabaseConfig(**config_dict['database'])
        config_dict['redis'] = RedisConfig(**config_dict['redis'])
        config_dict['security'] = SecurityConfig(**config_dict['security'])
        config_dict['logging'] = LoggingConfig(**config_dict['logging'])
        
        self.config = ProductionConfig(**config_dict)
        return self.config
    
    def generate_env_file(self, config: ProductionConfig, file_path: str = ".env.production"):
        """Generate environment file from configuration."""
        env_content = f"""# Production Environment Configuration
# Generated automatically - DO NOT EDIT MANUALLY

# Application Settings
ENVIRONMENT=production
DEBUG=false
TESTING=false

# Server Configuration
GUNICORN_WORKERS={config.workers}
GUNICORN_WORKER_CLASS={config.worker_class}
BIND_ADDRESS={config.bind}
WORKER_TIMEOUT={config.timeout}

# Database Configuration
DATABASE_URL={config.database.url}
DB_POOL_SIZE={config.database.pool_size}
DB_MAX_OVERFLOW={config.database.max_overflow}
DB_POOL_TIMEOUT={config.database.pool_timeout}
DB_POOL_RECYCLE={config.database.pool_recycle}
DB_MAX_CONNECTIONS={config.database.max_connections}

# Redis Configuration
REDIS_URL={config.redis.url}
REDIS_MAX_CONNECTIONS={config.redis.max_connections}

# Security Configuration
SECRET_KEY={config.security.secret_key}
JWT_SECRET_KEY={config.security.jwt_secret_key}
JWT_ALGORITHM={config.security.jwt_algorithm}
JWT_EXPIRE_MINUTES={config.security.jwt_expire_minutes}
CORS_ORIGINS={','.join(config.security.cors_origins)}
ALLOWED_HOSTS={','.join(config.security.allowed_hosts)}
RATE_LIMIT_PER_MINUTE={config.security.rate_limit_per_minute}

# Logging Configuration
LOG_LEVEL={config.logging.level}
LOG_FILE={config.logging.file_path}
LOG_MAX_FILE_SIZE={config.logging.max_file_size}
LOG_BACKUP_COUNT={config.logging.backup_count}
LOG_JSON_FORMAT={str(config.logging.json_format).lower()}

# Monitoring Configuration
PROMETHEUS_ENABLED={str(config.monitoring['prometheus_enabled']).lower()}
PROMETHEUS_PORT={config.monitoring['prometheus_port']}
HEALTH_CHECK_INTERVAL={config.monitoring['health_check_interval']}
METRICS_RETENTION_DAYS={config.monitoring['metrics_retention_days']}
"""
        
        # Add optional monitoring settings
        if config.monitoring.get('alert_webhook_url'):
            env_content += f"ALERT_WEBHOOK_URL={config.monitoring['alert_webhook_url']}\n"
        if config.monitoring.get('sentry_dsn'):
            env_content += f"SENTRY_DSN={config.monitoring['sentry_dsn']}\n"
        if config.monitoring.get('datadog_api_key'):
            env_content += f"DATADOG_API_KEY={config.monitoring['datadog_api_key']}\n"
        
        with open(file_path, 'w') as f:
            f.write(env_content)
        
        logger.info(f"Environment file generated: {file_path}")
    
    def validate_config(self, config: ProductionConfig) -> tuple[bool, list]:
        """Validate production configuration."""
        errors = []
        
        # Validate database configuration
        if config.database.pool_size < 1:
            errors.append("Database pool_size must be at least 1")
        
        if config.database.max_overflow < 0:
            errors.append("Database max_overflow cannot be negative")
        
        total_db_connections = config.workers * (config.database.pool_size + config.database.max_overflow)
        if total_db_connections > config.database.max_connections:
            errors.append(
                f"Total database connections ({total_db_connections}) exceed "
                f"max_connections ({config.database.max_connections})"
            )
        
        # Validate security configuration
        if len(config.security.secret_key) < 32:
            errors.append("SECRET_KEY must be at least 32 characters long")
        
        if len(config.security.jwt_secret_key) < 32:
            errors.append("JWT_SECRET_KEY must be at least 32 characters long")
        
        # Validate worker configuration
        if config.workers < 1:
            errors.append("Workers count must be at least 1")
        
        return len(errors) == 0, errors
    
    def _generate_secret_key(self) -> str:
        """Generate a secure secret key."""
        import secrets
        return secrets.token_urlsafe(32)
    
    def _parse_list(self, value: str) -> list:
        """Parse comma-separated string into list."""
        if not value or value == "*":
            return ["*"]
        return [item.strip() for item in value.split(",")]

# Global configuration manager
config_manager = ProductionConfigManager()
