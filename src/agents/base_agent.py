"""Base agent class for specialized analysis."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional

from src.core.domain.models import Candidate, Vacancy


@dataclass
class AgentResult:
    """Result from an agent analysis."""

    agent_name: str
    agent_type: str
    score: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    findings: str  
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    details: Dict = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


class BaseAgent(ABC):
    """Base class for all specialized agents."""

    def __init__(self, gemini_client):
        """
        Initialize agent.

        Args:
            gemini_client: Gemini API client for AI analysis
        """
        self.gemini = gemini_client
        self.agent_type = self.__class__.__name__

    @abstractmethod
    def get_name(self) -> str:
        """Get agent display name."""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Get agent description."""
        pass

    @abstractmethod
    def is_relevant_for_vacancy(self, vacancy: Vacancy) -> bool:
        """
        Check if this agent is relevant for the given vacancy.

        Args:
            vacancy: Vacancy to check

        Returns:
            True if agent should analyze candidates for this vacancy
        """
        pass

    @abstractmethod
    async def analyze(
        self,
        candidate: Candidate,
        vacancy: Vacancy,
        context: Optional[Dict] = None,
    ) -> AgentResult:
        """
        Analyze candidate against vacancy.

        Args:
            candidate: Candidate to analyze
            vacancy: Vacancy requirements
            context: Additional context (test results, GitHub data, etc.)

        Returns:
            Analysis result with score and findings
        """
        pass

    async def _get_ai_analysis(
        self,
        prompt: str,
        temperature: float = 0.3,
    ) -> str:
        """
        Get analysis from Gemini.

        Args:
            prompt: Analysis prompt
            temperature: Sampling temperature

        Returns:
            AI response
        """
        return await self.gemini.generate_response(prompt, temperature)

    def _parse_agent_response(self, response: str) -> Dict:
        """
        Parse agent response from AI.

        Expected format:
        SCORE: 0.85
        CONFIDENCE: 0.9
        FINDINGS: Main findings here
        STRENGTHS: strength1 | strength2 | strength3
        WEAKNESSES: weakness1 | weakness2
        RECOMMENDATIONS: rec1 | rec2
        """
        result = {
            "score": 0.0,
            "confidence": 0.8,
            "findings": "",
            "strengths": [],
            "weaknesses": [],
            "recommendations": [],
        }

        lines = response.strip().split("\n")
        current_section = None

        for line in lines:
            line = line.strip()

            if line.startswith("SCORE:"):
                try:
                    result["score"] = float(line.replace("SCORE:", "").strip())
                except ValueError:
                    pass

            elif line.startswith("CONFIDENCE:"):
                try:
                    result["confidence"] = float(
                        line.replace("CONFIDENCE:", "").strip()
                    )
                except ValueError:
                    pass

            elif line.startswith("FINDINGS:"):
                result["findings"] = line.replace("FINDINGS:", "").strip()
                current_section = "findings"

            elif line.startswith("STRENGTHS:"):
                strengths_text = line.replace("STRENGTHS:", "").strip()
                if strengths_text:
                    result["strengths"] = [
                        s.strip() for s in strengths_text.split("|") if s.strip()
                    ]

            elif line.startswith("WEAKNESSES:"):
                weaknesses_text = line.replace("WEAKNESSES:", "").strip()
                if weaknesses_text:
                    result["weaknesses"] = [
                        w.strip() for w in weaknesses_text.split("|") if w.strip()
                    ]

            elif line.startswith("RECOMMENDATIONS:"):
                recs_text = line.replace("RECOMMENDATIONS:", "").strip()
                if recs_text:
                    result["recommendations"] = [
                        r.strip() for r in recs_text.split("|") if r.strip()
                    ]

            elif current_section == "findings" and line and not any(
                line.startswith(k)
                for k in [
                    "SCORE:",
                    "CONFIDENCE:",
                    "STRENGTHS:",
                    "WEAKNESSES:",
                    "RECOMMENDATIONS:",
                ]
            ):
                result["findings"] += " " + line

        return result

