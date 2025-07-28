"""
Database Profiling API Endpoints
================================

This module provides API endpoints for accessing database query profiling data,
performance metrics, and optimization suggestions.

Features:
- Real-time performance statistics
- Query profiling data access
- EXPLAIN plan analysis
- Performance optimization suggestions
- N+1 query detection reports
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.dependencies import get_db
from app.core.security import get_current_admin
from app.middleware.query_profiler import query_profiler, explain_analyzer
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profiling", tags=["profiling"])

# =====================================================
# RESPONSE MODELS
# =====================================================

class QueryProfileResponse(BaseModel):
    """Response model for query profile data."""
    query: str
    execution_time: float
    rows_examined: int
    rows_returned: int
    timestamp: datetime
    endpoint: Optional[str] = None
    explain_plan: Optional[List[Dict[str, Any]]] = None
    optimization_suggestions: List[str] = []

class PerformanceStatsResponse(BaseModel):
    """Response model for performance statistics."""
    summary: Dict[str, Any]
    slowest_queries: List[Dict[str, Any]]
    most_frequent_queries: List[Dict[str, Any]]
    n1_patterns: Dict[str, int]

class ExplainAnalysisResponse(BaseModel):
    """Response model for EXPLAIN analysis."""
    query: str
    explain_plan: List[Dict[str, Any]]
    analysis: Dict[str, Any]
    optimization_suggestions: List[str]
    performance_rating: str

# =====================================================
# PROFILING ENDPOINTS
# =====================================================

@router.get("/stats", response_model=PerformanceStatsResponse)
def get_performance_stats(admin=Depends(get_current_admin)):
    """
    Get comprehensive database performance statistics.
    
    Requires admin authentication. Provides insights into:
    - Query execution times
    - Most frequent queries
    - Slowest queries
    - Potential N+1 patterns
    """
    try:
        stats = query_profiler.get_performance_stats()
        return PerformanceStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error getting performance stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve performance statistics"
        )

@router.get("/slow-queries")
def get_slow_queries(
    limit: int = Query(20, ge=1, le=100, description="Number of queries to return"),
    threshold: float = Query(0.1, ge=0.01, description="Minimum execution time in seconds"),
    admin=Depends(get_current_admin)
):
    """
    Get slow queries above the specified threshold.
    
    Args:
        limit: Maximum number of queries to return
        threshold: Minimum execution time in seconds
        
    Returns:
        List of slow queries with profiling data
    """
    try:
        # Get all queries from recent requests
        recent_queries = []
        for request in query_profiler.request_profiles:
            for query in request.queries:
                if query.execution_time >= threshold:
                    recent_queries.append({
                        "query": query.query,
                        "execution_time": query.execution_time,
                        "rows_examined": query.rows_examined,
                        "rows_returned": query.rows_returned,
                        "timestamp": query.timestamp.isoformat(),
                        "endpoint": query.endpoint,
                        "query_hash": query.query_hash
                    })
        
        # Sort by execution time and limit
        slow_queries = sorted(
            recent_queries, 
            key=lambda x: x["execution_time"], 
            reverse=True
        )[:limit]
        
        return {
            "slow_queries": slow_queries,
            "threshold": threshold,
            "total_found": len(slow_queries)
        }
        
    except Exception as e:
        logger.error(f"Error getting slow queries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve slow queries"
        )

@router.post("/explain", response_model=ExplainAnalysisResponse)
def analyze_query_explain(
    query: str,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """
    Analyze a query using EXPLAIN and provide optimization suggestions.
    
    Args:
        query: SQL query to analyze
        
    Returns:
        EXPLAIN analysis with optimization suggestions
    """
    try:
        # Validate query (basic security check)
        query_lower = query.lower().strip()
        if not query_lower.startswith('select'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only SELECT queries are supported for EXPLAIN analysis"
            )
            
        # Execute EXPLAIN
        explain_query = f"EXPLAIN {query}"
        result = db.execute(text(explain_query))
        explain_plan = [dict(row) for row in result.fetchall()]
        
        # Analyze the plan
        analysis = explain_analyzer.analyze_explain_plan(explain_plan)
        suggestions = explain_analyzer.get_query_optimization_suggestions(query, explain_plan)
        
        return ExplainAnalysisResponse(
            query=query,
            explain_plan=explain_plan,
            analysis=analysis,
            optimization_suggestions=suggestions,
            performance_rating=analysis.get("performance_rating", "Unknown")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze query: {str(e)}"
        )

@router.get("/n1-patterns")
def get_n1_patterns(admin=Depends(get_current_admin)):
    """
    Get detected N+1 query patterns.
    
    Returns patterns that might indicate N+1 query problems
    along with their frequency and suggestions for optimization.
    """
    try:
        patterns = dict(query_profiler.n1_patterns)
        
        # Add analysis for each pattern
        analyzed_patterns = []
        for pattern, count in patterns.items():
            if count > 3:  # Only show patterns with significant frequency
                analyzed_patterns.append({
                    "pattern": pattern,
                    "frequency": count,
                    "severity": "High" if count > 10 else "Medium" if count > 5 else "Low",
                    "suggestion": "Consider using eager loading (joinedload/selectinload) to fetch related data in fewer queries"
                })
        
        # Sort by frequency
        analyzed_patterns.sort(key=lambda x: x["frequency"], reverse=True)
        
        return {
            "n1_patterns": analyzed_patterns,
            "total_patterns": len(analyzed_patterns),
            "recommendations": [
                "Use SQLAlchemy's joinedload() for many-to-one relationships",
                "Use SQLAlchemy's selectinload() for one-to-many relationships",
                "Consider using raw SQL with JOINs for complex queries",
                "Implement query result caching for frequently accessed data"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting N+1 patterns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve N+1 patterns"
        )

@router.get("/request-profiles")
def get_request_profiles(
    limit: int = Query(50, ge=1, le=200, description="Number of requests to return"),
    min_queries: int = Query(0, ge=0, description="Minimum number of queries per request"),
    admin=Depends(get_current_admin)
):
    """
    Get recent request profiles with query information.
    
    Args:
        limit: Maximum number of requests to return
        min_queries: Filter requests with at least this many queries
        
    Returns:
        List of request profiles with timing and query data
    """
    try:
        # Filter and format request profiles
        profiles = []
        for request in list(query_profiler.request_profiles)[-limit:]:
            if request.query_count >= min_queries:
                profiles.append({
                    "endpoint": request.endpoint,
                    "method": request.method,
                    "total_time": round(request.total_time, 3),
                    "query_count": request.query_count,
                    "total_query_time": round(request.total_query_time, 3),
                    "timestamp": request.timestamp.isoformat(),
                    "user_id": request.user_id,
                    "efficiency_ratio": round(
                        request.total_query_time / request.total_time * 100, 1
                    ) if request.total_time > 0 else 0
                })
        
        # Sort by total time (slowest first)
        profiles.sort(key=lambda x: x["total_time"], reverse=True)
        
        return {
            "request_profiles": profiles,
            "total_requests": len(profiles),
            "analysis": {
                "avg_queries_per_request": sum(p["query_count"] for p in profiles) / len(profiles) if profiles else 0,
                "avg_response_time": sum(p["total_time"] for p in profiles) / len(profiles) if profiles else 0,
                "high_query_requests": len([p for p in profiles if p["query_count"] > 10])
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting request profiles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve request profiles"
        )

@router.delete("/clear-stats")
def clear_profiling_stats(admin=Depends(get_current_admin)):
    """
    Clear all profiling statistics and start fresh.
    
    This endpoint clears all collected profiling data.
    Use with caution as this will remove all performance history.
    """
    try:
        query_profiler.query_stats.clear()
        query_profiler.request_profiles.clear()
        query_profiler.n1_patterns.clear()
        
        return {
            "message": "Profiling statistics cleared successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error clearing profiling stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear profiling statistics"
        )
