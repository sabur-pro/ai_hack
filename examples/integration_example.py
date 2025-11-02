"""
Пример интеграции GitHub оценки в существующую систему подбора кандидатов.
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Optional

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from examples.github_code_evaluator import GitHubCodeEvaluationService, CodeEvaluation
from src.core.domain.models import Candidate, Vacancy
from src.services.matching_service import MatchingService


class EnhancedMatchingService:
    """
    Расширенный сервис сопоставления с оценкой GitHub кода.
    """
    
    def __init__(self):
        self.matching_service = MatchingService()
        self.github_service = GitHubCodeEvaluationService()
    
    async def evaluate_candidate_comprehensive(
        self,
        candidate: Candidate,
        vacancy: Vacancy
    ) -> Dict:
        """
        Комплексная оценка кандидата с учетом GitHub кода.
        
        Args:
            candidate: Кандидат
            vacancy: Вакансия
        
        Returns:
            Словарь с результатами оценки
        """
        result = {
            'candidate_id': candidate.id,
            'vacancy_id': vacancy.id,
            'basic_match_score': 0.0,
            'github_code_score': None,
            'final_score': 0.0,
            'recommendation': '',
            'details': {}
        }
        
        try:
            basic_match = await self.matching_service.match_candidate_to_vacancy(
                candidate, vacancy
            )
            result['basic_match_score'] = basic_match.score
            result['details']['basic_match'] = {
                'score': basic_match.score,
                'explanation': getattr(basic_match, 'explanation', '')
            }
        except Exception as e:
            print(f"⚠️  Ошибка базовой оценки: {e}")
        
        resume_text = self._build_resume_text(candidate)
        github_evaluation = await self.github_service.evaluate_candidate_from_resume(
            resume_text,
            num_files=5
        )
        
        if github_evaluation:
            # Нормализуем оценку GitHub к диапазону 0-1
            github_normalized = github_evaluation.overall_score / 10
            result['github_code_score'] = github_evaluation.overall_score
            result['details']['github'] = {
                'overall_score': github_evaluation.overall_score,
                'architecture': github_evaluation.architecture_score,
                'code_quality': github_evaluation.code_quality_score,
                'best_practices': github_evaluation.best_practices_score,
                'documentation': github_evaluation.documentation_score,
                'complexity': github_evaluation.complexity_score,
                'strengths': github_evaluation.strengths[:3],
                'weaknesses': github_evaluation.weaknesses[:3],
                'recommendations': github_evaluation.recommendations[:3]
            }
            
            # 3. Финальная оценка (взвешенное среднее)
            # 60% - базовое соответствие, 40% - качество кода
            result['final_score'] = (
                result['basic_match_score'] * 0.6 +
                github_normalized * 0.4
            )
        else:
            result['final_score'] = result['basic_match_score']
            result['details']['github'] = None
        
        result['recommendation'] = self._get_recommendation(
            result['final_score'],
            result['github_code_score']
        )
        
        return result
    
    def _build_resume_text(self, candidate: Candidate) -> str:
        """Строит текст резюме из объекта кандидата."""
        text_parts = []
        
        if hasattr(candidate, 'name'):
            text_parts.append(f"Name: {candidate.name}")
        
        if hasattr(candidate, 'skills'):
            skills = ', '.join(candidate.skills) if isinstance(candidate.skills, list) else candidate.skills
            text_parts.append(f"Skills: {skills}")
        
        if hasattr(candidate, 'experience'):
            text_parts.append(f"Experience: {candidate.experience}")
        
        if hasattr(candidate, 'github_url'):
            text_parts.append(f"GitHub: {candidate.github_url}")
        
        if hasattr(candidate, 'description'):
            text_parts.append(candidate.description)
        
        return '\n'.join(text_parts)
    
    def _get_recommendation(
        self,
        final_score: float,
        github_score: Optional[float]
    ) -> str:
        """Генерирует рекомендацию на основе оценок."""
        if github_score:
            if final_score >= 0.85 and github_score >= 8.0:
                return "⭐ НАСТОЯТЕЛЬНО РЕКОМЕНДУЕТСЯ - Отличное соответствие + Превосходный код"
            elif final_score >= 0.75 and github_score >= 7.0:
                return "✅ РЕКОМЕНДУЕТСЯ - Хорошее соответствие + Качественный код"
            elif final_score >= 0.65:
                return "🤔 РАССМОТРЕТЬ - Среднее соответствие, требуется доп. интервью"
            else:
                return "❌ НЕ РЕКОМЕНДУЕТСЯ - Низкое соответствие"
        else:
            if final_score >= 0.80:
                return "✅ РЕКОМЕНДУЕТСЯ - Хорошее соответствие (GitHub не найден)"
            elif final_score >= 0.65:
                return "🤔 РАССМОТРЕТЬ - Среднее соответствие (требуется проверка кода)"
            else:
                return "❌ НЕ РЕКОМЕНДУЕТСЯ - Низкое соответствие"
    
    def print_comprehensive_report(self, result: Dict):
        """Выводит подробный отчет об оценке."""
        print("\n" + "="*80)
        print("КОМПЛЕКСНАЯ ОЦЕНКА КАНДИДАТА")
        print("="*80)
        
        # Основные оценки
        print(f"\n📊 ФИНАЛЬНАЯ ОЦЕНКА: {result['final_score']:.2%}")
        print(f"   • Базовое соответствие: {result['basic_match_score']:.2%}")
        
        if result['github_code_score']:
            print(f"   • Качество кода (GitHub): {result['github_code_score']:.1f}/10")
        else:
            print(f"   • Качество кода: Не оценено (GitHub не найден)")
        
        print(f"\n💡 РЕКОМЕНДАЦИЯ: {result['recommendation']}")
        
        # GitHub детали
        if result['details'].get('github'):
            github = result['details']['github']
            print(f"\n📈 ДЕТАЛЬНАЯ ОЦЕНКА КОДА:")
            print(f"   • Архитектура:      {github['architecture']:.1f}/10")
            print(f"   • Качество кода:    {github['code_quality']:.1f}/10")
            print(f"   • Best Practices:   {github['best_practices']:.1f}/10")
            print(f"   • Документация:     {github['documentation']:.1f}/10")
            print(f"   • Сложность:        {github['complexity']:.1f}/10")
            
            if github['strengths']:
                print(f"\n✅ СИЛЬНЫЕ СТОРОНЫ КОДА:")
                for strength in github['strengths']:
                    print(f"   • {strength}")
            
            if github['weaknesses']:
                print(f"\n⚠️  ОБЛАСТИ ДЛЯ УЛУЧШЕНИЯ:")
                for weakness in github['weaknesses']:
                    print(f"   • {weakness}")
        
        print("\n" + "="*80 + "\n")


async def demo_integration():
    """Демонстрация интеграции."""
    
    print("\n" + "="*80)
    print("ДЕМОНСТРАЦИЯ ИНТЕГРАЦИИ GITHUB ОЦЕНКИ")
    print("="*80 + "\n")
    
    # Создаем тестовую вакансию
    vacancy = Vacancy(
        id=1,
        title="Senior Python Developer",
        description="Ищем опытного Python разработчика",
        required_skills=["Python", "FastAPI", "Docker"],
        experience_years=5
    )
    
    print(f"📋 ВАКАНСИЯ: {vacancy.title}")
    print(f"   Требуемые навыки: {', '.join(vacancy.required_skills)}")
    print(f"   Опыт: {vacancy.experience_years}+ лет\n")
    
    # Создаем тестовых кандидатов
    candidates = [
        Candidate(
            id=1,
            name="Алексей Иванов",
            skills=["Python", "FastAPI", "Docker", "PostgreSQL"],
            experience=7,
            github_url="https://github.com/fastapi/fastapi",
            description="Senior Python разработчик с опытом создания высоконагруженных систем"
        ),
        Candidate(
            id=2,
            name="Мария Петрова",
            skills=["Python", "Flask", "React"],
            experience=4,
            github_url="https://github.com/pallets/flask",
            description="Full-stack разработчик, работающий с Python и JavaScript"
        ),
    ]
    
    # Оцениваем кандидатов
    service = EnhancedMatchingService()
    
    for candidate in candidates:
        print(f"\n{'='*80}")
        print(f"Оценка кандидата: {candidate.name}")
        print(f"{'='*80}")
        
        result = await service.evaluate_candidate_comprehensive(candidate, vacancy)
        service.print_comprehensive_report(result)
    
    print("\n✅ Демонстрация завершена!\n")


if __name__ == "__main__":
    asyncio.run(demo_integration())

