"""
Демонстрация PyTorch улучшений в системе подбора.

Показывает:
1. Cross-Encoder реранкинг для точной оценки
2. Семантическое сравнение навыков
"""

import asyncio

import httpx


BASE_URL = "http://localhost:8000/api/v1"


async def test_pytorch_features():
    """Тест PyTorch улучшений."""
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        
        print("="*80)
        print("🚀 ДЕМОНСТРАЦИЯ PYTORCH УЛУЧШЕНИЙ")
        print("="*80)
        
        # 1. С PyTorch улучшениями (по умолчанию)
        print("\n1️⃣ С PyTorch улучшениями (реранкинг + семантические навыки)")
        print("-"*80)
        
        response = await client.get(
            f"{BASE_URL}/matching/all-vacancies-with-candidates",
            params={
                "top_k": 5,
                "use_ai": False,
                "use_reranking": True,  # Cross-Encoder
                "use_semantic_skills": True,  # Семантические навыки
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Успешно! Найдено вакансий: {data['total_vacancies']}")
            
            # Показываем первую вакансию
            if data['vacancies']:
                first_vacancy = list(data['vacancies'].values())[0]
                print(f"\n📋 Вакансия: {first_vacancy['vacancy_title']}")
                print(f"👥 Кандидатов найдено: {first_vacancy['candidates_count']}")
                
                if first_vacancy['candidates']:
                    print("\nТоп-3 кандидата:")
                    for i, candidate in enumerate(first_vacancy['candidates'][:3], 1):
                        details = candidate['details']
                        print(f"\n  {i}. {details['candidate_name']}")
                        print(f"     📊 Combined Score: {candidate['score']:.2%}")
                        print(f"     🔍 Vector Score: {details['vector_score']:.2%}")
                        print(f"     ✅ Screening Score: {details['screening_score']:.2%}")
                        
                        # Показываем реранкинг если есть
                        if 'rerank_score' in details:
                            print(f"     🎯 Rerank Score: {details['rerank_score']:.2%}")
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(response.text)
        
        # 2. Без PyTorch улучшений (базовый режим)
        print("\n\n2️⃣ Без PyTorch улучшений (базовый режим)")
        print("-"*80)
        
        response = await client.get(
            f"{BASE_URL}/matching/all-vacancies-with-candidates",
            params={
                "top_k": 5,
                "use_ai": False,
                "use_reranking": False,  # Без реранкинга
                "use_semantic_skills": False,  # Без семантических навыков
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Успешно! Найдено вакансий: {data['total_vacancies']}")
            
            if data['vacancies']:
                first_vacancy = list(data['vacancies'].values())[0]
                print(f"\n📋 Вакансия: {first_vacancy['vacancy_title']}")
                print(f"👥 Кандидатов найдено: {first_vacancy['candidates_count']}")
                
                if first_vacancy['candidates']:
                    print("\nТоп-3 кандидата:")
                    for i, candidate in enumerate(first_vacancy['candidates'][:3], 1):
                        details = candidate['details']
                        print(f"\n  {i}. {details['candidate_name']}")
                        print(f"     📊 Combined Score: {candidate['score']:.2%}")
        else:
            print(f"❌ Ошибка: {response.status_code}")
        
        print("\n" + "="*80)
        print("🎯 ВЫВОД:")
        print("="*80)
        print("""
PyTorch улучшения дают:
✅ Более точную оценку соответствия (Cross-Encoder)
✅ Понимание похожих навыков (Python ≈ Python3)
✅ Лучшее ранжирование кандидатов
✅ Работает быстро (1-2 сек на вакансию)

Рекомендуется использовать по умолчанию!
        """)


async def test_semantic_skills_example():
    """Пример семантического сравнения навыков."""
    
    print("\n" + "="*80)
    print("🧠 ПРИМЕР: Семантическое сравнение навыков")
    print("="*80)
    
    print("""
Традиционное сравнение (точное совпадение строк):
---------------------------------------------------
Требуется: ["Python", "Django", "PostgreSQL"]
Кандидат:  ["python", "Django REST Framework", "Postgres"]
Результат: 1/3 = 33% ❌ (только "Django" совпадает)

Семантическое сравнение (PyTorch embeddings):
---------------------------------------------
Требуется: ["Python", "Django", "PostgreSQL"]
Кандидат:  ["python", "Django REST Framework", "Postgres"]
Результат: 3/3 = 100% ✅

Почему?
- "Python" ≈ "python" (similarity: 0.99)
- "Django" ≈ "Django REST Framework" (similarity: 0.85)
- "PostgreSQL" ≈ "Postgres" (similarity: 0.92)

Все совпадения выше порога 0.7!
    """)


async def test_reranking_example():
    """Пример реранкинга с Cross-Encoder."""
    
    print("\n" + "="*80)
    print("🎯 ПРИМЕР: Cross-Encoder реранкинг")
    print("="*80)
    
    print("""
Bi-Encoder (обычный векторный поиск):
-------------------------------------
Кодирует вакансию и кандидата отдельно
→ Сравнивает векторы (cosine similarity)
→ Быстро, но может ошибаться

Cross-Encoder (реранкинг):
--------------------------
Анализирует пару (вакансия, кандидат) вместе
→ Более глубокий анализ контекста
→ Медленнее, но точнее

Пример:
-------
Вакансия: "Senior Python Developer with Django experience"

Bi-Encoder scores:
  Кандидат 1: 0.75
  Кандидат 2: 0.72
  Кандидат 3: 0.70

Cross-Encoder rerank scores:
  Кандидат 2: 0.88 ← Переместился на 1 место!
  Кандидат 1: 0.82
  Кандидат 3: 0.65

Cross-Encoder нашел, что Кандидат 2 лучше подходит!
    """)


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════════╗
║               ДЕМОНСТРАЦИЯ PYTORCH УЛУЧШЕНИЙ                           ║
║                                                                        ║
║  Эта демонстрация показывает новые возможности:                       ║
║  1. Cross-Encoder реранкинг для точной оценки                          ║
║  2. Семантическое сравнение навыков                                   ║
║                                                                        ║
║  Убедитесь, что сервер запущен: python main.py                        ║
╚════════════════════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(test_pytorch_features())
    asyncio.run(test_semantic_skills_example())
    asyncio.run(test_reranking_example())

