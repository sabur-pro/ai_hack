"""RAG (Retrieval Augmented Generation) service."""

import logging
from typing import Dict, List
from uuid import UUID

from src.agents import AgentCoordinator
from src.core.domain.models import Candidate, Vacancy
from src.infrastructure.ai import GeminiClient
from src.infrastructure.vector_db import ChromaRepository
from src.services.screening_service import ScreeningService

logger = logging.getLogger(__name__)


class RAGService:
    """Service for RAG-based operations."""

    def __init__(
        self,
        gemini_client: GeminiClient,
        vector_repository: ChromaRepository,
        use_reranking: bool = True,
        use_semantic_skills: bool = True,
    ):
        """
        Initialize RAG service.

        Args:
            gemini_client: Gemini API client
            vector_repository: Vector database repository
            use_reranking: Use Cross-Encoder reranking (PyTorch)
            use_semantic_skills: Use semantic skill matching (PyTorch)
        """
        self.gemini = gemini_client
        self.vector_db = vector_repository
        self.agent_coordinator = AgentCoordinator(gemini_client)
        self.screening_service = ScreeningService(use_semantic_matching=use_semantic_skills)
        
        # Reranking service (опционально)
        self.use_reranking = use_reranking
        self.reranking_service = None
        
        if use_reranking:
            try:
                from src.services.reranking_service import RerankingService
                self.reranking_service = RerankingService()
                logger.info("RAG service initialized with reranking (PyTorch)")
            except Exception as e:
                logger.warning(f"Failed to initialize reranking: {e}")
                self.use_reranking = False
        
        logger.info(
            f"RAG service initialized: "
            f"reranking={'enabled' if self.use_reranking else 'disabled'}, "
            f"semantic_skills={'enabled' if use_semantic_skills else 'disabled'}"
        )

    async def add_vacancy(self, vacancy: Vacancy) -> None:
        """
        Add vacancy to the system.

        Args:
            vacancy: Vacancy object to add
        """
        vacancy_text = vacancy.to_text()

        metadata = {
            "title": vacancy.title,
            "location": vacancy.location or "",
            "experience_years": vacancy.experience_years or 0,
            "employment_type": vacancy.employment_type,
        }

        await self.vector_db.add_vacancy(
            vacancy_id=vacancy.id,
            vacancy_text=vacancy_text,
            metadata=metadata,
        )

        logger.info(f"Added vacancy '{vacancy.title}' to RAG system")

    async def add_candidate(self, candidate: Candidate) -> None:
        """
        Add candidate to the system.

        Args:
            candidate: Candidate object to add
        """
        candidate_text = candidate.to_text()

        metadata = {
            "name": candidate.name,
            "email": candidate.email,
            "desired_position": candidate.desired_position or "",
            "experience_years": candidate.experience_years or 0,
            "location": candidate.location or "",
        }

        await self.vector_db.add_candidate(
            candidate_id=candidate.id,
            candidate_text=candidate_text,
            metadata=metadata,
        )

        logger.info(f"Added candidate '{candidate.name}' to RAG system")

    async def find_matching_candidates(
        self,
        vacancy: Vacancy,
        top_k: int = 5,
        ai_analysis_limit: int = 2,  
    ) -> List[Dict]:
        """
        Find candidates matching a vacancy using RAG.

        Args:
            vacancy: Vacancy to match
            top_k: Number of top candidates to return after screening
            ai_analysis_limit: Number of top candidates to analyze with AI agents (expensive)

        Returns:
            List of matching candidates with AI analysis
        """
        logger.info(f"Finding matches for vacancy: {vacancy.title}")

        vacancy_text = vacancy.to_text()
        similar_candidates = await self.vector_db.search_candidates(
            vacancy_text=vacancy_text,
            top_k=top_k * 5,
        )

        if not similar_candidates:
            logger.info("No candidates found in vector database")
            return []

        logger.info(f"Vector search found {len(similar_candidates)} candidates")

        screened_candidates = self.screening_service.filter_candidates(
            candidates_with_scores=similar_candidates,
            vacancy=vacancy,
            min_screening_score=0.4, 
            top_k=top_k,  
        )

        if not screened_candidates:
            logger.info("No candidates passed screening")
            return []

        logger.info(
            f"Screening passed: {len(screened_candidates)} candidates"
        )
        
        candidates_for_ai = screened_candidates[:ai_analysis_limit]
        logger.info(
            f"AI multi-agent analysis will be performed for top {len(candidates_for_ai)} candidates"
        )

        results = []
        for idx, candidate_data in enumerate(candidates_for_ai):
            try:
                from src.core.domain.models import Candidate as CandidateModel

                candidate = CandidateModel(
                    name=candidate_data["metadata"].get("name", "Unknown"),
                    email=candidate_data["metadata"].get(
                        "email", "unknown@example.com"
                    ),
                    summary=candidate_data["document"],
                    skills=[],
                    experience=[],
                    education=[],
                    experience_years=candidate_data["metadata"].get(
                        "experience_years", 0
                    ),
                )

                agent_analysis = await self.agent_coordinator.analyze_candidate(
                    candidate=candidate,
                    vacancy=vacancy,
                    context={
                        "vector_score": candidate_data["score"],
                        "screening_score": candidate_data["screening"]["screening_score"],
                        "github_info": "", 
                        "test_results": "",  
                        "achievements": "",  
                    },
                    sequential=True,  
                )
                
                if idx < len(candidates_for_ai) - 1:
                    logger.info(f"Waiting 20s before analyzing next candidate...")
                    import asyncio
                    await asyncio.sleep(20)


                screening_score = candidate_data["screening"]["screening_score"]
                vector_score = candidate_data["score"]
                agent_score = agent_analysis["overall_score"]
                
                combined_score = (
                    screening_score * 0.3 + vector_score * 0.2 + agent_score * 0.5
                )

                results.append({
                    "candidate_id": candidate_data["id"],
                    "vector_score": vector_score,
                    "screening_score": screening_score,
                    "screening_details": candidate_data["screening"],
                    "agent_score": agent_score,
                    "combined_score": combined_score,
                    "explanation": agent_analysis["summary"],  
                    "summary": agent_analysis["summary"],
                    "agent_results": agent_analysis["agent_results"],
                    "total_agents": agent_analysis["total_agents"],
                    "metadata": candidate_data["metadata"],
                })

            except Exception as e:
                logger.error(f"Error analyzing candidate {candidate_data['id']}: {e}")
                continue

        results.sort(key=lambda x: x["combined_score"], reverse=True)

        logger.info(f"Found {len(results)} matching candidates")
        return results

    async def find_matching_candidates_without_ai(
        self,
        vacancy: Vacancy,
        top_k: int = 5,
    ) -> List[Dict]:
        """
        Find candidates matching a vacancy using only vector search and screening (no AI).
        
        Enhanced with:
        - Cross-Encoder reranking for precise scoring (PyTorch)
        - Semantic skill matching (PyTorch)

        Args:
            vacancy: Vacancy to match
            top_k: Number of top candidates to return after screening

        Returns:
            List of matching candidates with screening scores only
        """
        logger.info(f"Finding matches (no AI) for vacancy: {vacancy.title}")

        vacancy_text = vacancy.to_text()
        similar_candidates = await self.vector_db.search_candidates(
            vacancy_text=vacancy_text,
            top_k=top_k * 5,
        )

        if not similar_candidates:
            logger.info("No candidates found in vector database")
            return []

        logger.info(f"Vector search found {len(similar_candidates)} candidates")
        
        # НОВОЕ: Реранкинг с Cross-Encoder для более точной оценки
        if self.use_reranking and self.reranking_service:
            try:
                similar_candidates = self.reranking_service.rerank_candidates(
                    vacancy_text=vacancy_text,
                    candidates=similar_candidates,
                    top_k=min(len(similar_candidates), top_k * 2)
                )
                logger.info(f"Reranked candidates using Cross-Encoder")
            except Exception as e:
                logger.warning(f"Reranking failed: {e}, using original scores")

        screened_candidates = self.screening_service.filter_candidates(
            candidates_with_scores=similar_candidates,
            vacancy=vacancy,
            min_screening_score=0.3, 
            top_k=top_k,
        )

        if not screened_candidates:
            logger.info("No candidates passed screening")
            return []

        logger.info(f"Screening passed: {len(screened_candidates)} candidates")

        results = []
        for candidate_data in screened_candidates:
            screening_score = candidate_data["screening"]["screening_score"]
            vector_score = candidate_data["score"]
            
            combined_score = screening_score * 0.6 + vector_score * 0.4

            explanation_parts = []
            screening = candidate_data["screening"]
            
            if screening["hard_skills_score"] >= 0.7:
                explanation_parts.append("Отличное совпадение навыков")
            elif screening["hard_skills_score"] >= 0.5:
                explanation_parts.append("Хорошее совпадение навыков")
            else:
                explanation_parts.append("Частичное совпадение навыков")
            
            if screening["experience_score"] >= 0.8:
                explanation_parts.append("опыт полностью соответствует")
            elif screening["experience_score"] >= 0.6:
                explanation_parts.append("опыт приемлем")
            else:
                explanation_parts.append("опыт требует проверки")
            
            if screening["location_score"] >= 0.9:
                explanation_parts.append("локация идеально подходит")
            elif screening["location_score"] >= 0.7:
                explanation_parts.append("локация подходит")

            explanation = "; ".join(explanation_parts)

            results.append({
                "candidate_id": candidate_data["id"],
                "vector_score": vector_score,
                "screening_score": screening_score,
                "screening_details": candidate_data["screening"],
                "agent_score": 0,  
                "combined_score": combined_score,
                "explanation": explanation,
                "summary": f"Кандидат {candidate_data['metadata'].get('name', 'Unknown')}: {explanation}",
                "agent_results": [],
                "total_agents": 0,
                "metadata": candidate_data["metadata"],
            })

        results.sort(key=lambda x: x["combined_score"], reverse=True)

        logger.info(f"Found {len(results)} matching candidates (without AI)")
        return results

    async def find_matching_vacancies(
        self,
        candidate: Candidate,
        top_k: int = 5,
    ) -> List[Dict]:
        """
        Find vacancies matching a candidate using RAG.

        Args:
            candidate: Candidate to match
            top_k: Number of top vacancies to return

        Returns:
            List of matching vacancies with AI analysis
        """
        logger.info(f"Finding matches for candidate: {candidate.name}")

        candidate_text = candidate.to_text()
        similar_vacancies = await self.vector_db.search_vacancies(
            candidate_text=candidate_text,
            top_k=top_k * 2,
        )

        if not similar_vacancies:
            logger.info("No vacancies found in vector database")
            return []

        results = []
        for vacancy_data in similar_vacancies[:top_k]:
            try:
                context = f"Similarity score from vector search: {vacancy_data['score']:.2f}"

                analysis = await self.gemini.analyze_matching(
                    vacancy_text=vacancy_data["document"],
                    candidate_text=candidate_text,
                    context=context,
                )

                results.append({
                    "vacancy_id": vacancy_data["id"],
                    "vector_score": vacancy_data["score"],
                    "ai_score": analysis["score"],
                    "combined_score": (vacancy_data["score"] + analysis["score"]) / 2,
                    "explanation": analysis["explanation"],
                    "strengths": analysis.get("strengths", ""),
                    "weaknesses": analysis.get("weaknesses", ""),
                    "metadata": vacancy_data["metadata"],
                })

            except Exception as e:
                logger.error(f"Error analyzing vacancy {vacancy_data['id']}: {e}")
                continue

        results.sort(key=lambda x: x["combined_score"], reverse=True)

        logger.info(f"Found {len(results)} matching vacancies")
        return results

    async def get_vacancy(self, vacancy_id: UUID) -> dict:
        """Get vacancy from vector database."""
        return await self.vector_db.get_vacancy(vacancy_id)

    async def get_candidate(self, candidate_id: UUID) -> dict:
        """Get candidate from vector database."""
        return await self.vector_db.get_candidate(candidate_id)

