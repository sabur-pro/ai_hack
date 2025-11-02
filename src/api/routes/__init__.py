"""API routes."""

from .candidates import router as candidates_router
from .matching import router as matching_router
from .vacancies import router as vacancies_router

__all__ = ["vacancies_router", "candidates_router", "matching_router"]

