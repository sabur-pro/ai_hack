"""Demonstration of multi-stage screening and sequential agent execution."""

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
    """Run screening and sequential agents demo."""
    import sys
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("=" * 80)
    print("  MULTI-STAGE SCREENING + SEQUENTIAL AGENTS DEMO")
    print("=" * 80)
    print()
    print("Improvements:")
    print("  1. Multi-stage candidate screening")
    print("  2. Sequential agent execution (10 req/min limit)")
    print("  3. Only top candidates reach AI agents")
    print()
    print("=" * 80)
    print()

    gemini = GeminiClient()
    vector_db = ChromaRepository()
    rag_service = RAGService(gemini, vector_db)
    matching_service = MatchingService(rag_service)

    vacancy = Vacancy(
        title="Senior Python Developer",
        description="""Требуется опытный Python разработчик для работы с микросервисами.
        Обязательны знания Docker, Kubernetes, PostgreSQL.""",
        requirements=[
            "Python 5+ лет",
            "Docker и Kubernetes",
            "PostgreSQL",
            "Опыт с FastAPI или Django",
        ],
        responsibilities=["Разработка backend", "Code review", "DevOps"],
        skills=["Python", "FastAPI", "Docker", "Kubernetes", "PostgreSQL"],
        experience_years=5,
        location="Москва",
        salary_range="300-400k",
        employment_type="full-time",
    )

    print("VACANCY:")
    print(f"   {vacancy.title}")
    print(f"   Requirements: {', '.join(vacancy.requirements)}")
    print(f"   Skills: {', '.join(vacancy.skills)}")
    print()

    await matching_service.create_vacancy(vacancy)
    print("Vacancy created\n")

    candidates = [
        # Perfect match
        Candidate(
            name="Иван Петров",
            email="ivan@example.com",
            summary="Senior Python Developer с 6 годами опыта. FastAPI, Docker, Kubernetes, PostgreSQL.",
            skills=["Python", "FastAPI", "Docker", "Kubernetes", "PostgreSQL", "Redis"],
            experience=[
                "6 лет Senior Python Developer",
                "Работа с микросервисами на FastAPI",
                "Настройка Kubernetes и Docker",
            ],
            education=["МФТИ"],
            experience_years=6,
            location="Москва",
        ),
        Candidate(
            name="Мария Иванова",
            email="maria@example.com",
            summary="Python Developer с 3 годами опыта. Django, Docker, базовые знания PostgreSQL.",
            skills=["Python", "Django", "Docker", "PostgreSQL"],
            experience=["3 года Python Developer", "Разработка на Django"],
            education=["МГУ"],
            experience_years=3,
            location="Москва",
        ),
        Candidate(
            name="Сергей Смирнов",
            email="sergey@example.com",
            summary="Senior Python Developer с 7 годами опыта. FastAPI, Docker, Kubernetes.",
            skills=["Python", "FastAPI", "Docker", "Kubernetes", "PostgreSQL"],
            experience=["7 лет Python Developer"],
            education=["СПбГУ"],
            experience_years=7,
            location="Владивосток",  
        ),
        Candidate(
            name="Алексей Козлов",
            email="alex@example.com",
            summary="Senior JavaScript Developer. React, Node.js, MongoDB.",
            skills=["JavaScript", "React", "Node.js", "MongoDB"],
            experience=["5 лет JavaScript Developer"],
            education=["ВШЭ"],
            experience_years=5,
            location="Москва",
        ),
    ]

    print(f"Creating {len(candidates)} test candidates...\n")
    for candidate in candidates:
        await matching_service.create_candidate(candidate)
        print(f"   ✓ {candidate.name} ({candidate.experience_years} years, {candidate.location})")

    print()
    print("=" * 80)
    print("  MULTI-STAGE SCREENING SEARCH")
    print("=" * 80)
    print()

    print("Stages:")
    print("  Stage 1: Vector similarity search (Top 20)")
    print("  Stage 2: Hard skills matching")
    print("  Stage 3: Experience level check")
    print("  Stage 4: Location matching")
    print("  Stage 5: Keyword boost")
    print("  --> Only top candidates go to AI agents")
    print()

    print("Starting search...")
    print()
    
    matches = await matching_service.find_candidates_for_vacancy(
        vacancy_id=vacancy.id,
        top_k=2, 
    )

    print()
    print("=" * 80)
    print("  RESULTS")
    print("=" * 80)
    print()

    for idx, match in enumerate(matches, 1):
        print(f"{'=' * 80}")
        print(f"  CANDIDATE #{idx}")
        print(f"{'=' * 80}")
        print(f"Name: {match.details.get('candidate_name')}")
        print(f"Email: {match.details.get('candidate_email')}")
        print()

        print("SCORES:")
        print(f"   Overall: {match.score:.1%}")
        print()
        print(f"   Breakdown:")
        print(f"     * Vector Score:    {match.details.get('vector_score', 0):.1%}")
        print(f"     * Screening Score: {match.details.get('screening_score', 0):.1%}")
        print(f"     * Agent Score:     {match.details.get('agent_score', 0):.1%}")
        print()

        screening = match.details.get("screening_details", {})
        if screening:
            print("SCREENING DETAILS:")
            print(f"   Hard Skills:  {screening.get('hard_skills_score', 0):.1%}")
            print(f"   Experience:   {screening.get('experience_score', 0):.1%}")
            print(f"   Location:     {screening.get('location_score', 0):.1%}")
            print(f"   Keyword Boost: +{screening.get('keyword_boost', 0):.1%}")
            
            details = screening.get('details', {})
            if details:
                print(f"   Matched Skills: {details.get('skills_matched', 0)}/{details.get('required_skills', 0)}")
                print(f"   Experience Diff: {details.get('experience_diff', 0)} years")
            print()

        agent_results = match.details.get("agent_results", [])
        if agent_results:
            print(f"AGENT RESULTS ({len(agent_results)} agents):")
            print()

            for agent_result in agent_results[:3]:  
                print(f"  +- {agent_result.agent_name}")
                print(f"  |  Score: {agent_result.score:.0%}")
                print(f"  |  Confidence: {agent_result.confidence:.0%}")
                print(f"  |  Findings: {agent_result.findings[:100]}...")
                print(f"  +-")
                print()

        print(f"SUMMARY: {match.details.get('summary', '')[:200]}...")
        print()

    print("=" * 80)
    print("  DEMO COMPLETE")
    print("=" * 80)
    print()
    print("What was demonstrated:")
    print()
    print("1. Multi-stage screening:")
    print("   * Vector similarity for initial selection")
    print("   * Hard skills matching (required skills)")
    print("   * Experience level check")
    print("   * Location match")
    print("   * Keyword boost for important terms")
    print()
    print("2. Efficient filtering:")
    print("   * From N candidates, only top K go to agents")
    print("   * Saves API calls on unsuitable candidates")
    print()
    print("3. Sequential agent execution:")
    print("   * Agents run one after another")
    print("   * 6 seconds between agents")
    print("   * Stays under 10 req/min limit")
    print()
    print("4. Weighted final score:")
    print("   * Screening 30%")
    print("   * Vector 20%")
    print("   * Agents 50%")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()

