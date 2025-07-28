"""
Database Query Profiling Middleware
===================================

This middleware provides comprehensive database query profiling for FastAPI applications.
It tracks query execution times, identifies slow queries, and provides EXPLAIN analysis
for performance optimization.

Features:
- Query execution time tracking
- Automatic EXPLAIN analysis for slow queries
- N+1 query detection
- Query performance logging
- Real-time performance metrics
"""

import time
import logging
import hashlib
import json
from typing import Dict, List, Any, Optional
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque

from fastapi import Request, Response
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# =====================================================
# PROFILING DATA STRUCTURES
# =====================================================

@dataclass
class QueryProfile:
    """Data structure for query profiling information."""
    query: str
    params: Dict[str, Any]
    execution_time: float
    rows_examined: int
    rows_returned: int
    query_hash: str
    timestamp: datetime
    endpoint: Optional[str] = None
    user_id: Optional[int] = None
    explain_plan: Optional[Dict[str, Any]] = None

@dataclass
class RequestProfile:
    """Data structure for request-level profiling."""
    endpoint: str
    method: str
    total_time: float
    query_count: int
    total_query_time: float
    queries: List[QueryProfile]
    timestamp: datetime
    user_id: Optional[int] = None

# =====================================================
# QUERY PROFILER CLASS
# =====================================================

