"""Multi-agent system example for HR AI Agent with large candidate pool."""

import asyncio
import logging
import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.domain.models import Candidate, Vacancy
from src.infrastructure.ai import GeminiClient
from src.infrastructure.vector_db import ChromaRepository
from src.services import MatchingService, RAGService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_candidates() -> List[Candidate]:
    """Generate 80 diverse candidates with varying skills and experience."""
    
    # Templates for names (first names and last names)
    first_names = [
        "Александр", "Дмитрий", "Максим", "Иван", "Андрей", "Михаил", "Сергей", "Артем",
        "Алексей", "Николай", "Павел", "Егор", "Владимир", "Роман", "Кирилл", "Денис",
        "Мария", "Анна", "Елена", "Ольга", "Татьяна", "Наталья", "Светлана", "Ирина",
        "Екатерина", "Юлия", "Анастасия", "Дарья", "Виктория", "Полина", "София", "Валерия"
    ]
    
    last_names = [
        "Иванов", "Петров", "Сидоров", "Смирнов", "Кузнецов", "Попов", "Васильев", "Соколов",
        "Михайлов", "Новиков", "Федоров", "Морозов", "Волков", "Алексеев", "Лебедев", "Семенов",
        "Егоров", "Павлов", "Козлов", "Степанов", "Николаев", "Орлов", "Андреев", "Макаров"
    ]
    

    translit_map = {
        "Александр": "alexander", "Дмитрий": "dmitry", "Максим": "maxim", "Иван": "ivan",
        "Андрей": "andrey", "Михаил": "mikhail", "Сергей": "sergey", "Артем": "artem",
        "Алексей": "alexey", "Николай": "nikolay", "Павел": "pavel", "Егор": "egor",
        "Владимир": "vladimir", "Роман": "roman", "Кирилл": "kirill", "Денис": "denis",
        "Мария": "maria", "Анна": "anna", "Елена": "elena", "Ольга": "olga",
        "Татьяна": "tatyana", "Наталья": "natalia", "Светлана": "svetlana", "Ирина": "irina",
        "Екатерина": "ekaterina", "Юлия": "julia", "Анастасия": "anastasia", "Дарья": "darya",
        "Виктория": "victoria", "Полина": "polina", "София": "sofia", "Валерия": "valeria",
        "Иванов": "ivanov", "Петров": "petrov", "Сидоров": "sidorov", "Смирнов": "smirnov",
        "Кузнецов": "kuznetsov", "Попов": "popov", "Васильев": "vasiliev", "Соколов": "sokolov",
        "Михайлов": "mikhailov", "Новиков": "novikov", "Федоров": "fedorov", "Морозов": "morozov",
        "Волков": "volkov", "Алексеев": "alekseev", "Лебедев": "lebedev", "Семенов": "semenov",
        "Егоров": "egorov", "Павлов": "pavlov", "Козлов": "kozlov", "Степанов": "stepanov",
        "Николаев": "nikolaev", "Орлов": "orlov", "Андреев": "andreev", "Макаров": "makarov"
    }
    
    # Skill sets для разных специализаций
    python_backend = ["Python", "FastAPI", "Django", "Flask", "PostgreSQL", "Redis"]
    devops_skills = ["Docker", "Kubernetes", "AWS", "CI/CD", "Terraform", "Jenkins"]
    database_skills = ["PostgreSQL", "MongoDB", "MySQL", "Redis", "Elasticsearch"]
    frontend_skills = ["JavaScript", "React", "Vue.js", "TypeScript", "HTML", "CSS"]
    testing_skills = ["pytest", "Selenium", "unittest", "Integration Testing"]
    
    candidates = []
    
    for i in range(80):
        first = first_names[i % len(first_names)]
        last = last_names[i % len(last_names)]
        name = f"{first} {last}"
        
        # Транслитерация для email
        first_translit = translit_map[first]
        last_translit = translit_map[last]
        email = f"{first_translit}.{last_translit}{i}@example.com"
        
        exp_years = (i % 10) + 1
        
        if exp_years <= 2:
            level = "Junior"
        elif exp_years <= 5:
            level = "Middle"
        else:
            level = "Senior"
        
        specialization_idx = i % 5
        
        if specialization_idx == 0:
            skills = python_backend.copy()
            if exp_years > 3:
                skills.extend(devops_skills[:3])
            if exp_years > 5:
                skills.extend(database_skills[:2])
            
            summary = f"""{level} Python Backend Developer с {exp_years} годами опыта. 
            Работал с микросервисной архитектурой, разрабатывал REST API."""
            
            if exp_years > 5:
                summary += " Имею опыт менторства и code review."
            
            experience = [
                f"{exp_years} лет опыта разработки на Python",
                "Разработка backend микросервисов",
                "Работа с базами данных"
            ]
            
            if exp_years > 4:
                experience.append("Опыт проектирования архитектуры")
            
            desired_position = f"{level} Python Developer"
            
        elif specialization_idx == 1:
            skills = devops_skills.copy()
            if exp_years > 3:
                skills.extend(python_backend[:2])
            
            summary = f"""{level} DevOps Engineer с {exp_years} годами опыта. 
            Специализируюсь на CI/CD, контейнеризации и облачных платформах."""
            
            experience = [
                f"{exp_years} лет опыта в DevOps",
                "Настройка CI/CD пайплайнов",
                "Работа с Docker и Kubernetes"
            ]
            
            if exp_years > 5:
                experience.append("Построение инфраструктуры с нуля")
            
            desired_position = f"{level} DevOps Engineer"
            
        elif specialization_idx == 2:
            skills = database_skills.copy()
            if exp_years > 3:
                skills.extend(python_backend[:3])
            
            summary = f"""{level} Database Engineer с {exp_years} годами опыта. 
            Специализируюсь на оптимизации запросов, репликации и масштабировании БД."""
            
            experience = [
                f"{exp_years} лет работы с базами данных",
                "Оптимизация SQL запросов",
                "Настройка репликации и шардирования"
            ]
            
            desired_position = f"{level} Database Engineer"
            
        elif specialization_idx == 3:
            skills = frontend_skills.copy()
            
            summary = f"""{level} Frontend Developer с {exp_years} годами опыта. 
            Разрабатываю современные SPA приложения на React."""
            
            experience = [
                f"{exp_years} лет frontend разработки",
                "Разработка SPA приложений",
                "Работа с современными фреймворками"
            ]
            
            desired_position = f"{level} Frontend Developer"
            
        else:
            skills = python_backend[:4] + frontend_skills[:3]
            if exp_years > 5:
                skills.extend(devops_skills[:2])
            
            summary = f"""{level} Fullstack Developer с {exp_years} годами опыта. 
            Работаю как с backend (Python), так и с frontend (React)."""
            
            experience = [
                f"{exp_years} лет fullstack разработки",
                "Backend разработка на Python",
                "Frontend разработка на React"
            ]
            
            desired_position = f"{level} Fullstack Developer"
        
        universities = ["МГУ", "МФТИ", "ИТМО", "СПбГУ", "ВШЭ", "Бауманка"]
        education = [f"{universities[i % len(universities)]} - Информатика и вычислительная техника"]
        
        locations = ["Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань"]
        location = locations[i % len(locations)]
        if exp_years > 6:
            location += " (готов к релокации)"
        
        candidate = Candidate(
            name=name,
            email=email,
            summary=summary,
            skills=skills,
            experience=experience,
            education=education,
            experience_years=exp_years,
            desired_position=desired_position,
            location=location,
        )
        
        candidates.append(candidate)
    
    return candidates


