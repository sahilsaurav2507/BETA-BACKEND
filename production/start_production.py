#!/usr/bin/env python3
"""
Production Startup Script with Scientific Worker Configuration
==============================================================

This script automatically configures and starts the production server
with scientifically-calculated worker counts and memory budgeting.
"""

import os
import sys
import subprocess
import logging
import argparse
from pathlib import Path

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from production.worker_config import ProductionWorkerCalculator, generate_gunicorn_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProductionServer:
    """Production server manager with scientific worker configuration."""
    
    def __init__(self, app_module: str = "main:app", memory_per_worker: int = 150):
        self.app_module = app_module
        self.memory_per_worker = memory_per_worker
        self.calculator = ProductionWorkerCalculator(memory_per_worker)
        self.config = None
        
    def analyze_system(self):
        """Analyze system and calculate optimal configuration."""
        logger.info("🔍 Analyzing system specifications...")
        
        system_info = self.calculator.get_system_info()
        logger.info("System Information:")
        for key, value in system_info.items():
            logger.info(f"  {key}: {value}")
        
        # Calculate optimal configuration
        self.config = self.calculator.calculate_optimal_workers()
        
        logger.info("📊 Calculated Configuration:")
        logger.info(f"  Workers: {self.config.workers}")
        logger.info(f"  Memory per Worker: {self.config.memory_per_worker_mb}MB")
        logger.info(f"  Total Memory Usage: {self.config.total_memory_usage_mb}MB")
        logger.info(f"  CPU Cores: {self.config.cpu_cores}")
        logger.info(f"  Available Memory: {self.config.available_memory_gb:.2f}GB")
        
        # Validate configuration
        is_valid, warnings = self.calculator.validate_configuration(self.config)
        
        if warnings:
            logger.warning("⚠️  Configuration Warnings:")
            for warning in warnings:
                logger.warning(f"    {warning}")
        
        if is_valid:
            logger.info("✅ Configuration validated successfully")
        else:
            logger.error("❌ Configuration validation failed")
            return False
            
        return True
    
    def generate_configs(self):
        """Generate production configuration files."""
        logger.info("📝 Generating configuration files...")
        
        # Generate Gunicorn config
        generate_gunicorn_config(self.config, "gunicorn.conf.py")
        
        # Create environment-specific configs
        self._create_env_config()
        
        logger.info("✅ Configuration files generated")
    
    def _create_env_config(self):
        """Create environment-specific configuration."""
        env_config = f"""# Production Environment Configuration
# Generated automatically based on system analysis

# Worker Configuration
GUNICORN_WORKERS={self.config.workers}
GUNICORN_WORKER_CLASS={self.config.worker_class}
GUNICORN_BIND={self.config.bind}
GUNICORN_TIMEOUT={self.config.timeout}

# Memory Configuration
MEMORY_PER_WORKER_MB={self.config.memory_per_worker_mb}
TOTAL_MEMORY_USAGE_MB={self.config.total_memory_usage_mb}

# System Information
CPU_CORES={self.config.cpu_cores}
AVAILABLE_MEMORY_GB={self.config.available_memory_gb}

# Database Connection Pool Sizing
# Formula: workers * (pool_size + max_overflow) < db_max_connections
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_MAX_CONNECTIONS={self.config.workers * 30}  # Conservative estimate

# Application Settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=info
"""
        
        with open('.env.production', 'w') as f:
            f.write(env_config)
    
    def start_server(self, dry_run: bool = False):
        """Start the production server with calculated configuration."""
        if not self.config:
            logger.error("Configuration not calculated. Run analyze_system() first.")
            return False
        
        # Build Gunicorn command
        cmd = [
            "gunicorn",
            self.app_module,
            "--workers", str(self.config.workers),
            "--worker-class", self.config.worker_class,
            "--worker-connections", str(self.config.worker_connections),
            "--bind", self.config.bind,
            "--timeout", str(self.config.timeout),
            "--keepalive", str(self.config.keepalive),
            "--max-requests", str(self.config.max_requests),
            "--max-requests-jitter", str(self.config.max_requests_jitter),
            "--preload-app",
            "--access-logfile", "-",
            "--error-logfile", "-",
            "--log-level", "info",
            "--pid", "/tmp/gunicorn.pid"
        ]
        
        logger.info("🚀 Starting production server...")
        logger.info(f"Command: {' '.join(cmd)}")
        
        if dry_run:
            logger.info("🔍 Dry run mode - server not actually started")
            return True
        
        try:
            # Start the server
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to start server: {e}")
            return False
        except KeyboardInterrupt:
            logger.info("🛑 Server stopped by user")
            return True
        
        return True
    
    def health_check(self):
        """Perform health check on the running server."""
        import requests
        import time
        
        logger.info("🏥 Performing health check...")
        
        # Wait for server to start
        time.sleep(2)
        
        try:
            response = requests.get(f"http://localhost:8000/health", timeout=10)
            if response.status_code == 200:
                logger.info("✅ Health check passed")
                return True
            else:
                logger.error(f"❌ Health check failed: HTTP {response.status_code}")
                return False
        except requests.RequestException as e:
            logger.error(f"❌ Health check failed: {e}")
            return False
    
    def show_performance_recommendations(self):
        """Show performance recommendations based on configuration."""
        if not self.config:
            return
        
        logger.info("🎯 Performance Recommendations:")
        
        # Worker recommendations
        if self.config.workers < 4:
            logger.info("  💡 Consider scaling to a larger server for better performance")
        
        # Memory recommendations
        memory_usage_percent = (self.config.total_memory_usage_mb / (self.config.available_memory_gb * 1024)) * 100
        if memory_usage_percent > 60:
            logger.info("  💡 High memory usage detected. Monitor for memory leaks")
        
        # Database connection recommendations
        max_db_connections = self.config.workers * 30  # Conservative estimate
        logger.info(f"  💡 Ensure database max_connections >= {max_db_connections}")
        
        # Load balancer recommendations
        if self.config.workers > 8:
            logger.info("  💡 Consider using a load balancer for better distribution")

