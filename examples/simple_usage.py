"""Simple usage example for HR AI Agent."""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.domain.models import Candidate, Vacancy
from src.infrastructure.ai import GeminiClient
from src.infrastructure.vector_db import ChromaRepository
from src.services import MatchingService, RAGService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Run example."""
    logger.info("=== HR AI Agent - Simple Usage Example ===\n")

    gemini = GeminiClient()
    vector_db = ChromaRepository()
    rag_service = RAGService(gemini, vector_db)
    matching_service = MatchingService(rag_service)

    vacancy = Vacancy(
        title="Senior Python Developer",
        description="Мы ищем опытного Python разработчика для работы над AI проектами",
        requirements=[
            "Опыт работы с Python 5+ лет",
            "Знание FastAPI, Django",
            "Опыт работы с ML/AI библиотеками",
        ],
        responsibilities=[
            "Разработка backend сервисов",
            "Интеграция ML моделей",
            "Code review и менторство",
        ],
        skills=["Python", "FastAPI", "Machine Learning", "Docker", "PostgreSQL"],
        experience_years=5,
        location="Москва (удаленно)",
        salary_range="250-350k RUB",
    )

    logger.info(f"Creating vacancy: {vacancy.title}")
    await matching_service.create_vacancy(vacancy)
    logger.info(f"✓ Vacancy created with ID: {vacancy.id}\n")

    candidates = [
        Candidate(
            name="Иван Петров",
            email="ivan@example.com",
            summary="Senior Python разработчик с опытом работы в AI стартапах",
            skills=["Python", "FastAPI", "TensorFlow", "Docker", "AWS"],
            experience=[
                "5 лет Senior Python Developer в AI компании",
                "Разработка ML pipeline и REST API",
                "Работа с большими данными",
            ],
            education=["МГУ - Прикладная математика"],
            experience_years=5,
            desired_position="Senior Python Developer",
            location="Москва",
        ),
        Candidate(
            name="Мария Сидорова",
            email="maria@example.com",
            summary="Full-stack разработчик с базовыми знаниями Python",
            skills=["JavaScript", "React", "Python", "Node.js", "MongoDB"],
            experience=[
                "3 года Full-stack Developer",
                "Разработка веб-приложений",
                "Базовые знания Python и Flask",
            ],
            education=["МФТИ - Информатика"],
            experience_years=3,
            desired_position="Full-stack Developer",
            location="Москва",
        ),
        Candidate(
            name="Алексей Смирнов",
            email="alex@example.com",
            summary="Python разработчик с экспертизой в Machine Learning",
            skills=["Python", "PyTorch", "Scikit-learn", "FastAPI", "Kubernetes"],
            experience=[
                "6 лет ML Engineer и Python Developer",
                "Разработка и деплой ML моделей",
                "Оптимизация производительности",
            ],
            education=["СПбГУ - Компьютерные науки", "Coursera ML Specialization"],
            experience_years=6,
            desired_position="ML Engineer / Senior Python Developer",
            location="Санкт-Петербург (готов к удаленке)",
        ),
    ]

    logger.info("Creating candidates...")
    for candidate in candidates:
        await matching_service.create_candidate(candidate)
        logger.info(f"✓ Candidate '{candidate.name}' created")

    logger.info(f"\nTotal candidates: {len(candidates)}\n")

    logger.info("=" * 60)
    logger.info("Finding best candidates for vacancy...")
    logger.info("=" * 60)

    matches = await matching_service.find_candidates_for_vacancy(
        vacancy_id=vacancy.id,
        top_k=3,
    )

    for idx, match in enumerate(matches, 1):
        logger.info(f"\n🏆 Match #{idx}")
        logger.info(f"Score: {match.score:.2%}")
        logger.info(f"Candidate: {match.details.get('candidate_name')}")
        logger.info(f"Email: {match.details.get('candidate_email')}")
        logger.info(f"Vector Score: {match.details.get('vector_score', 0):.2f}")
        logger.info(f"AI Score: {match.details.get('ai_score', 0):.2f}")
        logger.info(f"\nExplanation:\n{match.explanation}")

        if match.details.get("strengths"):
            logger.info(f"\n✅ Strengths: {match.details['strengths']}")
        if match.details.get("weaknesses"):
            logger.info(f"⚠️ Weaknesses: {match.details['weaknesses']}")

    logger.info("\n" + "=" * 60)
    logger.info("Testing AI Q&A functionality...")
    logger.info("=" * 60)

    question = "Какие навыки важны для Python разработчика в 2024 году?"
    logger.info(f"\nQuestion: {question}")

    answer = await gemini.answer_question(question)
    logger.info(f"\nAnswer:\n{answer}")

    logger.info("\n" + "=" * 60)
    logger.info("Example completed successfully!")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

