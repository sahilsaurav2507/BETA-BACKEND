"""
Advanced Pagination Utilities for FastAPI
=========================================

This module provides optimized pagination utilities that work with SQLAlchemy
and provide efficient LIMIT/OFFSET queries for large datasets.

Features:
- Server-side pagination with LIMIT/OFFSET
- Cursor-based pagination for real-time data
- Optimized count queries
- Flexible page size limits
- Metadata for frontend pagination controls
"""

import math
from typing import TypeVar, Generic, List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Query, Session
from sqlalchemy import func, text
from fastapi import Query as FastAPIQuery, HTTPException

# Type variables for generic pagination
T = TypeVar('T')

# =====================================================
# PAGINATION MODELS
# =====================================================

class PaginationParams(BaseModel):
    """Standard pagination parameters."""
    page: int = Field(1, ge=1, description="Page number (1-based)")
    limit: int = Field(50, ge=1, le=1000, description="Items per page")
    
    @validator('limit')
    def validate_limit(cls, v):
        if v > 1000:
            raise ValueError("Limit cannot exceed 1000 items per page")
        return v
    
    @property
    def offset(self) -> int:
        """Calculate offset from page and limit."""
        return (self.page - 1) * self.limit

class PaginationMeta(BaseModel):
    """Pagination metadata for responses."""
    page: int
    limit: int
    total: int
    pages: int
    has_next: bool
    has_prev: bool
    next_page: Optional[int] = None
    prev_page: Optional[int] = None
    
    @classmethod
    def create(cls, page: int, limit: int, total: int) -> 'PaginationMeta':
        """Create pagination metadata from parameters."""
        pages = math.ceil(total / limit) if total > 0 else 0
        has_next = page < pages
        has_prev = page > 1
        
        return cls(
            page=page,
            limit=limit,
            total=total,
            pages=pages,
            has_next=has_next,
            has_prev=has_prev,
            next_page=page + 1 if has_next else None,
            prev_page=page - 1 if has_prev else None
        )

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response model."""
    items: List[T]
    pagination: PaginationMeta
    
    class Config:
        arbitrary_types_allowed = True

# =====================================================
# CURSOR-BASED PAGINATION
# =====================================================

class CursorParams(BaseModel):
    """Cursor-based pagination parameters."""
    cursor: Optional[str] = None
    limit: int = Field(50, ge=1, le=1000)
    direction: str = Field("next", regex="^(next|prev)$")

class CursorMeta(BaseModel):
    """Cursor pagination metadata."""
    next_cursor: Optional[str] = None
    prev_cursor: Optional[str] = None
    has_next: bool = False
    has_prev: bool = False
    limit: int

class CursorResponse(BaseModel, Generic[T]):
    """Generic cursor-based paginated response."""
    items: List[T]
    cursor: CursorMeta
    
    class Config:
        arbitrary_types_allowed = True

# =====================================================
# PAGINATION UTILITIES
# =====================================================

class PaginationHelper:
    """Helper class for pagination operations."""
    
    @staticmethod
    def paginate_query(
        query: Query,
        page: int = 1,
        limit: int = 50,
        count_query: Optional[Query] = None
    ) -> Dict[str, Any]:
        """
        Paginate a SQLAlchemy query with optimized counting.
        
        Args:
            query: The main query to paginate
            page: Page number (1-based)
            limit: Items per page
            count_query: Optional separate query for counting (for optimization)
            
        Returns:
            Dictionary with items and pagination metadata
        """
        # Validate parameters
        if page < 1:
            page = 1
        if limit < 1 or limit > 1000:
            limit = 50
            
        # Calculate offset
        offset = (page - 1) * limit
        
        # Get total count (use separate query if provided for optimization)
        if count_query is not None:
            total = count_query.scalar()
        else:
            # Use subquery for better performance on complex queries
            total = query.statement.with_only_columns([func.count()]).order_by(None).scalar()
        
        # Get paginated items
        items = query.offset(offset).limit(limit).all()
        
        # Create pagination metadata
        pagination = PaginationMeta.create(page, limit, total)
        
        return {
            "items": items,
            "pagination": pagination
        }
    
    @staticmethod
    def paginate_raw_sql(
        db: Session,
        base_query: str,
        count_query: str,
        params: Dict[str, Any],
        page: int = 1,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Paginate raw SQL queries for maximum performance.
        
        Args:
            db: Database session
            base_query: Main SQL query (should include ORDER BY)
            count_query: SQL query to get total count
            params: Parameters for the queries
            page: Page number (1-based)
            limit: Items per page
            
        Returns:
            Dictionary with items and pagination metadata
        """
        # Validate parameters
        if page < 1:
            page = 1
        if limit < 1 or limit > 1000:
            limit = 50
            
        # Calculate offset
        offset = (page - 1) * limit
        
        # Get total count
        total_result = db.execute(text(count_query), params)
        total = total_result.scalar()
        
        # Add pagination to base query
        paginated_query = f"{base_query} LIMIT :limit OFFSET :offset"
        paginated_params = {**params, "limit": limit, "offset": offset}
        
        # Execute paginated query
        result = db.execute(text(paginated_query), paginated_params)
        items = result.fetchall()
        
        # Create pagination metadata
        pagination = PaginationMeta.create(page, limit, total)
        
        return {
            "items": items,
            "pagination": pagination
        }
    
    @staticmethod
    def create_cursor(item_id: int, timestamp: str) -> str:
        """Create a cursor for cursor-based pagination."""
        import base64
        import json
        
        cursor_data = {"id": item_id, "ts": timestamp}
        cursor_json = json.dumps(cursor_data)
        return base64.b64encode(cursor_json.encode()).decode()
    
    @staticmethod
    def parse_cursor(cursor: str) -> Dict[str, Any]:
        """Parse a cursor for cursor-based pagination."""
        import base64
        import json
        
        try:
            cursor_json = base64.b64decode(cursor.encode()).decode()
            return json.loads(cursor_json)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid cursor")

