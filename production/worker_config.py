"""
Scientific Worker Configuration for Production
=============================================

This module provides scientifically-backed worker configuration for Gunicorn
with proper memory budgeting and CPU utilization optimization.

Formula: (2 * CPU cores) + 1
Rationale: One worker processes requests while another waits on I/O operations
"""

import os
import psutil
import logging
from typing import Dict, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class WorkerConfig:
    """Configuration for Gunicorn workers."""
    workers: int
    worker_class: str
    worker_connections: int
    max_requests: int
    max_requests_jitter: int
    timeout: int
    keepalive: int
    preload_app: bool
    bind: str
    memory_per_worker_mb: int
    total_memory_usage_mb: int
    cpu_cores: int
    available_memory_gb: float

class ProductionWorkerCalculator:
    """Calculate optimal worker configuration for production."""
    
    def __init__(self, memory_per_worker_mb: int = 150):
        """
        Initialize worker calculator.
        
        Args:
            memory_per_worker_mb: Estimated memory usage per worker in MB
        """
        self.memory_per_worker_mb = memory_per_worker_mb
        self.cpu_cores = psutil.cpu_count(logical=False)  # Physical cores
        self.logical_cores = psutil.cpu_count(logical=True)  # Logical cores
        self.available_memory_gb = psutil.virtual_memory().total / (1024**3)
        
    def calculate_optimal_workers(self) -> WorkerConfig:
        """
        Calculate optimal number of workers using scientific formula.
        
        Returns:
            WorkerConfig: Optimized worker configuration
        """
        # Scientific formula: (2 * CPU cores) + 1
        optimal_workers = (2 * self.cpu_cores) + 1
        
        # Memory constraint check
        total_memory_needed_mb = optimal_workers * self.memory_per_worker_mb
        available_memory_mb = self.available_memory_gb * 1024 * 0.8  # Use 80% of available memory
        
        if total_memory_needed_mb > available_memory_mb:
            # Reduce workers to fit memory constraints
            max_workers_by_memory = int(available_memory_mb // self.memory_per_worker_mb)
            optimal_workers = min(optimal_workers, max_workers_by_memory)
            
            logger.warning(
                f"Memory constraint detected. Reducing workers from "
                f"{(2 * self.cpu_cores) + 1} to {optimal_workers}"
            )
        
        # Ensure minimum of 2 workers
        optimal_workers = max(2, optimal_workers)
        
        return WorkerConfig(
            workers=optimal_workers,
            worker_class="uvicorn.workers.UvicornWorker",
            worker_connections=1000,  # Connections per worker
            max_requests=1000,        # Restart worker after N requests
            max_requests_jitter=100,  # Add randomness to prevent thundering herd
            timeout=30,               # Worker timeout in seconds
            keepalive=5,              # Keep-alive timeout
            preload_app=True,         # Preload application for better performance
            bind="0.0.0.0:8000",     # Bind address
            memory_per_worker_mb=self.memory_per_worker_mb,
            total_memory_usage_mb=optimal_workers * self.memory_per_worker_mb,
            cpu_cores=self.cpu_cores,
            available_memory_gb=self.available_memory_gb
        )
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get detailed system information for configuration decisions."""
        memory = psutil.virtual_memory()
        
        return {
            "cpu_cores_physical": self.cpu_cores,
            "cpu_cores_logical": self.logical_cores,
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "memory_percent_used": memory.percent,
            "cpu_frequency_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else "Unknown",
            "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else "Unknown"
        }
    
    def validate_configuration(self, config: WorkerConfig) -> Tuple[bool, list]:
        """
        Validate the worker configuration against system constraints.
        
        Args:
            config: Worker configuration to validate
            
        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        warnings = []
        is_valid = True
        
        # Check memory constraints
        total_memory_mb = config.workers * config.memory_per_worker_mb
        available_memory_mb = self.available_memory_gb * 1024 * 0.8
        
        if total_memory_mb > available_memory_mb:
            warnings.append(
                f"Memory usage ({total_memory_mb}MB) exceeds 80% of available memory "
                f"({available_memory_mb:.0f}MB). Consider reducing workers."
            )
            is_valid = False
        
        # Check CPU utilization
        if config.workers > self.logical_cores * 2:
            warnings.append(
                f"Worker count ({config.workers}) is very high compared to logical cores "
                f"({self.logical_cores}). This may cause context switching overhead."
            )
        
        # Check if workers are too few
        if config.workers < 2:
            warnings.append("Using less than 2 workers reduces fault tolerance.")
        
        # Check timeout settings
        if config.timeout < 30:
            warnings.append("Timeout less than 30 seconds may cause premature worker kills.")
        
        return is_valid, warnings

def generate_gunicorn_config(config: WorkerConfig, output_file: str = "gunicorn.conf.py"):
    """
    Generate Gunicorn configuration file.
    
    Args:
        config: Worker configuration
        output_file: Output configuration file path
    """
    config_content = f'''"""
Gunicorn Configuration for Production
Generated automatically based on system specifications
"""

import multiprocessing
import os

# Server socket
bind = "{config.bind}"
backlog = 2048

# Worker processes
workers = {config.workers}
worker_class = "{config.worker_class}"
worker_connections = {config.worker_connections}
max_requests = {config.max_requests}
max_requests_jitter = {config.max_requests_jitter}
preload_app = {config.preload_app}

# Timeout
timeout = {config.timeout}
keepalive = {config.keepalive}
graceful_timeout = 30

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%%(h)s %%(l)s %%(u)s %%(t)s "%%(r)s" %%(s)s %%(b)s "%%(f)s" "%%(a)s" %%(D)s'

# Process naming
proc_name = "lawvriksh-api"

# Server mechanics
daemon = False
pidfile = "/tmp/gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Worker configuration based on system specs:
# CPU Cores: {config.cpu_cores}
# Memory per worker: {config.memory_per_worker_mb}MB
# Total memory usage: {config.total_memory_usage_mb}MB
# Available memory: {config.available_memory_gb:.2f}GB

def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_worker_init(worker):
    worker.log.info("Worker initialized (pid: %s)", worker.pid)

def worker_abort(worker):
    worker.log.info("Worker received SIGABRT signal")
'''
    
    # Write configuration file
    with open(output_file, 'w') as f:
        f.write(config_content)
    
    logger.info(f"Gunicorn configuration written to {output_file}")

def generate_systemd_service(config: WorkerConfig, 
                           app_path: str = "/app",
                           user: str = "www-data",
                           output_file: str = "lawvriksh-api.service"):
    """
    Generate systemd service file for production deployment.
    
    Args:
        config: Worker configuration
        app_path: Application path
        user: System user to run the service
        output_file: Output service file path
    """
    service_content = f'''[Unit]
Description=LawVriksh Referral Platform API
After=network.target mysql.service
Requires=mysql.service

[Service]
Type=notify
User={user}
Group={user}
WorkingDirectory={app_path}
Environment=PATH={app_path}/venv/bin
Environment=PYTHONPATH={app_path}
ExecStart={app_path}/venv/bin/gunicorn main:app --config gunicorn.conf.py
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

# Security settings
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths={app_path}/logs {app_path}/tmp

[Install]
WantedBy=multi-user.target
'''
    
    with open(output_file, 'w') as f:
        f.write(service_content)
    
    logger.info(f"Systemd service file written to {output_file}")

def main():
    """Main function to generate production configuration."""
    # Initialize calculator
    calculator = ProductionWorkerCalculator(memory_per_worker_mb=150)
    
    # Get system information
    system_info = calculator.get_system_info()
    print("=== System Information ===")
    for key, value in system_info.items():
        print(f"{key}: {value}")
    
    # Calculate optimal configuration
    config = calculator.calculate_optimal_workers()
    
    print(f"\n=== Recommended Configuration ===")
    print(f"Workers: {config.workers}")
    print(f"Worker Class: {config.worker_class}")
    print(f"Memory per Worker: {config.memory_per_worker_mb}MB")
    print(f"Total Memory Usage: {config.total_memory_usage_mb}MB")
    print(f"CPU Cores: {config.cpu_cores}")
    print(f"Available Memory: {config.available_memory_gb:.2f}GB")
    
    # Validate configuration
    is_valid, warnings = calculator.validate_configuration(config)
    
    if warnings:
        print(f"\n=== Configuration Warnings ===")
        for warning in warnings:
            print(f"⚠️  {warning}")
    
    if is_valid:
        print(f"\n✅ Configuration is valid and ready for production")
    else:
        print(f"\n❌ Configuration needs adjustment before production use")
    
    # Generate configuration files
    print(f"\n=== Generating Configuration Files ===")
    generate_gunicorn_config(config)
    generate_systemd_service(config)
    
    print(f"\n=== Gunicorn Command ===")
    print(f"gunicorn main:app --workers {config.workers} --worker-class {config.worker_class} --bind {config.bind}")

if __name__ == "__main__":
    main()
