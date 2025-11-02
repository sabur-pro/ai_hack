"""API schemas for requests and responses."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class VacancyCreate(BaseModel):
    """Schema for creating a vacancy."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10)
    requirements: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    experience_years: Optional[int] = Field(default=None, ge=0)
    salary_range: Optional[str] = None
    location: Optional[str] = None
    employment_type: str = Field(default="full-time")


class VacancyResponse(BaseModel):
    """Schema for vacancy response."""

    id: UUID
    title: str
    description: str
    requirements: List[str]
    responsibilities: List[str]
    skills: List[str]
    experience_years: Optional[int]
    salary_range: Optional[str]
    location: Optional[str]
    employment_type: str
    created_at: datetime


class CandidateCreate(BaseModel):
    """Schema for creating a candidate."""

    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    phone: Optional[str] = None
    summary: str = Field(..., min_length=10)
    skills: List[str] = Field(default_factory=list)
    experience: List[str] = Field(default_factory=list)
    education: List[str] = Field(default_factory=list)
    experience_years: Optional[int] = Field(default=None, ge=0)
    desired_position: Optional[str] = None
    desired_salary: Optional[str] = None
    location: Optional[str] = None


class CandidateResponse(BaseModel):
    """Schema for candidate response."""

    id: UUID
    name: str
    email: str
    phone: Optional[str]
    summary: str
    skills: List[str]
    experience: List[str]
    education: List[str]
    experience_years: Optional[int]
    desired_position: Optional[str]
    desired_salary: Optional[str]
    location: Optional[str]
    created_at: datetime


class MatchingResult(BaseModel):
    """Schema for matching result."""

    entity_id: UUID
    score: float = Field(..., ge=0.0, le=1.0)
    explanation: str
    details: dict = Field(default_factory=dict)


class MatchingRequest(BaseModel):
    """Schema for matching request."""

    entity_id: UUID
    top_k: int = Field(default=5, ge=1, le=20)


class RankedCandidate(BaseModel):
    """Ranked candidate with simple format."""
    
    rank: int
    candidate_id: str
    candidate_name: str
    score: float
    details: MatchingResult


class VacancyWithCandidates(BaseModel):
    """Schema for vacancy with matched candidates."""

    vacancy_id: str
    vacancy_title: str
    vacancy_location: str
    candidates_count: int
    candidates: List[MatchingResult]
    error: Optional[str] = None


class BulkMatchingResponse(BaseModel):
    """Schema for bulk matching response."""

    total_vacancies: int
    vacancies: dict  # Dict[str, VacancyWithCandidates]