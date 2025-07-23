"""
Precomputed Leaderboard System for Sub-Millisecond Response Times
================================================================

This module implements a precomputed leaderboard system that provides
sub-millisecond response times through in-memory storage and background
computation jobs.

Features:
- Sub-millisecond response times
- In-memory leaderboard storage
- Background computation jobs
- Real-time updates
- Automatic cache warming
- Memory-efficient data structures
"""

import logging
import threading
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import asyncio
from concurrent.futures import ThreadPoolExecutor
import heapq

logger = logging.getLogger(__name__)

@dataclass
class PrecomputedUser:
    """Optimized user data structure for precomputed leaderboard."""
    user_id: int
    name: str
    points: int
    shares_count: int
    rank: int
    default_rank: Optional[int] = None
    rank_improvement: int = 0
    last_updated: float = field(default_factory=time.time)

@dataclass
class LeaderboardPage:
    """Precomputed leaderboard page with metadata."""
    page: int
    limit: int
    users: List[PrecomputedUser]
    total_users: int
    computed_at: float
    cache_key: str

class PrecomputedLeaderboardSystem:
    """
    High-performance precomputed leaderboard system.
    
    Provides sub-millisecond response times through:
    - In-memory storage of precomputed pages
    - Background computation jobs
    - Efficient data structures
    - Real-time updates
    """
    
    def __init__(self, max_pages: int = 100, page_size: int = 50):
        self.max_pages = max_pages
        self.page_size = page_size
        
        # In-memory storage for precomputed data
        self.leaderboard_pages: Dict[str, LeaderboardPage] = {}
        self.user_ranks: Dict[int, int] = {}
        self.user_data: Dict[int, PrecomputedUser] = {}
        self.around_me_cache: Dict[str, List[PrecomputedUser]] = {}
        
        # Metadata
        self.total_users = 0
        self.last_full_computation = 0
        self.computation_in_progress = False
        
        # Thread safety
        self.lock = threading.RLock()
        self.computation_lock = threading.Lock()
        
        # Background computation
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="leaderboard-compute")
        self.computation_interval = 30  # seconds
        
        # Performance metrics
        self.metrics = {
            "cache_hits": 0,
            "cache_misses": 0,
            "computations": 0,
            "avg_response_time": 0.0,
            "last_computation_time": 0.0
        }
        
        # Start background computation
        self.start_background_computation()
        
        logger.info(f"Precomputed leaderboard system initialized (max_pages={max_pages}, page_size={page_size})")
    
    def _generate_cache_key(self, page: int, limit: int) -> str:
        """Generate cache key for leaderboard page."""
        return f"leaderboard:{page}:{limit}"
    
    def _generate_around_me_key(self, user_id: int, range_size: int) -> str:
        """Generate cache key for around-me data."""
        return f"around_me:{user_id}:{range_size}"
    
    def get_leaderboard_page(self, page: int, limit: int = None) -> Optional[List[Dict[str, Any]]]:
        """
        Get precomputed leaderboard page with sub-millisecond response time.
        
        Args:
            page: Page number (1-indexed)
            limit: Items per page (defaults to system page_size)
            
        Returns:
            List of leaderboard entries or None if not cached
        """
        start_time = time.time()
        
        if limit is None:
            limit = self.page_size
        
        cache_key = self._generate_cache_key(page, limit)
        
        with self.lock:
            if cache_key in self.leaderboard_pages:
                cached_page = self.leaderboard_pages[cache_key]
                
                # Check if cache is still fresh (within 5 minutes)
                if time.time() - cached_page.computed_at < 300:
                    self.metrics["cache_hits"] += 1
                    
                    # Convert to API format
                    result = []
                    for user in cached_page.users:
                        result.append({
                            "rank": user.rank,
                            "user_id": user.user_id,
                            "name": user.name,
                            "points": user.points,
                            "shares_count": user.shares_count,
                            "badge": None,
                            "default_rank": user.default_rank,
                            "rank_improvement": user.rank_improvement
                        })
                    
                    response_time = time.time() - start_time
                    self._update_avg_response_time(response_time)
                    
                    logger.debug(f"Precomputed leaderboard cache hit: {cache_key} in {response_time*1000:.2f}ms")
                    return result
            
            self.metrics["cache_misses"] += 1
            logger.debug(f"Precomputed leaderboard cache miss: {cache_key}")
            return None
    
    def get_user_rank(self, user_id: int) -> Optional[int]:
        """
        Get user rank with sub-millisecond response time.
        
        Args:
            user_id: User ID
            
        Returns:
            User's rank or None if not found
        """
        start_time = time.time()
        
        with self.lock:
            rank = self.user_ranks.get(user_id)
            
            response_time = time.time() - start_time
            self._update_avg_response_time(response_time)
            
            if rank:
                self.metrics["cache_hits"] += 1
                logger.debug(f"Precomputed user rank hit: {user_id} in {response_time*1000:.2f}ms")
            else:
                self.metrics["cache_misses"] += 1
            
            return rank
    
    def get_around_me(self, user_id: int, range_size: int = 5) -> Optional[List[Dict[str, Any]]]:
        """
        Get users around a specific user with sub-millisecond response time.
        
        Args:
            user_id: Target user ID
            range_size: Number of users above and below
            
        Returns:
            List of users around the target user
        """
        start_time = time.time()
        
        cache_key = self._generate_around_me_key(user_id, range_size)
        
        with self.lock:
            if cache_key in self.around_me_cache:
                cached_data = self.around_me_cache[cache_key]
                self.metrics["cache_hits"] += 1
                
                # Convert to API format
                result = []
                for user in cached_data:
                    result.append({
                        "rank": user.rank,
                        "name": user.name,
                        "points": user.points,
                        "is_current_user": user.user_id == user_id
                    })
                
                response_time = time.time() - start_time
                self._update_avg_response_time(response_time)
                
                logger.debug(f"Precomputed around-me cache hit: {cache_key} in {response_time*1000:.2f}ms")
                return result
            
            self.metrics["cache_misses"] += 1
            return None
    
    def _update_avg_response_time(self, response_time: float):
        """Update average response time metric."""
        current_avg = self.metrics["avg_response_time"]
        total_requests = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        
        if total_requests == 1:
            self.metrics["avg_response_time"] = response_time
        else:
            self.metrics["avg_response_time"] = (current_avg * (total_requests - 1) + response_time) / total_requests
    
    def compute_leaderboard(self, db_session) -> bool:
        """
        Compute and cache leaderboard data from database.
        
        Args:
            db_session: Database session
            
        Returns:
            True if computation was successful
        """
        if self.computation_in_progress:
            logger.debug("Leaderboard computation already in progress, skipping")
            return False
        
        with self.computation_lock:
            self.computation_in_progress = True
            
        start_time = time.time()
        
        try:
            logger.info("Starting precomputed leaderboard computation")
            
            # Get all users from database using raw SQL for performance
            from sqlalchemy import text
            sql = text("""
                SELECT 
                    u.id as user_id,
                    u.name,
                    u.total_points as points,
                    u.shares_count,
                    u.default_rank,
                    u.current_rank,
                    ROW_NUMBER() OVER (
                        ORDER BY u.total_points DESC, u.created_at ASC
                    ) as calculated_rank
                FROM users u
                WHERE u.is_admin = FALSE
                ORDER BY u.total_points DESC, u.created_at ASC
            """)
            
            result = db_session.execute(sql)
            rows = result.fetchall()
            
            # Process users and build data structures
            users_data = []
            user_ranks = {}
            user_data = {}
            
            for row in rows:
                rank_improvement = 0
                if row.default_rank and row.current_rank:
                    rank_improvement = row.default_rank - row.current_rank
                elif row.default_rank:
                    rank_improvement = row.default_rank - row.calculated_rank
                
                user = PrecomputedUser(
                    user_id=row.user_id,
                    name=row.name,
                    points=row.points,
                    shares_count=row.shares_count,
                    rank=row.calculated_rank,
                    default_rank=row.default_rank,
                    rank_improvement=rank_improvement
                )
                
                users_data.append(user)
                user_ranks[row.user_id] = row.calculated_rank
                user_data[row.user_id] = user
            
            # Precompute leaderboard pages
            leaderboard_pages = {}
            for page in range(1, min(self.max_pages + 1, (len(users_data) // self.page_size) + 2)):
                start_idx = (page - 1) * self.page_size
                end_idx = start_idx + self.page_size
                page_users = users_data[start_idx:end_idx]
                
                if page_users:
                    cache_key = self._generate_cache_key(page, self.page_size)
                    leaderboard_pages[cache_key] = LeaderboardPage(
                        page=page,
                        limit=self.page_size,
                        users=page_users,
                        total_users=len(users_data),
                        computed_at=time.time(),
                        cache_key=cache_key
                    )
            
            # Precompute around-me data for active users
            around_me_cache = {}
            for user in users_data[:1000]:  # Top 1000 users
                for range_size in [3, 5, 10]:
                    user_rank = user.rank
                    start_rank = max(1, user_rank - range_size)
                    end_rank = min(len(users_data), user_rank + range_size)
                    
                    around_users = []
                    for other_user in users_data:
                        if start_rank <= other_user.rank <= end_rank:
                            around_users.append(other_user)
                    
                    cache_key = self._generate_around_me_key(user.user_id, range_size)
                    around_me_cache[cache_key] = around_users
            
            # Update in-memory storage atomically
            with self.lock:
                self.leaderboard_pages = leaderboard_pages
                self.user_ranks = user_ranks
                self.user_data = user_data
                self.around_me_cache = around_me_cache
                self.total_users = len(users_data)
                self.last_full_computation = time.time()
            
            computation_time = time.time() - start_time
            self.metrics["computations"] += 1
            self.metrics["last_computation_time"] = computation_time
            
            logger.info(f"Precomputed leaderboard computation completed in {computation_time:.3f}s")
            logger.info(f"Cached {len(leaderboard_pages)} pages, {len(user_ranks)} user ranks, {len(around_me_cache)} around-me entries")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in leaderboard computation: {e}")
            return False
            
        finally:
            self.computation_in_progress = False
    
    def start_background_computation(self):
        """Start background computation thread."""
        def computation_worker():
            # Initial computation
            try:
                logger.info("Starting initial precomputed leaderboard computation...")
                from app.core.dependencies import get_db
                db = next(get_db())
                self.compute_leaderboard(db)
                db.close()
                logger.info("Initial precomputed leaderboard computation completed")
            except Exception as e:
                logger.error(f"Initial computation failed: {e}")

            # Continuous computation loop
            while True:
                try:
                    time.sleep(self.computation_interval)

                    # Check if computation is needed
                    if time.time() - self.last_full_computation > self.computation_interval:
                        # Get database session and compute
                        try:
                            from app.core.dependencies import get_db
                            db = next(get_db())
                            self.compute_leaderboard(db)
                            db.close()
                        except Exception as e:
                            logger.error(f"Background computation failed: {e}")

                except Exception as e:
                    logger.error(f"Background computation worker error: {e}")

        # Start background thread
        computation_thread = threading.Thread(target=computation_worker, daemon=True)
        computation_thread.start()
        logger.info("Background leaderboard computation started")
    
    def force_computation(self, db_session) -> bool:
        """Force immediate computation of leaderboard data."""
        return self.compute_leaderboard(db_session)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the precomputed system."""
        with self.lock:
            total_requests = self.metrics["cache_hits"] + self.metrics["cache_misses"]
            hit_rate = (self.metrics["cache_hits"] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                **self.metrics,
                "cache_hit_rate": round(hit_rate, 2),
                "total_requests": total_requests,
                "cached_pages": len(self.leaderboard_pages),
                "cached_user_ranks": len(self.user_ranks),
                "cached_around_me": len(self.around_me_cache),
                "total_users": self.total_users,
                "last_computation": self.last_full_computation,
                "avg_response_time_ms": round(self.metrics["avg_response_time"] * 1000, 3),
                "computation_in_progress": self.computation_in_progress
            }
    
    def clear_cache(self):
        """Clear all cached data."""
        with self.lock:
            self.leaderboard_pages.clear()
            self.user_ranks.clear()
            self.user_data.clear()
            self.around_me_cache.clear()
            logger.info("Precomputed leaderboard cache cleared")

# Global precomputed leaderboard instance
precomputed_leaderboard = PrecomputedLeaderboardSystem()
