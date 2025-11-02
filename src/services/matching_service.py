"""Matching service for managing vacancies and candidates."""

import logging
from typing import Dict, List, Optional
from uuid import UUID

from src.core.domain.models import Candidate, Vacancy
from src.core.domain.schemas import MatchingResult
from src.services.rag_service import RAGService

logger = logging.getLogger(__name__)


class MatchingService:
    """Service for managing matching operations."""

    def __init__(self, rag_service: RAGService):
        """
        Initialize matching service.

        Args:
            rag_service: RAG service instance
        """
        self.rag_service = rag_service

        self._vacancies: Dict[UUID, Vacancy] = {}
        self._candidates: Dict[UUID, Candidate] = {}

        logger.info("Matching service initialized")

    async def create_vacancy(self, vacancy: Vacancy) -> Vacancy:
        """
        Create a new vacancy.

        Args:
            vacancy: Vacancy object

        Returns:
            Created vacancy
        """
        self._vacancies[vacancy.id] = vacancy

        await self.rag_service.add_vacancy(vacancy)

        logger.info(f"Created vacancy: {vacancy.title} (ID: {vacancy.id})")
        return vacancy

    async def create_candidate(self, candidate: Candidate) -> Candidate:
        """
        Create a new candidate.

        Args:
            candidate: Candidate object

        Returns:
            Created candidate
        """
        self._candidates[candidate.id] = candidate

        await self.rag_service.add_candidate(candidate)

        logger.info(f"Created candidate: {candidate.name} (ID: {candidate.id})")
        return candidate

    async def get_vacancy(self, vacancy_id: UUID) -> Optional[Vacancy]:
        """Get vacancy by ID."""
        return self._vacancies.get(vacancy_id)

    async def get_candidate(self, candidate_id: UUID) -> Optional[Candidate]:
        """Get candidate by ID."""
        return self._candidates.get(candidate_id)

    async def list_vacancies(self) -> List[Vacancy]:
        """Get all vacancies."""
        return list(self._vacancies.values())

    async def list_candidates(self) -> List[Candidate]:
        """Get all candidates."""
        return list(self._candidates.values())

    async def find_candidates_for_vacancy(
        self,
        vacancy_id: UUID,
        top_k: int = 5,
        ai_analysis_limit: int = 2, 
    ) -> List[MatchingResult]:
        """
        Find best matching candidates for a vacancy.

        Args:
            vacancy_id: Vacancy ID
            top_k: Number of top matches to return
            ai_analysis_limit: Number of top candidates to analyze with AI agents

        Returns:
            List of matching results
        """
        vacancy = self._vacancies.get(vacancy_id)
        if not vacancy:
            raise ValueError(f"Vacancy {vacancy_id} not found")

        matches = await self.rag_service.find_matching_candidates(
            vacancy=vacancy,
            top_k=top_k,
            ai_analysis_limit=ai_analysis_limit,
        )

        results = []
        for match in matches:
            candidate_id = UUID(match["candidate_id"])
            candidate = self._candidates.get(candidate_id)

            details = {
                "vector_score": match.get("vector_score", 0),
                "screening_score": match.get("screening_score", 0),
                "screening_details": match.get("screening_details", {}),
                "agent_score": match.get("agent_score", 0),
                "ai_score": match.get("agent_score", 0), 
                "summary": match.get("summary", ""),
                "agent_results": match.get("agent_results", []),
                "total_agents": match.get("total_agents", 0),
                "candidate_name": match["metadata"].get("name", "Unknown"),
                "candidate_email": match["metadata"].get("email", ""),
            }

            if candidate:
                details.update({
                    "experience_years": candidate.experience_years,
                    "skills": candidate.skills,
                    "desired_position": candidate.desired_position,
                })

            results.append(
                MatchingResult(
                    entity_id=candidate_id,
                    score=match["combined_score"],
                    explanation=match.get("explanation", "No explanation available"),
                    details=details,
                )
            )

        logger.info(
            f"Found {len(results)} matching candidates for vacancy {vacancy_id}"
        )
        return results

    async def find_vacancies_for_candidate(
        self,
        candidate_id: UUID,
        top_k: int = 5,
    ) -> List[MatchingResult]:
        """
        Find best matching vacancies for a candidate.

        Args:
            candidate_id: Candidate ID
            top_k: Number of top matches to return

        Returns:
            List of matching results
        """
        candidate = self._candidates.get(candidate_id)
        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found")

        matches = await self.rag_service.find_matching_vacancies(
            candidate=candidate,
            top_k=top_k,
        )

        results = []
        for match in matches:
            vacancy_id = UUID(match["vacancy_id"])
            vacancy = self._vacancies.get(vacancy_id)

            details = {
                "vector_score": match["vector_score"],
                "ai_score": match["ai_score"],
                "strengths": match["strengths"],
                "weaknesses": match["weaknesses"],
                "vacancy_title": match["metadata"].get("title", "Unknown"),
                "vacancy_location": match["metadata"].get("location", ""),
            }

            if vacancy:
                details.update({
                    "required_experience": vacancy.experience_years,
                    "skills": vacancy.skills,
                    "employment_type": vacancy.employment_type,
                })

            results.append(
                MatchingResult(
                    entity_id=vacancy_id,
                    score=match["combined_score"],
                    explanation=match["explanation"],
                    details=details,
                )
            )

        logger.info(
            f"Found {len(results)} matching vacancies for candidate {candidate_id}"
        )
        return results

    async def find_all_vacancies_with_candidates(
        self,
        top_k: int = 5,
        use_ai: bool = False,
    ) -> Dict[str, List[MatchingResult]]:
        """
        Find matching candidates for all vacancies.

        Args:
            top_k: Number of top candidates to return for each vacancy
            use_ai: Whether to use AI agents (expensive and slow)

        Returns:
            Dictionary with vacancy IDs as keys and lists of matching candidates as values
        """
        logger.info(f"Finding candidates for all {len(self._vacancies)} vacancies (use_ai={use_ai})")

        results = {}
        
        for vacancy in self._vacancies.values():
            try:
                if use_ai:
                    matches = await self.rag_service.find_matching_candidates(
                        vacancy=vacancy,
                        top_k=top_k,
                        ai_analysis_limit=2,
                    )
                else:
                    matches = await self.rag_service.find_matching_candidates_without_ai(
                        vacancy=vacancy,
                        top_k=top_k,
                    )

                vacancy_results = []
                for match in matches:
                    candidate_id = UUID(match["candidate_id"])
                    candidate = self._candidates.get(candidate_id)

                    details = {
                        "vector_score": match.get("vector_score", 0),
                        "screening_score": match.get("screening_score", 0),
                        "screening_details": match.get("screening_details", {}),
                        "agent_score": match.get("agent_score", 0),
                        "ai_score": match.get("agent_score", 0),
                        "summary": match.get("summary", ""),
                        "agent_results": match.get("agent_results", []),
                        "total_agents": match.get("total_agents", 0),
                        "candidate_name": match["metadata"].get("name", "Unknown"),
                        "candidate_email": match["metadata"].get("email", ""),
                    }

                    if candidate:
                        details.update({
                            "experience_years": candidate.experience_years,
                            "skills": candidate.skills,
                            "desired_position": candidate.desired_position,
                        })

                    vacancy_results.append(
                        MatchingResult(
                            entity_id=candidate_id,
                            score=match["combined_score"],
                            explanation=match.get("explanation", "No explanation available"),
                            details=details,
                        )
                    )

                # Добавляем ранги к кандидатам
                ranked_candidates = []
                for rank, candidate_result in enumerate(vacancy_results, start=1):
                    ranked_candidates.append({
                        "rank": rank,
                        "candidate_id": str(candidate_result.entity_id),
                        "candidate_name": candidate_result.details.get("candidate_name", "Unknown"),
                        "score": candidate_result.score,
                        "details": candidate_result,
                    })
                
                results[str(vacancy.id)] = {
                    "vacancy_id": str(vacancy.id),
                    "vacancy_title": vacancy.title,
                    "vacancy_location": vacancy.location or "",
                    "candidates_count": len(vacancy_results),
                    "ranked_candidates": ranked_candidates,  # С рангами
                    "candidates": vacancy_results,  # Оставляем для обратной совместимости
                }

                logger.info(
                    f"Found {len(vacancy_results)} candidates for vacancy '{vacancy.title}' ({vacancy.id})"
                )

            except Exception as e:
                logger.error(f"Error finding candidates for vacancy {vacancy.id}: {e}")
                results[str(vacancy.id)] = {
                    "vacancy_id": str(vacancy.id),
                    "vacancy_title": vacancy.title,
                    "vacancy_location": vacancy.location or "",
                    "candidates_count": 0,
                    "candidates": [],
                    "error": str(e),
                }

        logger.info(f"Completed matching for all vacancies")
        return results

