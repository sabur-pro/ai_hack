"""Multi-stage screening service for better candidate filtering."""

import logging
from typing import Dict, List, Optional, Set
from uuid import UUID

from src.core.domain.models import Candidate, Vacancy

logger = logging.getLogger(__name__)


class ScreeningService:
    """
    Multi-stage screening service for pre-filtering candidates.
    
    Reduces the candidate pool before expensive AI agent analysis.
    Enhanced with semantic skill matching using PyTorch.
    """

    def __init__(self, use_semantic_matching: bool = True):
        """
        Initialize screening service.
        
        Args:
            use_semantic_matching: Use PyTorch-based semantic skill matching
        """
        self.use_semantic_matching = use_semantic_matching
        self.reranking_service = None
        
        if use_semantic_matching:
            try:
                from src.services.reranking_service import RerankingService
                self.reranking_service = RerankingService()
                logger.info("Screening service initialized with semantic matching (PyTorch)")
            except Exception as e:
                logger.warning(f"Failed to initialize semantic matching: {e}")
                logger.info("Falling back to basic string matching")
                self.use_semantic_matching = False
        else:
            logger.info("Screening service initialized (basic mode)")

    def calculate_hard_skills_match(
        self, 
        candidate_skills: List[str], 
        required_skills: List[str],
        return_details: bool = False
    ) -> float:
        """
        Calculate hard skills match percentage.
        
        Uses semantic matching with PyTorch if enabled, otherwise basic string matching.

        Args:
            candidate_skills: Candidate's skills
            required_skills: Required skills from vacancy
            return_details: Return detailed matching info

        Returns:
            Match percentage (0.0 to 1.0) or tuple with details
        """
        if not required_skills:
            return (1.0, {}) if return_details else 1.0

        # Попытка использовать семантическое сравнение
        if self.use_semantic_matching and self.reranking_service:
            try:
                result = self.reranking_service.calculate_semantic_skill_match(
                    candidate_skills=candidate_skills,
                    required_skills=required_skills,
                    threshold=0.7  # 70% similarity для совпадения
                )
                
                score = result['match_score']
                
                # Бонус за точные совпадения
                exact_matches = {skill.lower() for skill in candidate_skills}.intersection(
                    {skill.lower() for skill in required_skills}
                )
                if exact_matches:
                    bonus = len(exact_matches) * 0.05  # +5% за каждое точное совпадение
                    score = min(1.0, score + bonus)
                
                if return_details:
                    result['final_score'] = score
                    result['exact_matches'] = list(exact_matches)
                    return score, result
                
                return score
                
            except Exception as e:
                logger.warning(f"Semantic matching failed: {e}, using basic matching")
                # Fallback to basic matching
        
        # Базовое сравнение строк (fallback)
        candidate_skills_lower = {skill.lower() for skill in candidate_skills}
        required_skills_lower = {skill.lower() for skill in required_skills}

        matches = candidate_skills_lower.intersection(required_skills_lower)
        match_percentage = len(matches) / len(required_skills_lower)

        if return_details:
            details = {
                'matched_skills': list(matches),
                'unmatched_skills': list(required_skills_lower - candidate_skills_lower),
                'semantic_matches': []
            }
            return match_percentage, details

        return match_percentage

    def calculate_experience_match(
        self, candidate_years: int, required_years: int, tolerance: int = 1
    ) -> float:
        """
        Calculate experience match score.

        Args:
            candidate_years: Candidate's years of experience
            required_years: Required years of experience
            tolerance: Acceptable difference in years

        Returns:
            Match score (0.0 to 1.0)
        """
        if required_years == 0:
            return 1.0

        diff = abs(candidate_years - required_years)

        if diff == 0:
            return 1.0
        elif diff <= tolerance:
            return 0.8
        elif candidate_years > required_years:
            return max(0.6, 1.0 - (diff - tolerance) * 0.1)
        else:
            return max(0.3, 1.0 - (diff - tolerance) * 0.15)

    def calculate_keyword_boost(
        self, candidate_text: str, vacancy_text: str, keywords: List[str]
    ) -> float:
        """
        Calculate boost based on important keywords presence.

        Args:
            candidate_text: Candidate's summary/experience
            vacancy_text: Vacancy description
            keywords: Important keywords from vacancy

        Returns:
            Boost score (0.0 to 0.2)
        """
        candidate_lower = candidate_text.lower()
        vacancy_lower = vacancy_text.lower()

        if not keywords:
            keywords = self._extract_keywords(vacancy_lower)

        matches = sum(1 for keyword in keywords if keyword.lower() in candidate_lower)

        if not keywords:
            return 0.0

        boost = min(0.2, (matches / len(keywords)) * 0.2)
        return boost

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text."""
        important_keywords = [
            "senior",
            "lead",
            "architect",
            "microservices",
            "cloud",
            "aws",
            "azure",
            "gcp",
            "kubernetes",
            "docker",
            "ci/cd",
            "agile",
            "scrum",
            "tdd",
            "rest",
            "api",
            "database",
            "sql",
            "nosql",
            "python",
            "java",
            "javascript",
            "react",
            "angular",
            "vue",
        ]

        return [kw for kw in important_keywords if kw in text]

    def calculate_location_match(
        self, candidate_location: str, vacancy_location: str
    ) -> float:
        """
        Calculate location match score.

        Args:
            candidate_location: Candidate's location
            vacancy_location: Vacancy location

        Returns:
            Match score (0.0 to 1.0)
        """
        if not vacancy_location or not candidate_location:
            return 1.0 

        candidate_lower = candidate_location.lower()
        vacancy_lower = vacancy_location.lower()

        if candidate_lower == vacancy_lower:
            return 1.0

        if "remote" in vacancy_lower or "удален" in vacancy_lower:
            return 1.0

        if "remote" in candidate_lower or "удален" in candidate_lower:
            return 0.9

        if candidate_lower in vacancy_lower or vacancy_lower in candidate_lower:
            return 0.9

        if "релокация" in candidate_lower or "relocation" in candidate_lower:
            return 0.7

        return 0.5

    def screen_candidate(
        self, candidate: Candidate, vacancy: Vacancy, vector_score: float
    ) -> Dict:
        """
        Perform multi-stage screening of candidate.

        Args:
            candidate: Candidate to screen
            vacancy: Vacancy requirements
            vector_score: Vector similarity score from ChromaDB

        Returns:
            Screening result with scores and decision
        """
        hard_skills_score = self.calculate_hard_skills_match(
            candidate.skills, vacancy.skills
        )

        experience_score = self.calculate_experience_match(
            candidate.experience_years, vacancy.experience_years or 0
        )

        location_score = self.calculate_location_match(
            candidate.location or "", vacancy.location or ""
        )

        candidate_text = (
            candidate.summary + " " + " ".join(candidate.skills + candidate.experience)
        )
        vacancy_text = (
            vacancy.description
            + " "
            + " ".join(vacancy.skills + vacancy.requirements)
        )
        keyword_boost = self.calculate_keyword_boost(
            candidate_text, vacancy_text, vacancy.skills
        )

        screening_score = (
            vector_score * 0.4
            + hard_skills_score * 0.3
            + experience_score * 0.2
            + location_score * 0.1
            + keyword_boost 
        )

        if screening_score >= 0.6:
            decision = "PASS"  
        elif screening_score >= 0.4:
            decision = "MAYBE" 
        else:
            decision = "REJECT"  

        result = {
            "screening_score": screening_score,
            "vector_score": vector_score,
            "hard_skills_score": hard_skills_score,
            "experience_score": experience_score,
            "location_score": location_score,
            "keyword_boost": keyword_boost,
            "decision": decision,
            "details": {
                "candidate_skills": len(candidate.skills),
                "required_skills": len(vacancy.skills),
                "skills_matched": int(
                    hard_skills_score * len(vacancy.skills) if vacancy.skills else 0
                ),
                "experience_diff": abs(
                    candidate.experience_years - (vacancy.experience_years or 0)
                ),
            },
        }

        logger.debug(
            f"Screening result for {candidate.name}: "
            f"score={screening_score:.2f}, decision={decision}"
        )

        return result

    def filter_candidates(
        self,
        candidates_with_scores: List[Dict],
        vacancy: Vacancy,
        min_screening_score: float = 0.4,
        top_k: int = 10,
    ) -> List[Dict]:
        """
        Filter and rank candidates using multi-stage screening.

        Args:
            candidates_with_scores: Candidates with vector scores from ChromaDB
            vacancy: Vacancy requirements
            min_screening_score: Minimum screening score to pass
            top_k: Maximum number of candidates to return

        Returns:
            Filtered and ranked candidates
        """
        screened_candidates = []

        logger.info(f"Screening {len(candidates_with_scores)} candidates...")

        for candidate_data in candidates_with_scores:
            from src.core.domain.models import Candidate as CandidateModel

            candidate = CandidateModel(
                name=candidate_data["metadata"].get("name", "Unknown"),
                email=candidate_data["metadata"].get("email", "unknown@example.com"),
                summary=candidate_data["document"],
                skills=candidate_data["metadata"].get("skills", "").split(",")
                if candidate_data["metadata"].get("skills")
                else [],
                experience=candidate_data["metadata"].get("experience", "").split("|")
                if candidate_data["metadata"].get("experience")
                else [],
                education=[],
                experience_years=candidate_data["metadata"].get("experience_years", 0),
                location=candidate_data["metadata"].get("location", ""),
            )

            screening_result = self.screen_candidate(
                candidate, vacancy, candidate_data["score"]
            )

            candidate_data["screening"] = screening_result

            if screening_result["screening_score"] >= min_screening_score:
                screened_candidates.append(candidate_data)

        screened_candidates.sort(
            key=lambda x: x["screening"]["screening_score"], reverse=True
        )

        top_candidates = screened_candidates[:top_k]

        logger.info(
            f"Screening complete: {len(screened_candidates)}/{len(candidates_with_scores)} "
            f"passed threshold, returning top {len(top_candidates)}"
        )

        return top_candidates

