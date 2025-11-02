"""
Простая демонстрация формата рангов.
Показывает ranking_summary в формате: job_title | rank | candidate_name
"""

import asyncio

import httpx


BASE_URL = "http://localhost:8000/api/v1"


async def show_ranking_format():
    """Показать простой формат рангов."""
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        print("🚀 Загрузка рангов...\n")
        
        response = await client.get(
            f"{BASE_URL}/matching/all-vacancies-with-candidates",
            params={
                "top_k": 5,
                "use_ai": False,
                "use_reranking": True,
                "use_semantic_skills": True,
            }
        )
        
        if response.status_code != 200:
            print(f"❌ Ошибка: {response.status_code}")
            return
        
        data = response.json()
        
        print("="*80)
        print("РАНГИ КАНДИДАТОВ ДЛЯ ВАКАНСИЙ")
        print("="*80)
        print(f"Всего вакансий: {data['total_vacancies']}")
        print(f"Всего совпадений: {data['total_matches']}")
        print()
        
        # Формат как в примере: job_title | rank | candidate_name
        print(f"{'ВАКАНСИЯ':<35} | {'RANK':<5} | {'КАНДИДАТ':<30} | {'SCORE':<6}")
        print("-"*80)
        
        for item in data['ranking_summary']:
            job_title = item['job_title'][:35]  # Обрезаем если длинное
            rank = item['rank']
            candidate = item['candidate_name'][:30]
            score = f"{item['score']:.1%}"
            
            print(f"{job_title:<35} | {rank:<5} | {candidate:<30} | {score:<6}")
        
        print("="*80)
        print(f"\n✅ Готово! Всего показано {len(data['ranking_summary'])} совпадений")
        
        # Показываем пример детализации для первой вакансии
        if data['vacancies']:
            print("\n\n" + "="*80)
            print("ПРИМЕР ДЕТАЛИЗАЦИИ (первая вакансия)")
            print("="*80)
            
            first_vacancy = list(data['vacancies'].values())[0]
            print(f"\n📋 Вакансия: {first_vacancy['vacancy_title']}")
            print(f"📍 Локация: {first_vacancy['vacancy_location']}")
            print(f"👥 Найдено кандидатов: {first_vacancy['candidates_count']}")
            
            if 'ranked_candidates' in first_vacancy:
                print("\nРанжированные кандидаты:")
                print(f"  {'Ранг':<6} | {'Кандидат':<30} | {'Score'}")
                print("  " + "-"*60)
                
                for ranked in first_vacancy['ranked_candidates']:
                    print(f"  {ranked['rank']:<6} | {ranked['candidate_name']:<30} | {ranked['score']:.2%}")


async def show_csv_format():
    """Показать в CSV формате."""
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        print("\n\n" + "="*80)
        print("ФОРМАТ CSV (для экспорта)")
        print("="*80)
        
        response = await client.get(
            f"{BASE_URL}/matching/all-vacancies-with-candidates",
            params={"top_k": 5}
        )
        
        if response.status_code != 200:
            return
        
        data = response.json()
        
        # CSV заголовок
        print("job_title,rank,candidate_name,score")
        
        # CSV данные
        for item in data['ranking_summary']:
            print(f'"{item["job_title"]}",{item["rank"]},"{item["candidate_name"]}",{item["score"]:.4f}')
        
        print("\n✅ Можно скопировать и использовать в Excel/Google Sheets")


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════════╗
║                    ДЕМОНСТРАЦИЯ ФОРМАТА РАНГОВ                         ║
║                                                                        ║
║  Формат: job_title | rank | candidate_name | score                    ║
║                                                                        ║
║  Где rank 1 = самый подходящий кандидат для вакансии                  ║
║                                                                        ║
║  Убедитесь, что сервер запущен: python main.py                        ║
╚════════════════════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(show_ranking_format())
    asyncio.run(show_csv_format())