# =====================================================
# FASTAPI DEPENDENCIES
# =====================================================

def get_pagination_params(
    page: int = FastAPIQuery(1, ge=1, description="Page number"),
    limit: int = FastAPIQuery(50, ge=1, le=1000, description="Items per page")
) -> PaginationParams:
    """FastAPI dependency for pagination parameters."""
    return PaginationParams(page=page, limit=limit)

def get_cursor_params(
    cursor: Optional[str] = FastAPIQuery(None, description="Pagination cursor"),
    limit: int = FastAPIQuery(50, ge=1, le=1000, description="Items per page"),
    direction: str = FastAPIQuery("next", regex="^(next|prev)$", description="Pagination direction")
) -> CursorParams:
    """FastAPI dependency for cursor-based pagination parameters."""
    return CursorParams(cursor=cursor, limit=limit, direction=direction)

# =====================================================
# SPECIALIZED PAGINATION CLASSES
# =====================================================

class LeaderboardPagination:
    """Specialized pagination for leaderboard queries."""
    
    @staticmethod
    def paginate_leaderboard(
        db: Session,
        page: int = 1,
        limit: int = 50,
        include_admin: bool = False
    ) -> Dict[str, Any]:
        """Paginate leaderboard with optimized ranking query."""
        
        # Base query for leaderboard
        base_query = """
            SELECT 
                u.id as user_id,
                u.name,
                u.total_points,
                u.shares_count,
                u.default_rank,
                u.current_rank,
                ROW_NUMBER() OVER (ORDER BY u.total_points DESC, u.created_at ASC) as calculated_rank
            FROM users u
            WHERE u.is_admin = :include_admin OR :include_admin = true
            ORDER BY u.total_points DESC, u.created_at ASC
        """
        
        # Count query
        count_query = """
            SELECT COUNT(*) 
            FROM users u 
            WHERE u.is_admin = :include_admin OR :include_admin = true
        """
        
        params = {"include_admin": include_admin}
        
        return PaginationHelper.paginate_raw_sql(
            db, base_query, count_query, params, page, limit
        )

class ShareHistoryPagination:
    """Specialized pagination for share history queries."""
    
    @staticmethod
    def paginate_user_shares(
        db: Session,
        user_id: int,
        page: int = 1,
        limit: int = 20,
        platform: Optional[str] = None
    ) -> Dict[str, Any]:
        """Paginate user's share history."""
        
        # Build WHERE clause
        where_clause = "WHERE se.user_id = :user_id"
        params = {"user_id": user_id}
        
        if platform:
            where_clause += " AND se.platform = :platform"
            params["platform"] = platform
        
        # Base query
        base_query = f"""
            SELECT 
                se.id,
                se.platform,
                se.points_earned,
                se.created_at
            FROM share_events se
            {where_clause}
            ORDER BY se.created_at DESC
        """
        
        # Count query
        count_query = f"""
            SELECT COUNT(*) 
            FROM share_events se 
            {where_clause}
        """
        
        return PaginationHelper.paginate_raw_sql(
            db, base_query, count_query, params, page, limit
        )

# Global instances
pagination_helper = PaginationHelper()
leaderboard_pagination = LeaderboardPagination()
share_history_pagination = ShareHistoryPagination()
