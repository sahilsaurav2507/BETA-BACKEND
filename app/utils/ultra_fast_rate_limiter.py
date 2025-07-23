"""
Ultra-Fast O(1) Token Bucket Rate Limiter
=========================================

This module implements an ultra-fast O(1) token bucket rate limiter that
provides maximum performance with minimal overhead compared to O(n) sliding
window approaches.

Features:
- O(1) time complexity for all operations
- Ultra-fast token bucket algorithm
- Minimal memory footprint
- High-performance data structures
- Automatic token refill
- Multiple rate limit tiers
- Thread-safe operations
"""

import logging
import threading
import time
from typing import Dict, Tuple
from dataclasses import dataclass
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class UltraFastTokenBucket:
    """
    Ultra-fast token bucket with O(1) operations.
    
    Optimized for maximum performance with minimal overhead.
    """
    capacity: int
    tokens: float
    refill_rate: float  # tokens per second
    last_refill: float
    
    def consume_tokens(self, tokens: int = 1) -> bool:
        """
        Consume tokens with O(1) time complexity.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False if insufficient tokens
        """
        now = time.time()
        
        # Calculate tokens to add based on elapsed time (O(1))
        time_elapsed = now - self.last_refill
        tokens_to_add = time_elapsed * self.refill_rate
        
        # Update token count (O(1))
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
        
        # Check and consume tokens (O(1))
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        return False
    
    def get_tokens_remaining(self) -> int:
        """Get remaining tokens with O(1) complexity."""
        now = time.time()
        time_elapsed = now - self.last_refill
        tokens_to_add = time_elapsed * self.refill_rate
        current_tokens = min(self.capacity, self.tokens + tokens_to_add)
        return int(current_tokens)
    
    def get_refill_time(self) -> float:
        """Get time until bucket is full with O(1) complexity."""
        if self.tokens >= self.capacity:
            return 0.0
        
        tokens_needed = self.capacity - self.tokens
        return tokens_needed / self.refill_rate if self.refill_rate > 0 else float('inf')

