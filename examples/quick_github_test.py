"""
Быстрый тест оценки GitHub репозитория.

ИСПОЛЬЗОВАНИЕ:
Для избежания rate limit, установите GitHub токен:
$env:GITHUB_TOKEN="ghp_your_token"
"""

import asyncio
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from examples.github_code_evaluator import GitHubCodeEvaluationService


async def quick_evaluate(github_url: str, num_files: int = 5):
    """
    Быстрая оценка GitHub репозитория.
    
    Args:
        github_url: URL GitHub репозитория
        num_files: Количество файлов для анализа
    """
    resume = f"""
    GitHub: {github_url}
    """
    
    print(f"\n🔍 Анализ репозитория: {github_url}")
    print(f"📁 Количество файлов для анализа: {num_files}")
    print("⏳ Подождите, идет анализ...\n")
    print("="*80)
    
    github_token = os.getenv('GITHUB_TOKEN')
    if github_token:
        print(f"\n✅ Используется GitHub токен: {github_token[:10]}...\n")
    else:
        print(f"\n⚠️  GitHub токен не найден. Лимит: 60 запросов/час")
        print(f"   Установите: $env:GITHUB_TOKEN='ваш_токен'\n")
    
    service = GitHubCodeEvaluationService(github_token=github_token)
    evaluation = await service.evaluate_candidate_from_resume(resume, num_files)
    
    if evaluation:
        print("\n" + "="*80)
        print("✅ РЕЗУЛЬТАТЫ АНАЛИЗА")
        print("="*80 + "\n")
        
        overall = evaluation.overall_score
        stars = "⭐" * int(overall)
        print(f"🎯 ИТОГОВАЯ ОЦЕНКА: {overall:.1f}/10 {stars}")
        print()
        
        print("📊 ДЕТАЛЬНЫЕ МЕТРИКИ:\n")
        
        metrics = [
            ("Архитектура", evaluation.architecture_score),
            ("Качество кода", evaluation.code_quality_score),
            ("Best Practices", evaluation.best_practices_score),
            ("Документация", evaluation.documentation_score),
            ("Сложность", evaluation.complexity_score),
        ]
        
        for name, score in metrics:
            bar_length = 20
            filled = int((score / 10) * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)
            print(f"  {name:<20} [{bar}] {score:.1f}/10")
        
        print()
        
        if evaluation.summary:
            print("📝 РЕЗЮМЕ:")
            print(f"   {evaluation.summary}\n")
        
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
        
        if evaluation.recommendations:
            print("💡 РЕКОМЕНДАЦИИ:")
            for i, rec in enumerate(evaluation.recommendations[:3], 1):
                print(f"   {i}. {rec}")
            print()
        
        print("="*80)
        if overall >= 8.0:
            print("🌟 ВЕРДИКТ: Отличный код! Кандидат демонстрирует высокий уровень.")
        elif overall >= 6.5:
            print("✅ ВЕРДИКТ: Хороший код. Кандидат компетентен.")
        elif overall >= 5.0:
            print("⚠️  ВЕРДИКТ: Средний уровень. Требует дополнительной проверки.")
        else:
            print("❌ ВЕРДИКТ: Код требует значительного улучшения.")
        print("="*80 + "\n")
        
    else:
        print("\n❌ Не удалось проанализировать репозиторий.")
        print("   Убедитесь, что:")
        print("   - URL правильный")
        print("   - Репозиторий публичный")
        print("   - В репозитории есть код\n")


async def main():
    """Основная функция."""
    
    print("\n" + "="*80)
    print("БЫСТРАЯ ОЦЕНКА GITHUB РЕПОЗИТОРИЯ")
    print("="*80)
    
    test_repos = [
        "https://github.com/fastapi/fastapi",      
        "https://github.com/pallets/flask",         
        "https://github.com/psf/requests",     
    ]
    
    print("\n📋 ДОСТУПНЫЕ ТЕСТОВЫЕ РЕПОЗИТОРИИ:")
    for i, repo in enumerate(test_repos, 1):
        print(f"   {i}. {repo}")
    
    print("\n💡 Или укажите свой GitHub репозиторий ниже")
    print("="*80 + "\n")
    

    selected_repo = test_repos[0]
    
    print(f"Выбран репозиторий: {selected_repo}\n")
    
    await quick_evaluate(selected_repo, num_files=5)


if __name__ == "__main__":
    asyncio.run(main())

