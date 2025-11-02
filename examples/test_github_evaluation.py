"""
Тестовый пример оценки кандидатов по GitHub с вакансией.

ИСПОЛЬЗОВАНИЕ:
Для избежания rate limit, установите GitHub токен:
$env:GITHUB_TOKEN="ghp_your_token"
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import List, Dict
import json

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from examples.github_code_evaluator import (
    GitHubCodeEvaluationService, 
    CodeEvaluation
)


class VacancyWithGitHubEvaluation:
    """Вакансия с оценкой кандидатов по GitHub."""
    
    def __init__(self, title: str, description: str, requirements: List[str]):
        self.title = title
        self.description = description
        self.requirements = requirements
        github_token = os.getenv('GITHUB_TOKEN')
        self.evaluation_service = GitHubCodeEvaluationService(github_token=github_token)
    
    async def evaluate_candidate(self, candidate: Dict) -> Dict:
        """
        Оценивает кандидата.
        
        Args:
            candidate: Словарь с данными кандидата (name, resume)
        
        Returns:
            Словарь с результатами оценки
        """
        print(f"\n{'='*80}")
        print(f"Оценка кандидата: {candidate['name']}")
        print(f"{'='*80}\n")
        
        evaluation = await self.evaluation_service.evaluate_candidate_from_resume(
            candidate['resume'],
            num_files=5
        )
        
        result = {
            'name': candidate['name'],
            'github_found': evaluation is not None,
            'evaluation': evaluation
        }
        
        if evaluation:
            self._print_evaluation(candidate['name'], evaluation)
        else:
            print(f"❌ GitHub репозиторий не найден или недоступен\n")
        
        return result
    
    def _print_evaluation(self, name: str, evaluation: CodeEvaluation):
        """Выводит результаты оценки."""
        print(f"📊 ОБЩАЯ ОЦЕНКА: {evaluation.overall_score:.1f}/10")
        print()
        print("📈 ДЕТАЛЬНЫЕ МЕТРИКИ:")
        print(f"  • Архитектура:      {evaluation.architecture_score:.1f}/10")
        print(f"  • Качество кода:    {evaluation.code_quality_score:.1f}/10")
        print(f"  • Best Practices:   {evaluation.best_practices_score:.1f}/10")
        print(f"  • Документация:     {evaluation.documentation_score:.1f}/10")
        print(f"  • Сложность:        {evaluation.complexity_score:.1f}/10")
        print()
        
        if evaluation.summary:
            print("📝 РЕЗЮМЕ:")
            print(f"  {evaluation.summary}")
            print()
        
        if evaluation.strengths:
            print("✅ СИЛЬНЫЕ СТОРОНЫ:")
            for strength in evaluation.strengths[:3]: 
                print(f"  • {strength}")
            print()
        
        if evaluation.weaknesses:
            print("⚠️ СЛАБЫЕ СТОРОНЫ:")
            for weakness in evaluation.weaknesses[:3]:  
                print(f"  • {weakness}")
            print()
    
    async def evaluate_all_candidates(self, candidates: List[Dict]) -> List[Dict]:
        """Оценивает всех кандидатов."""
        results = []
        
        for candidate in candidates:
            result = await self.evaluate_candidate(candidate)
            results.append(result)
        
        return results
    
    def print_ranking(self, results: List[Dict]):
        """Выводит рейтинг кандидатов."""
        print("\n" + "="*80)
        print("ИТОГОВЫЙ РЕЙТИНГ КАНДИДАТОВ")
        print("="*80)
        print()
        
        evaluated = [r for r in results if r['github_found']]
        
        if not evaluated:
            print("❌ Ни один кандидат не был оценен (GitHub не найден)")
            return
        
        evaluated.sort(key=lambda x: x['evaluation'].overall_score, reverse=True)
        
        print(f"{'Место':<8} {'Кандидат':<30} {'Общая оценка':<15} {'Рекомендация'}")
        print("-" * 80)
        
        for i, result in enumerate(evaluated, 1):
            name = result['name']
            score = result['evaluation'].overall_score
            
            if score >= 8.0:
                recommendation = "🌟 Отличный кандидат"
            elif score >= 6.5:
                recommendation = "✅ Хороший кандидат"
            elif score >= 5.0:
                recommendation = "⚠️ Требует внимания"
            else:
                recommendation = "❌ Не рекомендуется"
            
            print(f"{i:<8} {name:<30} {score:.1f}/10{'':<7} {recommendation}")
        
        print()
        
        best = evaluated[0]
        print(f"🏆 ЛУЧШИЙ КАНДИДАТ: {best['name']}")
        print(f"   Оценка: {best['evaluation'].overall_score:.1f}/10")
        
        if best['evaluation'].strengths:
            print(f"   Ключевые преимущества:")
            for strength in best['evaluation'].strengths[:2]:
                print(f"     • {strength}")
        
        print()
    
    def save_results(self, results: List[Dict], filename: str = "evaluation_results.json"):
        """Сохраняет результаты в JSON файл."""
        output = []
        
        for result in results:
            data = {
                'name': result['name'],
                'github_found': result['github_found']
            }
            
            if result['evaluation']:
                eval_data = result['evaluation']
                data['evaluation'] = {
                    'overall_score': eval_data.overall_score,
                    'architecture_score': eval_data.architecture_score,
                    'code_quality_score': eval_data.code_quality_score,
                    'best_practices_score': eval_data.best_practices_score,
                    'documentation_score': eval_data.documentation_score,
                    'complexity_score': eval_data.complexity_score,
                    'summary': eval_data.summary,
                    'strengths': eval_data.strengths,
                    'weaknesses': eval_data.weaknesses,
                    'recommendations': eval_data.recommendations
                }
            
            output.append(data)
        
        filepath = project_root / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Результаты сохранены в: {filepath}")


async def main():
    """Основной тестовый сценарий."""
    
    vacancy = VacancyWithGitHubEvaluation(
        title="Senior Python Backend Developer",
        description="Ищем опытного Python разработчика для работы над высоконагруженными backend сервисами",
        requirements=[
            "Опыт работы с Python 5+ лет",
            "Знание FastAPI/Django",
            "Опыт проектирования архитектуры",
            "Работа с Docker, K8s",
            "Чистый код и best practices",
            "Опыт работы с большими проектами"
        ]
    )
    
    print("="*80)
    print(f"ВАКАНСИЯ: {vacancy.title}")
    print("="*80)
    print(f"\n{vacancy.description}\n")
    print("ТРЕБОВАНИЯ:")
    for req in vacancy.requirements:
        print(f"  • {req}")
    print()
    
    candidates = [
        {
            'name': 'FastAPI Team (пример отличного проекта)',
            'resume': """
            Senior Python Developer
            
            Опыт:
            - 10+ лет в Python
            - Создание web фреймворков
            - Высоконагруженные системы
            - Open source проекты
            
            GitHub: https://github.com/fastapi/fastapi
            
            Навыки: Python, FastAPI, async, архитектура
            """
        },
        {
            'name': 'Flask Team (пример хорошего проекта)',
            'resume': """
            Python Developer
            
            Опыт:
            - 8 лет в Python
            - Web разработка
            - Микросервисы
            
            Мой проект: https://github.com/pallets/flask
            
            Навыки: Python, Flask, REST API
            """
        },
        {
            'name': 'Requests Library (популярная библиотека)',
            'resume': """
            Python Developer
            
            Опыт:
            - 7 лет в Python
            - HTTP клиенты
            - Библиотеки
            
            Portfolio: https://github.com/psf/requests
            
            Навыки: Python, HTTP, API
            """
        }
    ]
    
    print("\nНачинаем оценку кандидатов...\n")
    results = await vacancy.evaluate_all_candidates(candidates)
    
    vacancy.print_ranking(results)
    
    vacancy.save_results(results)
    
    print("\n" + "="*80)
    print("ОЦЕНКА ЗАВЕРШЕНА")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())

