"""Domain models for HR AI Agent."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Vacancy(BaseModel):
    """Vacancy domain model."""

    id: UUID = Field(default_factory=uuid4)
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10)
    requirements: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    experience_years: Optional[int] = Field(default=None, ge=0)
    salary_range: Optional[str] = None
    location: Optional[str] = None
    employment_type: str = Field(default="full-time")  
    created_at: datetime = Field(default_factory=datetime.now)

    def to_text(self) -> str:
        """Convert vacancy to text representation for embedding."""
        text_parts = [
            f"Вакансия: {self.title}",
            f"Описание: {self.description}",
        ]

        if self.requirements:
            text_parts.append(f"Требования: {', '.join(self.requirements)}")

        if self.responsibilities:
            text_parts.append(f"Обязанности: {', '.join(self.responsibilities)}")

        if self.skills:
            text_parts.append(f"Навыки: {', '.join(self.skills)}")

        if self.experience_years is not None:
            text_parts.append(f"Опыт работы: {self.experience_years} лет")

        if self.location:
            text_parts.append(f"Локация: {self.location}")

        return " | ".join(text_parts)


class Candidate(BaseModel):
    """Candidate domain model."""

    id: UUID = Field(default_factory=uuid4)
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
    created_at: datetime = Field(default_factory=datetime.now)

    def to_text(self) -> str:
        """Convert candidate to text representation for embedding."""
        text_parts = [
            f"Кандидат: {self.name}",
            f"Резюме: {self.summary}",
        ]

        if self.desired_position:
            text_parts.append(f"Желаемая позиция: {self.desired_position}")

        if self.skills:
            text_parts.append(f"Навыки: {', '.join(self.skills)}")

        if self.experience:
            text_parts.append(f"Опыт: {' | '.join(self.experience)}")

        if self.education:
            text_parts.append(f"Образование: {', '.join(self.education)}")

        if self.experience_years is not None:
            text_parts.append(f"Лет опыта: {self.experience_years}")

        if self.location:
            text_parts.append(f"Локация: {self.location}")

        return " | ".join(text_parts)

