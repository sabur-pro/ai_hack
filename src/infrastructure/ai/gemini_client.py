"""Google Gemini API client."""

import logging
from typing import Optional

import google.generativeai as genai

from src.core.config import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for interacting with Google Gemini API."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini client.

        Args:
            api_key: Gemini API key. If not provided, uses settings.
        """
        self.api_key = api_key or settings.api_gemini
        genai.configure(api_key=self.api_key)

        try:
            self.model = genai.GenerativeModel("gemini-2.0-flash-lite")
            logger.info("Gemini client initialized with model: gemini-2.0-flash-lite")
        except Exception:
            self.model = genai.GenerativeModel("gemini-1.5-flash")
            logger.info("Gemini client initialized with model: gemini-1.5-flash")

    async def generate_response(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate a response using Gemini.

        Args:
            prompt: The prompt to send to Gemini
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated response text
        """
        try:
            generation_config = {
                "temperature": temperature,
            }

            if max_tokens:
                generation_config["max_output_tokens"] = max_tokens

            response = self.model.generate_content(
                prompt,
                generation_config=generation_config,
            )

            return response.text

        except Exception as e:
            logger.error(f"Error generating response from Gemini: {e}")
            raise

    async def analyze_matching(
        self,
        vacancy_text: str,
        candidate_text: str,
        context: Optional[str] = None,
    ) -> dict:
        """
        Analyze matching between vacancy and candidate using Gemini.

        Args:
            vacancy_text: Text representation of vacancy
            candidate_text: Text representation of candidate
            context: Additional context from RAG

        Returns:
            Dictionary with score and explanation
        """
        prompt = self._build_matching_prompt(vacancy_text, candidate_text, context)

        try:
            response = await self.generate_response(prompt, temperature=0.3)
            return self._parse_matching_response(response)

        except Exception as e:
            logger.error(f"Error analyzing matching: {e}")
            raise

    def _build_matching_prompt(
        self,
        vacancy_text: str,
        candidate_text: str,
        context: Optional[str] = None,
    ) -> str:
        """Build prompt for matching analysis."""
        prompt = f"""Ты HR эксперт. Проанализируй соответствие кандидата вакансии.

ВАКАНСИЯ:
{vacancy_text}

КАНДИДАТ:
{candidate_text}
"""

        if context:
            prompt += f"\n\nДОПОЛНИТЕЛЬНЫЙ КОНТЕКСТ:\n{context}\n"

        prompt += """
Оцени соответствие по шкале от 0 до 1 (где 1 - идеальное соответствие).

Предоставь ответ в следующем формате:
SCORE: [число от 0 до 1]
EXPLANATION: [подробное объяснение оценки]
STRENGTHS: [сильные стороны кандидата для этой вакансии]
WEAKNESSES: [слабые стороны или недостающие навыки]
"""

        return prompt

    def _parse_matching_response(self, response: str) -> dict:
        """Parse matching response from Gemini."""
        result = {
            "score": 0.0,
            "explanation": "",
            "strengths": "",
            "weaknesses": "",
        }

        lines = response.strip().split("\n")

        for line in lines:
            line = line.strip()

            if line.startswith("SCORE:"):
                try:
                    score_str = line.replace("SCORE:", "").strip()
                    result["score"] = float(score_str)
                except ValueError:
                    logger.warning(f"Could not parse score: {line}")

            elif line.startswith("EXPLANATION:"):
                result["explanation"] = line.replace("EXPLANATION:", "").strip()

            elif line.startswith("STRENGTHS:"):
                result["strengths"] = line.replace("STRENGTHS:", "").strip()

            elif line.startswith("WEAKNESSES:"):
                result["weaknesses"] = line.replace("WEAKNESSES:", "").strip()

        # If explanation is still empty, use the entire response
        if not result["explanation"]:
            result["explanation"] = response.strip()

        return result

    async def answer_question(self, question: str) -> str:
        """
        Answer a general question using Gemini.

        Args:
            question: The question to answer

        Returns:
            Answer text
        """
        prompt = f"""Ты полезный HR ассистент. Ответь на следующий вопрос:

{question}

Дай профессиональный и подробный ответ."""

        return await self.generate_response(prompt, temperature=0.7)

