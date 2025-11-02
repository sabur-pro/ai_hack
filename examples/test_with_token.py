"""
Тест оценки GitHub с поддержкой токена из переменной окружения.

ИСПОЛЬЗОВАНИЕ:
1. Создайте GitHub token: https://github.com/settings/tokens
2. Установите переменную окружения:
   
   Windows PowerShell:
   $env:GITHUB_TOKEN="ghp_your_token_here"
   
   Linux/Mac:
   export GITHUB_TOKEN="ghp_your_token_here"

3. Запустите скрипт:
   python examples/test_with_token.py
"""

import asyncio
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from examples.github_code_evaluator import GitHubCodeEvaluationService


async def check_rate_limit(github_token=None):
    """Проверяет текущие лимиты GitHub API."""
    import requests
    
    url = "https://api.github.com/rate_limit"
    headers = {}
    if github_token:
        headers['Authorization'] = f'token {github_token}'
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            rate = data.get('rate', {})
            
            print("\n" + "="*80)
            print("📊 СТАТУС ЛИМИТОВ GITHUB API")
            print("="*80)
            print(f"Максимум запросов в час: {rate.get('limit', 'N/A')}")
            print(f"Осталось запросов:       {rate.get('remaining', 'N/A')}")
            
            if 'reset' in rate:
                from datetime import datetime
                reset_dt = datetime.fromtimestamp(rate['reset'])
                print(f"Лимит сбросится:         {reset_dt.strftime('%Y-%m-%d %H:%M:%S')}")
            
            print("="*80 + "\n")
            
            return rate.get('remaining', 0) > 0
        else:
            print(f"⚠️  Не удалось проверить лимиты: {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️  Ошибка проверки лимитов: {e}")
        return False


async def test_evaluation_with_token():
    """Тестирует оценку с токеном."""
    
    print("\n" + "="*80)
    print("ТЕСТ ОЦЕНКИ GITHUB С ТОКЕНОМ")
    print("="*80 + "\n")
    
    github_token = os.getenv('GITHUB_TOKEN')
    
    if github_token:
        print("✅ GitHub токен найден!")
        print(f"   Токен начинается с: {github_token[:10]}...")
        print()
        
        has_requests = await check_rate_limit(github_token)
        
        if not has_requests:
            print("⚠️  Достигнут лимит запросов. Подождите до сброса.")
            return
    else:
        print("⚠️  GitHub токен НЕ найден!")
        print()
        print("Без токена лимит: 60 запросов/час")
        print("С токеном лимит:  5000 запросов/час")
        print()
        print("КАК ПОЛУЧИТЬ ТОКЕН:")
        print("1. Перейдите: https://github.com/settings/tokens")
        print("2. 'Generate new token (classic)'")
        print("3. Выберите scope: 'public_repo'")
        print("4. Установите переменную:")
        print("   $env:GITHUB_TOKEN='ваш_токен'")
        print()
        
        await check_rate_limit(None)
        
        response = input("Продолжить без токена? (y/n): ")
        if response.lower() != 'y':
            print("\n❌ Прервано пользователем")
            return
    
 
    service = GitHubCodeEvaluationService(github_token=github_token)
    
    resume = """
    Senior Python Developer
    
    Опыт: 5+ лет разработки на Python
    Навыки: FastAPI, Django, Docker, PostgreSQL
    
    Мой проект: https://github.com/fastapi/fastapi
    """
    
    print("\n" + "="*80)
    print("НАЧИНАЕМ ОЦЕНКУ КОДА")
    print("="*80 + "\n")
    
    try:
        evaluation = await service.evaluate_candidate_from_resume(
            resume, 
            num_files=5
        )
        
        if evaluation:
            print("\n" + "="*80)
            print("✅ ОЦЕНКА УСПЕШНА!")
            print("="*80 + "\n")
            
            print(f"🎯 ИТОГОВАЯ ОЦЕНКА: {evaluation.overall_score:.1f}/10")
            print()
            print("📊 ДЕТАЛЬНЫЕ МЕТРИКИ:")
            print(f"  • Архитектура:      {evaluation.architecture_score:.1f}/10")
            print(f"  • Качество кода:    {evaluation.code_quality_score:.1f}/10")
            print(f"  • Best Practices:   {evaluation.best_practices_score:.1f}/10")
            print(f"  • Документация:     {evaluation.documentation_score:.1f}/10")
            print(f"  • Сложность:        {evaluation.complexity_score:.1f}/10")
            print()
            
            if evaluation.strengths:
                print("✅ ТОП-3 СИЛЬНЫЕ СТОРОНЫ:")
                for i, strength in enumerate(evaluation.strengths[:3], 1):
                    print(f"   {i}. {strength}")
                print()
            
            if evaluation.weaknesses:
                print("⚠️  ТОП-3 ОБЛАСТИ ДЛЯ УЛУЧШЕНИЯ:")
                for i, weakness in enumerate(evaluation.weaknesses[:3], 1):
                    print(f"   {i}. {weakness}")
                print()
            
            print("="*80)
            print("✅ ТЕСТ ЗАВЕРШЕН УСПЕШНО!")
            print("="*80 + "\n")
            
        else:
            print("\n❌ Не удалось оценить код")
            print("   Проверьте логи выше для деталей\n")
    
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}\n")


async def main():
    """Основная функция."""
    await test_evaluation_with_token()


if __name__ == "__main__":
    asyncio.run(main())

