"""
Пример использования массового подбора кандидатов для всех вакансий.

Этот скрипт демонстрирует как использовать новый endpoint для быстрого
подбора кандидатов без использования AI агентов.
"""

import asyncio
import json
from typing import Dict, List

import httpx


BASE_URL = "http://localhost:8000/api/v1"


async def get_all_vacancies_with_candidates(
    top_k: int = 5, 
    use_ai: bool = False
) -> Dict:
    """
    Получить подходящих кандидатов для всех вакансий.
    
    Args:
        top_k: Количество кандидатов для каждой вакансии
        use_ai: Использовать AI агентов (медленно и дорого)
    
    Returns:
        Словарь с результатами для всех вакансий
    """
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.get(
            f"{BASE_URL}/matching/all-vacancies-with-candidates",
            params={
                "top_k": top_k,
                "use_ai": use_ai,
            }
        )
        response.raise_for_status()
        return response.json()


def print_results(data: Dict):
    """Красиво вывести результаты."""
    print(f"\n{'='*80}")
    print(f"МАССОВЫЙ ПОДБОР КАНДИДАТОВ")
    print(f"{'='*80}")
    print(f"\nВсего вакансий: {data['total_vacancies']}")
    print(f"Всего совпадений: {data.get('total_matches', 0)}")
    
    # Показываем простой список рангов
    if 'ranking_summary' in data:
        print(f"\n{'-'*80}")
        print(f"📊 РАНГИ (job_title | rank | candidate_name | score)")
        print(f"{'-'*80}")
        
        for item in data['ranking_summary'][:20]:  # Показываем первые 20
            print(f"{item['job_title']:<30} {item['rank']:>3}  {item['candidate_name']:<25} {item['score']:.2%}")
        
        if len(data['ranking_summary']) > 20:
            print(f"... и ещё {len(data['ranking_summary']) - 20} совпадений")
    
    # Детализация по вакансиям
    print(f"\n\n{'='*80}")
    print(f"📋 ДЕТАЛИЗАЦИЯ ПО ВАКАНСИЯМ")
    print(f"{'='*80}")
    
    for vacancy_id, vacancy_data in data['vacancies'].items():
        print(f"\n{'-'*80}")
        print(f"📋 Вакансия: {vacancy_data['vacancy_title']}")
        print(f"📍 Локация: {vacancy_data['vacancy_location']}")
        print(f"👥 Найдено кандидатов: {vacancy_data['candidates_count']}")
        
        if 'error' in vacancy_data:
            print(f"❌ Ошибка: {vacancy_data['error']}")
            continue
        
        if vacancy_data['candidates_count'] == 0:
            print("   Нет подходящих кандидатов")
            continue
        
        # Показываем ранжированных кандидатов
        if 'ranked_candidates' in vacancy_data:
            print("\n  Ранг | Кандидат                    | Score")
            print("  " + "-"*60)
            for ranked in vacancy_data['ranked_candidates']:
                print(f"  {ranked['rank']:>4} | {ranked['candidate_name']:<26} | {ranked['score']:.2%}")
        
        print("\nТоп-3 кандидата (детально):")
        for candidate in vacancy_data['candidates'][:3]:
            details = candidate['details']
            print(f"\n  ✓ {details['candidate_name']} ({details['candidate_email']})")
            print(f"    📊 Общая оценка: {candidate['score']:.2%}")
            print(f"    🔍 Векторная оценка: {details['vector_score']:.2%}")
            print(f"    ✅ Оценка скрининга: {details['screening_score']:.2%}")
            print(f"    💬 {candidate['explanation']}")
            
            # Детали скрининга
            screening = details['screening_details']
            print(f"    📝 Навыки: {screening['hard_skills_score']:.2%} | "
                  f"Опыт: {screening['experience_score']:.2%} | "
                  f"Локация: {screening['location_score']:.2%}")
            
            if details.get('skills'):
                skills_str = ', '.join(details['skills'][:5])
                if len(details['skills']) > 5:
                    skills_str += f" (и ещё {len(details['skills']) - 5})"
                print(f"    🛠️ Навыки: {skills_str}")


def save_results_to_file(data: Dict, filename: str = "bulk_matching_results.json"):
    """Сохранить результаты в файл."""
    # Преобразуем для JSON сериализации
    json_data = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(json_data)
    
    print(f"\n✅ Результаты сохранены в файл: {filename}")


async def main():
    """Основная функция."""
    print("🚀 Запуск массового подбора кандидатов...")
    print("⏱️ Это может занять некоторое время в зависимости от количества вакансий...")
    
    try:
        # Быстрый подбор без AI (рекомендуется)
        print("\n1️⃣ Выполняю быстрый подбор (без AI агентов)...")
        data = await get_all_vacancies_with_candidates(top_k=5, use_ai=False)
        
        # Выводим результаты
        print_results(data)
        
        # Сохраняем в файл
        save_results_to_file(data, "bulk_matching_results_no_ai.json")
        
        # Опционально: глубокий анализ с AI (медленно!)
        # Раскомментируйте, если нужен детальный AI анализ
        # print("\n\n2️⃣ Выполняю глубокий анализ с AI агентами (это займёт время)...")
        # data_with_ai = await get_all_vacancies_with_candidates(top_k=3, use_ai=True)
        # print_results(data_with_ai)
        # save_results_to_file(data_with_ai, "bulk_matching_results_with_ai.json")
        
    except httpx.HTTPStatusError as e:
        print(f"\n❌ Ошибка HTTP: {e.response.status_code}")
        print(f"   {e.response.text}")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════════╗
║                   МАССОВЫЙ ПОДБОР КАНДИДАТОВ                           ║
║                                                                        ║
║  Этот скрипт демонстрирует новый endpoint для массового подбора       ║
║  кандидатов для всех вакансий без использования AI агентов.           ║
║                                                                        ║
║  Преимущества:                                                         ║
║  ⚡ Быстро - секунды вместо минут                                      ║
║  💰 Дешево - не использует API Google Gemini                           ║
║  🎯 Точно - комбинация векторного поиска и скрининга                   ║
║                                                                        ║
║  Убедитесь, что сервер запущен: python main.py                        ║
╚════════════════════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(main())