def create_vacancies() -> List[Vacancy]:
    """Create 2 different vacancies."""
    
    vacancy1 = Vacancy(
        title="Senior Python Backend Developer",
        description="""Мы ищем опытного Senior Python разработчика для работы над high-load 
        backend системами. Работа с микросервисной архитектурой, облачными платформами и 
        современными DevOps практиками. Важны как технические, так и soft skills.""",
        requirements=[
            "Опыт с Python 5+ лет",
            "Знание FastAPI, Django или Flask",
            "Опыт с Docker и Kubernetes",
            "Знание PostgreSQL и оптимизация запросов",
            "Понимание CI/CD процессов",
            "Опыт code review и менторства",
        ],
        responsibilities=[
            "Разработка backend микросервисов",
            "Проектирование архитектуры",
            "Code review и менторство junior разработчиков",
            "Оптимизация производительности",
            "Взаимодействие с командой и стейкхолдерами",
        ],
        skills=[
            "Python",
            "FastAPI",
            "Django",
            "Docker",
            "Kubernetes",
            "PostgreSQL",
            "Redis",
            "AWS",
            "CI/CD",
            "Git",
        ],
        experience_years=5,
        location="Москва (гибрид)",
        salary_range="300-450k RUB",
        employment_type="full-time",
    )
    
    vacancy2 = Vacancy(
        title="Lead Database Engineer",
        description="""Требуется Lead Database Engineer для управления и оптимизации 
        высоконагруженных баз данных. Работа с PostgreSQL, MongoDB, проектирование 
        схем данных, настройка репликации и шардирования. Необходим опыт руководства 
        командой и работы с большими объемами данных.""",
        requirements=[
            "Опыт работы с БД 6+ лет",
            "Глубокие знания PostgreSQL",
            "Опыт с MongoDB или другими NoSQL",
            "Знание принципов репликации и шардирования",
            "Опыт оптимизации запросов и индексов",
            "Опыт работы с высоконагруженными системами",
            "Навыки мониторинга и диагностики",
        ],
        responsibilities=[
            "Проектирование архитектуры БД",
            "Оптимизация производительности",
            "Настройка репликации и failover",
            "Мониторинг и диагностика проблем",
            "Менторство команды DBA",
            "Участие в code review SQL кода",
        ],
        skills=[
            "PostgreSQL",
            "MongoDB",
            "Redis",
            "SQL",
            "Репликация",
            "Шардирование",
            "Индексация",
            "Query optimization",
            "Мониторинг",
        ],
        experience_years=6,
        location="Москва",
        salary_range="350-500k RUB",
        employment_type="full-time",
    )
    
    return [vacancy1, vacancy2]