class UltraFastRateLimiter:
    """
    Ultra-fast O(1) rate limiter using optimized token buckets.
    
    Provides maximum performance with minimal overhead for high-throughput
    applications requiring ultra-fast rate limiting.
    """
    
    def __init__(self):
        # Rate limit configurations optimized for performance
        self.rate_configs = {
            "default": {"capacity": 60, "refill_rate": 1.0},      # 60 requests/minute
            "auth": {"capacity": 10, "refill_rate": 0.167},       # 10 requests/minute
            "api": {"capacity": 100, "refill_rate": 1.667},       # 100 requests/minute
            "admin": {"capacity": 200, "refill_rate": 3.333},     # 200 requests/minute
            "burst": {"capacity": 20, "refill_rate": 0.333},      # 20 requests/minute with burst
        }
        
        # Ultra-fast token buckets storage
        self.buckets: Dict[str, UltraFastTokenBucket] = {}
        
        # Minimal thread safety with RLock for performance
        self.lock = threading.RLock()
        
        # Performance metrics
        self.metrics = {
            "total_requests": 0,
            "allowed_requests": 0,
            "blocked_requests": 0,
            "avg_processing_time": 0.0,
            "active_buckets": 0,
            "o1_operations": 0
        }
        
        # Cleanup configuration
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes
        
        logger.info("Ultra-fast O(1) rate limiter initialized")
    
    def _get_bucket_key(self, ip: str, endpoint_type: str) -> str:
        """Generate optimized bucket key with O(1) complexity."""
        # Use hash for memory efficiency and O(1) lookup
        key_string = f"{ip}:{endpoint_type}"
        return hashlib.md5(key_string.encode()).hexdigest()[:12]  # Shorter hash for memory efficiency
    
    def _get_endpoint_type(self, path: str) -> str:
        """Determine endpoint type with O(1) complexity."""
        # Ultra-fast endpoint classification
        if path.startswith("/auth/"):
            return "auth"
        elif path.startswith("/admin/"):
            return "admin"
        elif path.startswith("/api/"):
            return "api"
        elif "burst" in path or "fast" in path:
            return "burst"
        else:
            return "default"
    
    def _create_bucket(self, endpoint_type: str) -> UltraFastTokenBucket:
        """Create optimized token bucket with O(1) complexity."""
        config = self.rate_configs.get(endpoint_type, self.rate_configs["default"])
        
        return UltraFastTokenBucket(
            capacity=config["capacity"],
            tokens=config["capacity"],  # Start with full bucket
            refill_rate=config["refill_rate"],
            last_refill=time.time()
        )
    
    def is_allowed(self, ip: str, path: str = "/") -> Tuple[bool, Dict[str, any]]:
        """
        Ultra-fast rate limiting check with O(1) time complexity.
        
        Args:
            ip: Client IP address
            path: Request path for endpoint classification
            
        Returns:
            Tuple of (allowed, rate_limit_info)
        """
        start_time = time.time()
        
        # O(1) endpoint type determination
        endpoint_type = self._get_endpoint_type(path)
        
        # O(1) bucket key generation
        bucket_key = self._get_bucket_key(ip, endpoint_type)
        
        with self.lock:
            self.metrics["total_requests"] += 1
            self.metrics["o1_operations"] += 1
            
            # O(1) bucket retrieval or creation
            if bucket_key not in self.buckets:
                self.buckets[bucket_key] = self._create_bucket(endpoint_type)
            
            bucket = self.buckets[bucket_key]
            
            # O(1) token consumption
            allowed = bucket.consume_tokens(1)
            
            # O(1) metrics update
            if allowed:
                self.metrics["allowed_requests"] += 1
            else:
                self.metrics["blocked_requests"] += 1
            
            # O(1) rate limit info generation
            config = self.rate_configs[endpoint_type]
            remaining_tokens = bucket.get_tokens_remaining()
            refill_time = bucket.get_refill_time()
            
            rate_limit_info = {
                "limit": config["capacity"],
                "remaining": remaining_tokens,
                "reset_time": int(time.time() + refill_time),
                "retry_after": int(refill_time) if not allowed else 0,
                "endpoint_type": endpoint_type
            }
            
            # O(1) performance tracking
            processing_time = time.time() - start_time
            self._update_avg_processing_time(processing_time)
            
            # Periodic cleanup (amortized O(1))
            self._maybe_cleanup()
            
            return allowed, rate_limit_info
    
    def _update_avg_processing_time(self, processing_time: float):
        """Update average processing time with O(1) complexity."""
        current_avg = self.metrics["avg_processing_time"]
        total_requests = self.metrics["total_requests"]
        
        if total_requests == 1:
            self.metrics["avg_processing_time"] = processing_time
        else:
            # Rolling average with O(1) complexity
            self.metrics["avg_processing_time"] = (
                current_avg * 0.99 + processing_time * 0.01
            )
    
    def _maybe_cleanup(self):
        """Perform cleanup if needed (amortized O(1))."""
        now = time.time()
        if now - self.last_cleanup > self.cleanup_interval:
            self._cleanup_expired_buckets()
            self.last_cleanup = now
    
    def _cleanup_expired_buckets(self):
        """Clean up expired buckets to maintain memory efficiency."""
        try:
            now = time.time()
            expired_keys = []
            
            # Find buckets that haven't been used recently
            for key, bucket in self.buckets.items():
                if now - bucket.last_refill > self.cleanup_interval * 2:
                    expired_keys.append(key)
            
            # Remove expired buckets
            for key in expired_keys:
                del self.buckets[key]
            
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired rate limit buckets")
                
        except Exception as e:
            logger.error(f"Error in bucket cleanup: {e}")
    
    def get_bucket_status(self, ip: str, path: str = "/") -> Dict[str, any]:
        """Get bucket status with O(1) complexity."""
        endpoint_type = self._get_endpoint_type(path)
        bucket_key = self._get_bucket_key(ip, endpoint_type)
        
        with self.lock:
            if bucket_key not in self.buckets:
                config = self.rate_configs[endpoint_type]
                return {
                    "tokens_remaining": config["capacity"],
                    "capacity": config["capacity"],
                    "refill_rate": config["refill_rate"],
                    "refill_time": 0.0,
                    "endpoint_type": endpoint_type,
                    "bucket_exists": False
                }
            
            bucket = self.buckets[bucket_key]
            return {
                "tokens_remaining": bucket.get_tokens_remaining(),
                "capacity": bucket.capacity,
                "refill_rate": bucket.refill_rate,
                "refill_time": bucket.get_refill_time(),
                "endpoint_type": endpoint_type,
                "bucket_exists": True
            }
    
    def reset_bucket(self, ip: str, path: str = "/") -> bool:
        """Reset bucket with O(1) complexity."""
        endpoint_type = self._get_endpoint_type(path)
        bucket_key = self._get_bucket_key(ip, endpoint_type)
        
        with self.lock:
            if bucket_key in self.buckets:
                del self.buckets[bucket_key]
                logger.info(f"Reset rate limit bucket for {ip}:{endpoint_type}")
                return True
            return False
    
    def get_performance_stats(self) -> Dict[str, any]:
        """Get performance statistics with O(1) complexity."""
        with self.lock:
            stats = self.metrics.copy()
            stats["active_buckets"] = len(self.buckets)
            
            # Calculate performance metrics
            total_requests = stats["total_requests"]
            if total_requests > 0:
                stats["success_rate"] = round(
                    (stats["allowed_requests"] / total_requests) * 100, 2
                )
                stats["block_rate"] = round(
                    (stats["blocked_requests"] / total_requests) * 100, 2
                )
                stats["avg_processing_time_ms"] = round(
                    stats["avg_processing_time"] * 1000, 3
                )
            else:
                stats["success_rate"] = 100.0
                stats["block_rate"] = 0.0
                stats["avg_processing_time_ms"] = 0.0
            
            # Performance benefits
            stats["algorithm_complexity"] = "O(1)"
            stats["performance_improvement"] = "Ultra-fast vs O(n) sliding window"
            
            return stats
    
    def benchmark_performance(self, iterations: int = 10000) -> Dict[str, any]:
        """Benchmark O(1) performance with multiple iterations."""
        start_time = time.time()
        
        # Simulate high-load scenario
        allowed_count = 0
        blocked_count = 0
        
        for i in range(iterations):
            ip = f"192.168.1.{i % 255}"
            path = f"/api/test/{i % 10}"
            
            allowed, _ = self.is_allowed(ip, path)
            if allowed:
                allowed_count += 1
            else:
                blocked_count += 1
        
        total_time = time.time() - start_time
        
        return {
            "iterations": iterations,
            "total_time_seconds": round(total_time, 3),
            "requests_per_second": round(iterations / total_time, 2),
            "avg_time_per_request_ms": round((total_time / iterations) * 1000, 3),
            "allowed_requests": allowed_count,
            "blocked_requests": blocked_count,
            "algorithm_complexity": "O(1)",
            "performance_class": "Ultra-fast"
        }

# Global ultra-fast rate limiter instance
ultra_fast_rate_limiter = UltraFastRateLimiter()
