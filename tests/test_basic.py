"""Basic tests for HR AI Agent."""

import pytest
from uuid import UUID

from src.core.domain.models import Candidate, Vacancy


def test_vacancy_creation():
    """Test vacancy creation."""
    vacancy = Vacancy(
        title="Python Developer",
        description="Looking for experienced Python developer",
        skills=["Python", "FastAPI"],
        experience_years=3,
    )

    assert vacancy.title == "Python Developer"
    assert isinstance(vacancy.id, UUID)
    assert vacancy.experience_years == 3
    assert "Python" in vacancy.skills


def test_candidate_creation():
    """Test candidate creation."""
    candidate = Candidate(
        name="John Doe",
        email="john@example.com",
        summary="Experienced Python developer with 5 years of experience",
        skills=["Python", "Django", "PostgreSQL"],
        experience_years=5,
    )

    assert candidate.name == "John Doe"
    assert isinstance(candidate.id, UUID)
    assert candidate.experience_years == 5
    assert "Python" in candidate.skills


def test_vacancy_to_text():
    """Test vacancy to text conversion."""
    vacancy = Vacancy(
        title="Senior Developer",
        description="Great opportunity",
        skills=["Python", "Docker"],
        requirements=["5+ years experience"],
        experience_years=5,
    )

    text = vacancy.to_text()

    assert "Senior Developer" in text
    assert "Great opportunity" in text
    assert "Python" in text
    assert "Docker" in text


def test_candidate_to_text():
    """Test candidate to text conversion."""
    candidate = Candidate(
        name="Jane Smith",
        email="jane@example.com",
        summary="Expert developer",
        skills=["Python", "FastAPI"],
        experience=["5 years at TechCorp"],
        experience_years=5,
    )

    text = candidate.to_text()

    assert "Jane Smith" in text
    assert "Expert developer" in text
    assert "Python" in text
    assert "5 years at TechCorp" in text


def test_email_validation():
    """Test email validation."""
    with pytest.raises(Exception): 
        Candidate(
            name="Test",
            email="invalid-email",  # Invalid email
            summary="Test summary",
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