async def main():
    """Run multi-agent example with large dataset."""
    logger.info("=" * 80)
    logger.info("  🤖 HR AI Agent - Multi-Agent System Demo (Large Scale)")
    logger.info("=" * 80)
    logger.info("")

    gemini = GeminiClient()
    vector_db = ChromaRepository()
    rag_service = RAGService(gemini, vector_db)
    matching_service = MatchingService(rag_service)

    vacancies = create_vacancies()
    logger.info(f"📋 Создание вакансий: {len(vacancies)}")
    for vacancy in vacancies:
        await matching_service.create_vacancy(vacancy)
        logger.info(f"   ✓ {vacancy.title}")
    logger.info("")

    candidates = generate_candidates()
    logger.info(f"👥 Создание кандидатов: {len(candidates)}")
    
    junior_count = sum(1 for c in candidates if "Junior" in c.desired_position)
    middle_count = sum(1 for c in candidates if "Middle" in c.desired_position)
    senior_count = sum(1 for c in candidates if "Senior" in c.desired_position)
    
    logger.info(f"   - Junior: {junior_count}")
    logger.info(f"   - Middle: {middle_count}")
    logger.info(f"   - Senior: {senior_count}")
    logger.info("")
    logger.info("   Добавление в систему...")
    
    for i, candidate in enumerate(candidates):
        await matching_service.create_candidate(candidate)
        if (i + 1) % 20 == 0:
            logger.info(f"   ✓ Добавлено {i + 1}/{len(candidates)} кандидатов")
    
    logger.info(f"   ✓ Все {len(candidates)} кандидатов добавлены")
    logger.info("")

    for vacancy in vacancies:
        logger.info("=" * 80)
        logger.info(f"  🔍 АНАЛИЗ ВАКАНСИИ: {vacancy.title}")
        logger.info("=" * 80)
        logger.info("")
        
        logger.info(f"Требуемый опыт: {vacancy.experience_years}+ лет")
        logger.info(f"Ключевые навыки: {', '.join(vacancy.skills[:5])}...")
        logger.info("")
        
        # Find matching candidates
        logger.info("⏳ Поиск подходящих кандидатов...")
        logger.info("   Этап 1: Vector search среди всех 80 кандидатов")
        logger.info("   Этап 2: Скрининг по формальным критериям")
        logger.info("   Этап 3: AI multi-agent анализ топ-2 кандидатов")
        logger.info("")
        
        matches = await matching_service.find_candidates_for_vacancy(
            vacancy_id=vacancy.id,
            top_k=10,  # Вернуть топ-10 после скрининга
            ai_analysis_limit=2,  # Но AI агенты проанализируют только топ-2
        )

        logger.info(f"✅ Найдено {len(matches)} подходящих кандидатов")
        logger.info("")

        # Show results
        for idx, match in enumerate(matches, 1):
            logger.info("-" * 80)
            logger.info(f"  🏆 КАНДИДАТ #{idx}")
            logger.info("-" * 80)
            logger.info(f"Имя: {match.details.get('candidate_name')}")
            logger.info(f"Email: {match.details.get('candidate_email')}")
            logger.info(f"Позиция: {match.details.get('desired_position', 'N/A')}")
            logger.info(f"Опыт: {match.details.get('experience_years', 0)} лет")
            logger.info("")
            logger.info(f"📊 ОБЩИЙ SCORE: {match.score:.1%}")
            logger.info(
                f"   - Vector Score: {match.details.get('vector_score', 0):.1%}"
            )
            logger.info(
                f"   - Screening Score: {match.details.get('screening_score', 0):.1%}"
            )
            logger.info(
                f"   - Agent Score: {match.details.get('agent_score', 0):.1%}"
            )
            logger.info("")

            agent_results = match.details.get("agent_results", [])
            if agent_results:
                logger.info(f"🤖 AI MULTI-AGENT АНАЛИЗ ({len(agent_results)} агентов):")
                logger.info("")

                for agent_result in agent_results:
                    logger.info(f"  ┌─ {agent_result.agent_name}")
                    logger.info(f"  │  Score: {agent_result.score:.1%}")
                    logger.info(
                        f"  │  Confidence: {agent_result.confidence:.1%}"
                    )
                    logger.info(f"  │")
                    logger.info(f"  │  💡 Выводы:")
                    for line in agent_result.findings.split(". ")[:3]:  # Первые 3 предложения
                        if line.strip():
                            logger.info(f"  │    {line.strip()}")

                    if agent_result.strengths:
                        logger.info(f"  │  ✅ Сильные стороны:")
                        for strength in agent_result.strengths[:2]:  # Топ-2
                            logger.info(f"  │    • {strength}")

                    if agent_result.weaknesses:
                        logger.info(f"  │  ⚠️  Слабости:")
                        for weakness in agent_result.weaknesses[:2]:  # Топ-2
                            logger.info(f"  │    • {weakness}")

                    logger.info(f"  └─")
                    logger.info("")

                # Overall summary
                logger.info("📝 ОБЩЕЕ РЕЗЮМЕ AI:")
                summary = match.details.get("summary", match.explanation)
                for line in summary.split(". ")[:3]:  # Первые 3 предложения
                    if line.strip():
                        logger.info(f"   {line.strip()}")
                logger.info("")
            else:
                logger.info("ℹ️  AI multi-agent анализ не проводился (не входит в топ-2)")
                logger.info("")
                
                screening = match.details.get("screening_details", {})
                if screening:
                    logger.info("📋 РЕЗУЛЬТАТЫ СКРИНИНГА:")
                    logger.info(f"   - Соответствие опыту: {screening.get('experience_match', False)}")
                    logger.info(f"   - Совпадение навыков: {screening.get('skills_overlap', 0):.1%}")
                    logger.info("")

        logger.info("")

    logger.info("=" * 80)
    logger.info("  ✅ Анализ завершен!")
    logger.info("=" * 80)
    logger.info("")
    logger.info("📈 СТАТИСТИКА:")
    logger.info(f"  • Вакансий: {len(vacancies)}")
    logger.info(f"  • Кандидатов: {len(candidates)}")
    logger.info(f"  • AI multi-agent анализ: только топ-2 для каждой вакансии")
    logger.info(f"  • Задержка между агентами: 10 секунд")
    logger.info("")
    logger.info("🎯 ПРЕИМУЩЕСТВА ПОДХОДА:")
    logger.info("  • Vector search быстро отфильтровывает нерелевантных кандидатов")
    logger.info("  • Скрининг проверяет формальные требования")
    logger.info("  • Дорогой AI анализ применяется только к лучшим кандидатам")
    logger.info("  • Агенты подбираются автоматически по специализации вакансии")


if __name__ == "__main__":
    asyncio.run(main())
