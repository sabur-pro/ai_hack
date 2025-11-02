"""Простая демонстрация мультиагентной системы без превышения API limits."""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents import AgentCoordinator, DevOpsAgent, PythonExpertAgent
from src.core.domain.models import Candidate, Vacancy
from src.infrastructure.ai import GeminiClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Демо системы агентов."""
    print("=" * 80)
    print("ДЕМОНСТРАЦИЯ МУЛЬТИАГЕНТНОЙ СИСТЕМЫ")
    print("=" * 80)
    print()

    gemini = GeminiClient()
    coordinator = AgentCoordinator(gemini)

    vacancy = Vacancy(
        title="Senior Python Backend Developer",
        description="""Требуется опытный Python разработчик для работы с микросервисами.
        Необходим опыт с Docker, Kubernetes, PostgreSQL.""",
        requirements=[
            "Python 5+ лет",
            "Docker, Kubernetes",
            "PostgreSQL",
            "Микросервисная архитектура",
        ],
        responsibilities=["Разработка backend", "Code review", "DevOps задачи"],
        skills=["Python", "FastAPI", "Docker", "Kubernetes", "PostgreSQL"],
        experience_years=5,
        location="Remote",
        salary_range="300-400k",
        employment_type="full-time",
    )

    # Кандидат
    candidate = Candidate(
        name="Александр Петров",
        email="alex@example.com",
        summary="""Senior Python Developer с 6 годами опыта. Работал с FastAPI,
        Docker, Kubernetes. Настраивал CI/CD, работал с PostgreSQL. Имею опыт
        менторства и code review.""",
        skills=["Python", "FastAPI", "Docker", "Kubernetes", "PostgreSQL", "AWS"],
        experience=[
            "6 лет Senior Python Developer",
            "Разработка микросервисов на FastAPI",
            "Настройка CI/CD и Kubernetes",
            "Менторство junior разработчиков",
        ],
        education=["МФТИ - Прикладная математика"],
        experience_years=6,
        desired_position="Senior Python Developer",
        location="Москва",
    )

    print("📋 ВАКАНСИЯ:")
    print(f"   {vacancy.title}")
    print(f"   Требования: {', '.join(vacancy.requirements)}")
    print()
    print("👤 КАНДИДАТ:")
    print(f"   {candidate.name}")
    print(f"   Опыт: {candidate.experience_years} лет")
    print(f"   Навыки: {', '.join(candidate.skills)}")
    print()
    print("=" * 80)
    print()

    print("🔍 Шаг 1: AI выбирает подходящих агентов для вакансии...")
    print()

    selected_agents = await coordinator.select_agents_for_vacancy(vacancy)

    print(f"✓ Выбрано {len(selected_agents)} агентов:")
    for agent in selected_agents:
        print(f"  • {agent.get_name()}: {agent.get_description()}")
    print()
    print("=" * 80)
    print()

    print(" Шаг 2: Запуск 2 агентов для демонстрации (Python и DevOps)...")
    print("   (Полная система запускает всех агентов параллельно)")
    print()

    demo_agents = [PythonExpertAgent(gemini), DevOpsAgent(gemini)]

    for agent in demo_agents:
        print(f"▶ Запуск: {agent.get_name()}")
        print(f"  Специализация: {agent.get_description()}")
        print()

        try:
            result = await agent.analyze(candidate, vacancy)

            print(f"  📊 Результат анализа:")
            print(f"     Score: {result.score:.0%}")
            print(f"     Confidence: {result.confidence:.0%}")
            print()
            print(f"  💡 Выводы:")
            print(f"     {result.findings}")
            print()

            if result.strengths:
                print(f"  ✅ Сильные стороны:")
                for strength in result.strengths:
                    print(f"     • {strength}")
                print()

            if result.weaknesses:
                print(f"  ⚠️  Слабости:")
                for weakness in result.weaknesses:
                    print(f"     • {weakness}")
                print()

            if result.recommendations:
                print(f"  💭 Рекомендации:")
                for rec in result.recommendations:
                    print(f"     • {rec}")
                print()

            print("-" * 80)
            print()

            await asyncio.sleep(6)

        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            print()
            if "429" in str(e):
                print("  ℹ️  Достигнут лимит API (10 запросов/мин)")
                print("     Подождите минуту или используйте API key с большим лимитом")
            print()

    print("=" * 80)
    print("  ✅ ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
    print("=" * 80)
    print()
    print("📚 Что было показано:")
    print("   1. AI автоматически выбирает нужных агентов для вакансии")
    print("   2. Каждый агент - эксперт в своей области")
    print("   3. Детальный анализ с оценкой, выводами и рекомендациями")
    print()
    print("💡 В реальной системе:")
    print("   • Все агенты работают параллельно (быстро)")
    print("   • Результаты объединяются в итоговую оценку")
    print("   • Можно добавлять контекст (GitHub, тесты и т.д.)")
    print()
    print("📖 Документация: MULTI_AGENT_SYSTEM.md")
    print("🚀 Полный пример: examples/multi_agent_example.py")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
    except Exception as e:
        print(f"\n\n❌ Ошибка: {e}")
        if "429" in str(e):
            print("\nℹ️  Достигнут лимит Gemini API (10 запросов/минуту на free tier)")
            print("   Решения:")
            print("   1. Подождите 1 минуту и попробуйте снова")
            print("   2. Используйте API key с большим лимитом")
            print("   3. Добавьте rate limiting в код")

