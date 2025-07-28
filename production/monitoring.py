"""
Production Monitoring and Health Checks
=======================================

This module provides comprehensive monitoring, logging, and health check
capabilities for the production environment.
"""

import os
import time
import logging
import psutil
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import requests
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System performance metrics."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    load_average: List[float]
    network_io: Dict[str, int]
    process_count: int

@dataclass
class ApplicationMetrics:
    """Application-specific metrics."""
    timestamp: datetime
    active_connections: int
    request_count: int
    response_time_avg: float
    error_rate: float
    database_connections: int
    cache_hit_rate: float
    worker_status: Dict[str, Any]

@dataclass
class HealthCheckResult:
    """Health check result."""
    service: str
    status: str  # healthy, unhealthy, degraded
    response_time: float
    details: Dict[str, Any]
    timestamp: datetime

class ProductionMonitor:
    """Comprehensive production monitoring system."""
    
    def __init__(self, app_url: str = "http://localhost:8000"):
        self.app_url = app_url
        self.metrics_history: List[SystemMetrics] = []
        self.app_metrics_history: List[ApplicationMetrics] = []
        self.health_checks: List[HealthCheckResult] = []
        self.alert_thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_percent": 90.0,
            "response_time": 2.0,
            "error_rate": 5.0,
            "database_connections": 80  # Percentage of max connections
        }
        
    def collect_system_metrics(self) -> SystemMetrics:
        """Collect system performance metrics."""
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        memory_used_gb = memory.used / (1024**3)
        memory_total_gb = memory.total / (1024**3)
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_used_gb = disk.used / (1024**3)
        disk_total_gb = disk.total / (1024**3)
        
        # Load average
        load_avg = list(os.getloadavg()) if hasattr(os, 'getloadavg') else [0.0, 0.0, 0.0]
        
        # Network I/O
        network = psutil.net_io_counters()
        network_io = {
            "bytes_sent": network.bytes_sent,
            "bytes_recv": network.bytes_recv,
            "packets_sent": network.packets_sent,
            "packets_recv": network.packets_recv
        }
        
        # Process count
        process_count = len(psutil.pids())
        
        metrics = SystemMetrics(
            timestamp=datetime.utcnow(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_gb=round(memory_used_gb, 2),
            memory_total_gb=round(memory_total_gb, 2),
            disk_percent=disk.percent,
            disk_used_gb=round(disk_used_gb, 2),
            disk_total_gb=round(disk_total_gb, 2),
            load_average=load_avg,
            network_io=network_io,
            process_count=process_count
        )
        
        # Store metrics (keep last 1000 entries)
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > 1000:
            self.metrics_history.pop(0)
            
        return metrics
    
    def collect_application_metrics(self) -> Optional[ApplicationMetrics]:
        """Collect application-specific metrics."""
        try:
            # Get application performance stats
            response = requests.get(f"{self.app_url}/performance-stats", timeout=5)
            if response.status_code == 200:
                stats = response.json()
                
                # Extract metrics from response
                db_stats = stats.get("db_pool_stats", {})
                cache_stats = stats.get("cache_stats", {})
                
                metrics = ApplicationMetrics(
                    timestamp=datetime.utcnow(),
                    active_connections=db_stats.get("checked_out", 0),
                    request_count=stats.get("total_requests", 0),
                    response_time_avg=stats.get("avg_response_time", 0.0),
                    error_rate=stats.get("error_rate", 0.0),
                    database_connections=db_stats.get("utilization_percent", 0),
                    cache_hit_rate=cache_stats.get("hit_rate", 0.0),
                    worker_status=stats.get("worker_status", {})
                )
                
                # Store metrics
                self.app_metrics_history.append(metrics)
                if len(self.app_metrics_history) > 1000:
                    self.app_metrics_history.pop(0)
                    
                return metrics
                
        except Exception as e:
            logger.error(f"Failed to collect application metrics: {e}")
            
        return None
    
    def perform_health_checks(self) -> List[HealthCheckResult]:
        """Perform comprehensive health checks."""
        health_results = []
        
        # Application health check
        app_health = self._check_application_health()
        health_results.append(app_health)
        
        # Database health check
        db_health = self._check_database_health()
        health_results.append(db_health)
        
        # Redis health check
        redis_health = self._check_redis_health()
        health_results.append(redis_health)
        
        # Nginx health check
        nginx_health = self._check_nginx_health()
        health_results.append(nginx_health)
        
        # Store health check results
        self.health_checks.extend(health_results)
        if len(self.health_checks) > 1000:
            self.health_checks = self.health_checks[-1000:]
            
        return health_results
    
    def _check_application_health(self) -> HealthCheckResult:
        """Check application health."""
        start_time = time.time()
        
        try:
            response = requests.get(f"{self.app_url}/health", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                return HealthCheckResult(
                    service="application",
                    status="healthy",
                    response_time=response_time,
                    details={"status_code": 200, "response": response.json()},
                    timestamp=datetime.utcnow()
                )
            else:
                return HealthCheckResult(
                    service="application",
                    status="unhealthy",
                    response_time=response_time,
                    details={"status_code": response.status_code, "error": "Non-200 response"},
                    timestamp=datetime.utcnow()
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheckResult(
                service="application",
                status="unhealthy",
                response_time=response_time,
                details={"error": str(e)},
                timestamp=datetime.utcnow()
            )
    
    def _check_database_health(self) -> HealthCheckResult:
        """Check database health."""
        start_time = time.time()
        
        try:
            # Use application's database health check endpoint
            response = requests.get(f"{self.app_url}/debug-db-health", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    return HealthCheckResult(
                        service="database",
                        status="healthy",
                        response_time=response_time,
                        details=data,
                        timestamp=datetime.utcnow()
                    )
                else:
                    return HealthCheckResult(
                        service="database",
                        status="unhealthy",
                        response_time=response_time,
                        details=data,
                        timestamp=datetime.utcnow()
                    )
            else:
                return HealthCheckResult(
                    service="database",
                    status="unhealthy",
                    response_time=response_time,
                    details={"status_code": response.status_code},
                    timestamp=datetime.utcnow()
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheckResult(
                service="database",
                status="unhealthy",
                response_time=response_time,
                details={"error": str(e)},
                timestamp=datetime.utcnow()
            )
    
    def _check_redis_health(self) -> HealthCheckResult:
        """Check Redis health."""
        start_time = time.time()
        
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=5)
            r.ping()
            response_time = time.time() - start_time
            
            # Get Redis info
            info = r.info()
            
            return HealthCheckResult(
                service="redis",
                status="healthy",
                response_time=response_time,
                details={
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory_human": info.get("used_memory_human", "0B"),
                    "uptime_in_seconds": info.get("uptime_in_seconds", 0)
                },
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheckResult(
                service="redis",
                status="unhealthy",
                response_time=response_time,
                details={"error": str(e)},
                timestamp=datetime.utcnow()
            )
    
    def _check_nginx_health(self) -> HealthCheckResult:
        """Check Nginx health."""
        start_time = time.time()
        
        try:
            # Check if Nginx is running
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] == 'nginx':
                    response_time = time.time() - start_time
                    return HealthCheckResult(
                        service="nginx",
                        status="healthy",
                        response_time=response_time,
                        details={"pid": proc.info['pid'], "status": "running"},
                        timestamp=datetime.utcnow()
                    )
            
            # Nginx not found
            response_time = time.time() - start_time
            return HealthCheckResult(
                service="nginx",
                status="unhealthy",
                response_time=response_time,
                details={"error": "Nginx process not found"},
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheckResult(
                service="nginx",
                status="unhealthy",
                response_time=response_time,
                details={"error": str(e)},
                timestamp=datetime.utcnow()
            )
    
    def check_alerts(self, system_metrics: SystemMetrics, 
                    app_metrics: Optional[ApplicationMetrics] = None) -> List[Dict[str, Any]]:
        """Check for alert conditions."""
        alerts = []
        
        # System alerts
        if system_metrics.cpu_percent > self.alert_thresholds["cpu_percent"]:
            alerts.append({
                "type": "system",
                "severity": "warning",
                "metric": "cpu_percent",
                "value": system_metrics.cpu_percent,
                "threshold": self.alert_thresholds["cpu_percent"],
                "message": f"High CPU usage: {system_metrics.cpu_percent:.1f}%"
            })
        
        if system_metrics.memory_percent > self.alert_thresholds["memory_percent"]:
            alerts.append({
                "type": "system",
                "severity": "warning",
                "metric": "memory_percent",
                "value": system_metrics.memory_percent,
                "threshold": self.alert_thresholds["memory_percent"],
                "message": f"High memory usage: {system_metrics.memory_percent:.1f}%"
            })
        
        if system_metrics.disk_percent > self.alert_thresholds["disk_percent"]:
            alerts.append({
                "type": "system",
                "severity": "critical",
                "metric": "disk_percent",
                "value": system_metrics.disk_percent,
                "threshold": self.alert_thresholds["disk_percent"],
                "message": f"High disk usage: {system_metrics.disk_percent:.1f}%"
            })
        
        # Application alerts
        if app_metrics:
            if app_metrics.response_time_avg > self.alert_thresholds["response_time"]:
                alerts.append({
                    "type": "application",
                    "severity": "warning",
                    "metric": "response_time",
                    "value": app_metrics.response_time_avg,
                    "threshold": self.alert_thresholds["response_time"],
                    "message": f"High response time: {app_metrics.response_time_avg:.2f}s"
                })
            
            if app_metrics.error_rate > self.alert_thresholds["error_rate"]:
                alerts.append({
                    "type": "application",
                    "severity": "critical",
                    "metric": "error_rate",
                    "value": app_metrics.error_rate,
                    "threshold": self.alert_thresholds["error_rate"],
                    "message": f"High error rate: {app_metrics.error_rate:.1f}%"
                })
        
        return alerts
    
    def generate_monitoring_report(self) -> Dict[str, Any]:
        """Generate comprehensive monitoring report."""
        # Get latest metrics
        system_metrics = self.collect_system_metrics()
        app_metrics = self.collect_application_metrics()
        health_checks = self.perform_health_checks()
        alerts = self.check_alerts(system_metrics, app_metrics)
        
        # Calculate trends (last 10 minutes)
        recent_time = datetime.utcnow() - timedelta(minutes=10)
        recent_system_metrics = [
            m for m in self.metrics_history 
            if m.timestamp > recent_time
        ]
        
        # System trends
        system_trends = {}
        if recent_system_metrics:
            system_trends = {
                "cpu_trend": self._calculate_trend([m.cpu_percent for m in recent_system_metrics]),
                "memory_trend": self._calculate_trend([m.memory_percent for m in recent_system_metrics]),
                "disk_trend": self._calculate_trend([m.disk_percent for m in recent_system_metrics])
            }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system_metrics": asdict(system_metrics),
            "application_metrics": asdict(app_metrics) if app_metrics else None,
            "health_checks": [asdict(hc) for hc in health_checks],
            "alerts": alerts,
            "system_trends": system_trends,
            "summary": {
                "overall_status": "healthy" if not alerts else "warning" if any(a["severity"] == "warning" for a in alerts) else "critical",
                "total_alerts": len(alerts),
                "services_healthy": sum(1 for hc in health_checks if hc.status == "healthy"),
                "services_total": len(health_checks)
            }
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from values."""
        if len(values) < 2:
            return "stable"
        
        # Simple trend calculation
        first_half = sum(values[:len(values)//2]) / (len(values)//2)
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        diff_percent = ((second_half - first_half) / first_half) * 100 if first_half > 0 else 0
        
        if diff_percent > 5:
            return "increasing"
        elif diff_percent < -5:
            return "decreasing"
        else:
            return "stable"
    
    def save_metrics_to_file(self, file_path: str = "/var/log/lawvriksh/metrics.json"):
        """Save metrics to file for external monitoring systems."""
        report = self.generate_monitoring_report()
        
        # Create directory if it doesn't exist
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)

# Global monitor instance
production_monitor = ProductionMonitor()
