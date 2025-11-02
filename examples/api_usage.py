"""Example of using the API with HTTP requests."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx

BASE_URL = "http://localhost:8000/api/v1"


async def main():
    """Run API usage example."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("=== HR AI Agent - API Usage Example ===\n")

        print("1. Creating vacancy...")
        vacancy_data = {
            "title": "Frontend Developer",
            "description": "Ищем талантливого Frontend разработчика",
            "requirements": [
                "Опыт с React 3+ года",
                "TypeScript",
                "State management (Redux, MobX)",
            ],
            "responsibilities": [
                "Разработка UI компонентов",
                "Интеграция с API",
                "Оптимизация производительности",
            ],
            "skills": ["React", "TypeScript", "Redux", "CSS", "HTML"],
            "experience_years": 3,
            "location": "Москва",
            "employment_type": "full-time",
        }

        response = await client.post(f"{BASE_URL}/vacancies/", json=vacancy_data)
        vacancy = response.json()
        vacancy_id = vacancy["id"]
        print(f"✓ Vacancy created: {vacancy['title']} (ID: {vacancy_id})\n")

        print("2. Creating candidates...")
        candidates_data = [
            {
                "name": "Петр Иванов",
                "email": "petr@example.com",
                "summary": "Опытный React разработчик",
                "skills": ["React", "TypeScript", "Redux", "Next.js"],
                "experience": ["4 года Frontend Developer", "Работа с крупными проектами"],
                "education": ["ВШЭ - Программная инженерия"],
                "experience_years": 4,
                "desired_position": "Senior Frontend Developer",
                "location": "Москва",
            },
            {
                "name": "Анна Козлова",
                "email": "anna@example.com",
                "summary": "Junior React разработчик",
                "skills": ["React", "JavaScript", "HTML", "CSS"],
                "experience": ["1 год Frontend Developer", "Участие в pet-проектах"],
                "education": ["Skillbox - Frontend курс"],
                "experience_years": 1,
                "desired_position": "Frontend Developer",
                "location": "Москва",
            },
        ]

        candidate_ids = []
        for candidate_data in candidates_data:
            response = await client.post(f"{BASE_URL}/candidates/", json=candidate_data)
            candidate = response.json()
            candidate_ids.append(candidate["id"])
            print(f"✓ Candidate created: {candidate['name']}")

        print()

        print("3. Finding matching candidates for vacancy...")
        response = await client.post(
            f"{BASE_URL}/matching/find-candidates/{vacancy_id}?top_k=2"
        )
        matches = response.json()

        for idx, match in enumerate(matches, 1):
            print(f"\n🏆 Match #{idx}")
            print(f"Score: {match['score']:.2%}")
            print(f"Candidate: {match['details']['candidate_name']}")
            print(f"Explanation: {match['explanation'][:150]}...")

        print("\n4. Asking AI a question...")
        question = "Что такое React hooks?"
        response = await client.post(f"{BASE_URL}/matching/ask?question={question}")
        result = response.json()

        print(f"Q: {question}")
        print(f"A: {result['answer'][:200]}...")

        print("\n✓ API usage example completed!")


if __name__ == "__main__":
    asyncio.run(main())