class QueryProfiler:
    """Main query profiler class."""
    
    def __init__(self, slow_query_threshold: float = 0.1, enable_explain: bool = True):
        self.slow_query_threshold = slow_query_threshold
        self.enable_explain = enable_explain
        self.query_stats = defaultdict(list)
        self.request_profiles = deque(maxlen=1000)  # Keep last 1000 requests
        self.n1_patterns = defaultdict(int)
        self.current_request_queries = []
        self.current_request_start = None
        
    def start_request_profiling(self, request: Request):
        """Start profiling for a new request."""
        self.current_request_queries = []
        self.current_request_start = time.time()
        
    def add_query_profile(self, profile: QueryProfile):
        """Add a query profile to the current request."""
        self.current_request_queries.append(profile)
        
        # Store in query stats for analysis
        query_key = profile.query_hash
        self.query_stats[query_key].append(profile)
        
        # Keep only recent queries (last 1000 per query type)
        if len(self.query_stats[query_key]) > 1000:
            self.query_stats[query_key] = self.query_stats[query_key][-1000:]
            
        # Detect potential N+1 patterns
        self._detect_n1_pattern(profile)
        
    def finish_request_profiling(self, request: Request, response: Response):
        """Finish profiling for the current request."""
        if self.current_request_start is None:
            return
            
        total_time = time.time() - self.current_request_start
        query_count = len(self.current_request_queries)
        total_query_time = sum(q.execution_time for q in self.current_request_queries)
        
        # Extract user ID from request if available
        user_id = getattr(request.state, 'user_id', None)
        
        request_profile = RequestProfile(
            endpoint=f"{request.method} {request.url.path}",
            method=request.method,
            total_time=total_time,
            query_count=query_count,
            total_query_time=total_query_time,
            queries=self.current_request_queries.copy(),
            timestamp=datetime.utcnow(),
            user_id=user_id
        )
        
        self.request_profiles.append(request_profile)
        
        # Log slow requests
        if total_time > self.slow_query_threshold * 2:  # 2x threshold for requests
            logger.warning(
                f"Slow request: {request_profile.endpoint} "
                f"took {total_time:.3f}s with {query_count} queries"
            )
            
        # Log requests with many queries (potential N+1)
        if query_count > 10:
            logger.warning(
                f"High query count: {request_profile.endpoint} "
                f"executed {query_count} queries"
            )
    
    def _detect_n1_pattern(self, profile: QueryProfile):
        """Detect potential N+1 query patterns."""
        # Simple N+1 detection based on similar queries
        query_pattern = self._normalize_query(profile.query)
        self.n1_patterns[query_pattern] += 1
        
        # Alert if we see the same pattern many times in a short period
        if self.n1_patterns[query_pattern] > 5:
            logger.warning(f"Potential N+1 pattern detected: {query_pattern}")
            
    def _normalize_query(self, query: str) -> str:
        """Normalize query for pattern detection."""
        # Remove parameter values and normalize whitespace
        import re
        normalized = re.sub(r'\b\d+\b', '?', query)  # Replace numbers with ?
        normalized = re.sub(r"'[^']*'", '?', normalized)  # Replace strings with ?
        normalized = re.sub(r'\s+', ' ', normalized).strip()  # Normalize whitespace
        return normalized
        
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        now = datetime.utcnow()
        recent_requests = [
            r for r in self.request_profiles 
            if (now - r.timestamp).total_seconds() < 3600  # Last hour
        ]
        
        if not recent_requests:
            return {"message": "No recent requests"}
            
        # Calculate statistics
        total_requests = len(recent_requests)
        avg_response_time = sum(r.total_time for r in recent_requests) / total_requests
        avg_query_count = sum(r.query_count for r in recent_requests) / total_requests
        
        # Find slowest queries
        all_queries = []
        for request in recent_requests:
            all_queries.extend(request.queries)
            
        slowest_queries = sorted(all_queries, key=lambda q: q.execution_time, reverse=True)[:10]
        
        # Most frequent queries
        query_frequency = defaultdict(int)
        for query in all_queries:
            query_frequency[query.query_hash] += 1
            
        most_frequent = sorted(
            query_frequency.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        return {
            "summary": {
                "total_requests": total_requests,
                "avg_response_time": round(avg_response_time, 3),
                "avg_query_count": round(avg_query_count, 1),
                "total_queries": len(all_queries)
            },
            "slowest_queries": [
                {
                    "query": q.query[:100] + "..." if len(q.query) > 100 else q.query,
                    "execution_time": round(q.execution_time, 3),
                    "endpoint": q.endpoint
                }
                for q in slowest_queries
            ],
            "most_frequent_queries": [
                {
                    "query_hash": query_hash,
                    "frequency": freq,
                    "sample_query": next(
                        (q.query[:100] + "..." if len(q.query) > 100 else q.query 
                         for q in all_queries if q.query_hash == query_hash), 
                        "Unknown"
                    )
                }
                for query_hash, freq in most_frequent
            ],
            "n1_patterns": dict(self.n1_patterns)
        }

# Global profiler instance
query_profiler = QueryProfiler()

# =====================================================
# SQLALCHEMY EVENT LISTENERS
# =====================================================

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Record query start time."""
    context._query_start_time = time.time()

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Record query execution time and create profile."""
    if not hasattr(context, '_query_start_time'):
        return
        
    execution_time = time.time() - context._query_start_time
    
    # Create query hash
    query_hash = hashlib.md5(statement.encode()).hexdigest()[:16]
    
    # Get row counts
    rows_returned = cursor.rowcount if cursor.rowcount >= 0 else 0
    rows_examined = getattr(cursor, 'rows_examined', 0)
    
    # Create profile
    profile = QueryProfile(
        query=statement,
        params=parameters or {},
        execution_time=execution_time,
        rows_examined=rows_examined,
        rows_returned=rows_returned,
        query_hash=query_hash,
        timestamp=datetime.utcnow()
    )
    
    # Add to profiler
    query_profiler.add_query_profile(profile)
    
    # Log slow queries
    if execution_time > query_profiler.slow_query_threshold:
        logger.warning(
            f"Slow query ({execution_time:.3f}s): "
            f"{statement[:200]}{'...' if len(statement) > 200 else ''}"
        )
        
        # Get EXPLAIN plan for slow queries if enabled
        if query_profiler.enable_explain and statement.strip().upper().startswith('SELECT'):
            try:
                explain_result = conn.execute(text(f"EXPLAIN {statement}"), parameters)
                profile.explain_plan = [dict(row) for row in explain_result.fetchall()]
            except Exception as e:
                logger.debug(f"Could not get EXPLAIN plan: {e}")

# =====================================================
# FASTAPI MIDDLEWARE
# =====================================================

async def query_profiling_middleware(request: Request, call_next):
    """FastAPI middleware for query profiling."""
    # Start profiling
    query_profiler.start_request_profiling(request)
    
    # Process request
    response = await call_next(request)
    
    # Finish profiling
    query_profiler.finish_request_profiling(request, response)
    
    # Add profiling headers in development
    if hasattr(request.app.state, 'debug') and request.app.state.debug:
        query_count = len(query_profiler.current_request_queries)
        total_query_time = sum(q.execution_time for q in query_profiler.current_request_queries)
        
        response.headers["X-Query-Count"] = str(query_count)
        response.headers["X-Query-Time"] = f"{total_query_time:.3f}"
    
    return response

# =====================================================
# EXPLAIN QUERY ANALYSIS UTILITIES
# =====================================================

class ExplainAnalyzer:
    """Utility class for analyzing EXPLAIN query plans."""

    @staticmethod
    def analyze_explain_plan(explain_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze EXPLAIN plan and provide optimization suggestions."""
        if not explain_rows:
            return {"error": "No EXPLAIN data available"}

        analysis = {
            "total_rows_examined": 0,
            "using_filesort": False,
            "using_temporary": False,
            "full_table_scans": [],
            "missing_indexes": [],
            "optimization_suggestions": []
        }

        for row in explain_rows:
            # Count total rows examined
            rows = row.get('rows', 0)
            if isinstance(rows, int):
                analysis["total_rows_examined"] += rows

            # Check for performance issues
            extra = row.get('Extra', '').lower()
            if 'using filesort' in extra:
                analysis["using_filesort"] = True
                analysis["optimization_suggestions"].append(
                    f"Query uses filesort on table '{row.get('table', 'unknown')}'. "
                    "Consider adding an index on the ORDER BY columns."
                )

            if 'using temporary' in extra:
                analysis["using_temporary"] = True
                analysis["optimization_suggestions"].append(
                    f"Query uses temporary table for table '{row.get('table', 'unknown')}'. "
                    "Consider optimizing GROUP BY or DISTINCT clauses."
                )

            # Check for full table scans
            select_type = row.get('type', '').lower()
            if select_type in ['all', 'index']:
                table_name = row.get('table', 'unknown')
                analysis["full_table_scans"].append(table_name)
                analysis["optimization_suggestions"].append(
                    f"Full table scan detected on table '{table_name}'. "
                    "Consider adding appropriate indexes."
                )

            # Check for missing indexes
            key = row.get('key')
            if not key or key == 'NULL':
                table_name = row.get('table', 'unknown')
                analysis["missing_indexes"].append(table_name)

        # Performance rating
        if analysis["total_rows_examined"] > 10000:
            analysis["performance_rating"] = "Poor"
        elif analysis["total_rows_examined"] > 1000:
            analysis["performance_rating"] = "Fair"
        else:
            analysis["performance_rating"] = "Good"

        return analysis

    @staticmethod
    def get_query_optimization_suggestions(query: str, explain_plan: List[Dict[str, Any]]) -> List[str]:
        """Get specific optimization suggestions for a query."""
        suggestions = []

        if not explain_plan:
            return ["Unable to analyze query - no EXPLAIN data available"]

        analysis = ExplainAnalyzer.analyze_explain_plan(explain_plan)

        # Add general suggestions based on query structure
        query_lower = query.lower()

        if 'select *' in query_lower:
            suggestions.append(
                "Avoid SELECT * - specify only the columns you need to reduce data transfer."
            )

        if 'order by' in query_lower and analysis["using_filesort"]:
            suggestions.append(
                "Add a composite index covering the ORDER BY columns to avoid filesort."
            )

        if 'group by' in query_lower and analysis["using_temporary"]:
            suggestions.append(
                "Optimize GROUP BY clause or add covering indexes to avoid temporary tables."
            )

        if analysis["full_table_scans"]:
            suggestions.append(
                f"Add indexes to tables with full scans: {', '.join(analysis['full_table_scans'])}"
            )

        if analysis["total_rows_examined"] > 1000:
            suggestions.append(
                "Consider adding LIMIT clause or more selective WHERE conditions to reduce rows examined."
            )

        return suggestions or ["Query appears to be well optimized."]

# Global analyzer instance
explain_analyzer = ExplainAnalyzer()
