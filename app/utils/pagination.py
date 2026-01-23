"""
Pagination utilities for API endpoints.
"""
from typing import Generic, TypeVar, Optional, List
from pydantic import BaseModel

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Pagination parameters for API requests."""
    skip: int = 0
    limit: int = 50
    
    class Config:
        """Pydantic config."""
        validate_assignment = True
    
    def validate_limit(self) -> int:
        """Validate and constrain limit to reasonable values."""
        if self.limit < 1:
            return 1
        if self.limit > 100:
            return 100
        return self.limit
    
    def validate_skip(self) -> int:
        """Validate skip is non-negative."""
        if self.skip < 0:
            return 0
        return self.skip


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response model."""
    items: List[T]
    total: int
    skip: int
    limit: int
    has_more: bool
    
    class Config:
        """Pydantic config."""
        from_attributes = True


def create_paginated_response(
    items: List[T],
    total: int,
    skip: int,
    limit: int
) -> PaginatedResponse[T]:
    """
    Create a paginated response.
    
    Args:
        items: List of items for current page
        total: Total number of items
        skip: Number of items skipped
        limit: Maximum number of items per page
    
    Returns:
        PaginatedResponse with items and metadata
    """
    return PaginatedResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
        has_more=(skip + len(items)) < total
    )