def main():
    """Main function with command-line interface."""
    parser = argparse.ArgumentParser(description="Production server with scientific worker configuration")
    parser.add_argument("--app", default="main:app", help="Application module (default: main:app)")
    parser.add_argument("--memory-per-worker", type=int, default=150, 
                       help="Memory per worker in MB (default: 150)")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Analyze and generate configs without starting server")
    parser.add_argument("--config-only", action="store_true",
                       help="Only generate configuration files")
    parser.add_argument("--health-check", action="store_true",
                       help="Perform health check on running server")
    
    args = parser.parse_args()
    
    # Initialize production server
    server = ProductionServer(args.app, args.memory_per_worker)
    
    # Analyze system
    if not server.analyze_system():
        logger.error("❌ System analysis failed")
        sys.exit(1)
    
    # Generate configurations
    server.generate_configs()
    
    # Show performance recommendations
    server.show_performance_recommendations()
    
    if args.config_only:
        logger.info("✅ Configuration files generated successfully")
        return
    
    if args.health_check:
        success = server.health_check()
        sys.exit(0 if success else 1)
    
    # Start server
    success = server.start_server(dry_run=args.dry_run)
    
    if success and not args.dry_run:
        # Perform health check after startup
        server.health_check()
    
    sys.exit(0 if success else 1)

def deploy_production():
    """Complete production deployment with configuration generation."""
    from production.production_config import config_manager

    logger.info("🚀 Starting production deployment...")

    # Initialize production server
    server = ProductionServer()

    # Analyze system and calculate configuration
    if not server.analyze_system():
        logger.error("❌ System analysis failed")
        return False

    # Generate complete production configuration
    logger.info("📋 Generating production configuration...")
    config = config_manager.generate_config(
        workers=server.config.workers,
        db_max_connections=100  # Adjust based on your database
    )

    # Validate configuration
    is_valid, errors = config_manager.validate_config(config)
    if not is_valid:
        logger.error("❌ Configuration validation failed:")
        for error in errors:
            logger.error(f"    {error}")
        return False

    # Save configuration files
    config_manager.save_config(config, "production/production.json")
    config_manager.generate_env_file(config, ".env.production")

    # Generate server configuration files
    server.generate_configs()

    logger.info("✅ Production deployment configuration complete!")
    logger.info("📁 Generated files:")
    logger.info("    - gunicorn.conf.py")
    logger.info("    - .env.production")
    logger.info("    - production/production.json")
    logger.info("    - lawvriksh-api.service")

    logger.info("🎯 Next steps:")
    logger.info("    1. Review generated configuration files")
    logger.info("    2. Set up database with appropriate max_connections")
    logger.info("    3. Configure reverse proxy (Nginx)")
    logger.info("    4. Start the application: python production/start_production.py")

    return True

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "deploy":
        success = deploy_production()
        sys.exit(0 if success else 1)
    else:
        main()
