"""Matching API endpoints."""

import logging
from typing import Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import get_gemini_client, get_matching_service
from src.core.domain.schemas import MatchingResult
from src.infrastructure.ai import GeminiClient
from src.services import MatchingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/matching", tags=["matching"])


@router.post(
    "/find-candidates/{vacancy_id}",
    response_model=List[MatchingResult],
    summary="Найти подходящих кандидатов для вакансии",
    description="Найти и ранжировать наиболее подходящих кандидатов для заданной вакансии с использованием RAG и AI",
    response_description="Список кандидатов с оценками соответствия и пояснениями",
)
async def find_candidates_for_vacancy(
    vacancy_id: UUID,
    top_k: int = Query(default=5, ge=1, le=20, description="Количество лучших совпадений для возврата (от 1 до 20)"),
    service: MatchingService = Depends(get_matching_service),
) -> List[MatchingResult]:
    """
    Найти подходящих кандидатов для вакансии.

    Система использует RAG (Retrieval-Augmented Generation) и AI для поиска
    наиболее подходящих кандидатов на основе требований вакансии.

    **Процесс:**
    1. Получение вакансии по ID
    2. Векторный поиск похожих кандидатов в ChromaDB
    3. AI-анализ соответствия кандидатов требованиям
    4. Ранжирование кандидатов по оценке соответствия
    5. Генерация детальных пояснений для каждого совпадения

    **Параметры:**
    - **vacancy_id**: UUID вакансии
    - **top_k**: Количество лучших совпадений (по умолчанию 5, максимум 20)

    **Возвращает:**
    - Список кандидатов с:
        - `entity_id`: UUID кандидата
        - `score`: Оценка соответствия (0.0 - 1.0)
        - `explanation`: Детальное пояснение о соответствии
        - `details`: Дополнительные детали анализа

    **Ошибки:**
    - 404: Вакансия не найдена
    - 500: Внутренняя ошибка сервера
    """
    try:
        results = await service.find_candidates_for_vacancy(
            vacancy_id=vacancy_id,
            top_k=top_k,
        )

        logger.info(f"Found {len(results)} candidates for vacancy {vacancy_id}")
        return results

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error finding candidates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/find-vacancies/{candidate_id}",
    response_model=List[MatchingResult],
    summary="Найти подходящие вакансии для кандидата",
    description="Найти и ранжировать наиболее подходящие вакансии для заданного кандидата с использованием RAG и AI",
    response_description="Список вакансий с оценками соответствия и пояснениями",
)
async def find_vacancies_for_candidate(
    candidate_id: UUID,
    top_k: int = Query(default=5, ge=1, le=20, description="Количество лучших совпадений для возврата (от 1 до 20)"),
    service: MatchingService = Depends(get_matching_service),
) -> List[MatchingResult]:
    """
    Найти подходящие вакансии для кандидата.

    Система использует RAG (Retrieval-Augmented Generation) и AI для поиска
    наиболее подходящих вакансий на основе навыков и опыта кандидата.

    **Процесс:**
    1. Получение кандидата по ID
    2. Векторный поиск похожих вакансий в ChromaDB
    3. AI-анализ соответствия вакансий профилю кандидата
    4. Ранжирование вакансий по оценке соответствия
    5. Генерация детальных пояснений для каждого совпадения

    **Параметры:**
    - **candidate_id**: UUID кандидата
    - **top_k**: Количество лучших совпадений (по умолчанию 5, максимум 20)

    **Возвращает:**
    - Список вакансий с:
        - `entity_id`: UUID вакансии
        - `score`: Оценка соответствия (0.0 - 1.0)
        - `explanation`: Детальное пояснение о соответствии
        - `details`: Дополнительные детали анализа

    **Ошибки:**
    - 404: Кандидат не найден
    - 500: Внутренняя ошибка сервера
    """
    try:
        results = await service.find_vacancies_for_candidate(
            candidate_id=candidate_id,
            top_k=top_k,
        )

        logger.info(f"Found {len(results)} vacancies for candidate {candidate_id}")
        return results

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error finding vacancies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/all-vacancies-with-candidates",
    response_model=dict,
    summary="Получить всех кандидатов для всех вакансий",
    description="Массовый подбор кандидатов для всех вакансий с PyTorch улучшениями (реранкинг + семантические навыки)",
    response_description="Словарь с вакансиями и подобранными кандидатами",
)
async def get_all_vacancies_with_candidates(
    top_k: int = Query(default=5, ge=1, le=20, description="Количество кандидатов для каждой вакансии (от 1 до 20)"),
    use_ai: bool = Query(default=False, description="Использовать AI агентов для анализа (медленно и дорого)"),
    use_reranking: bool = Query(default=True, description="Использовать Cross-Encoder реранкинг (PyTorch, точнее)"),
    use_semantic_skills: bool = Query(default=True, description="Использовать семантическое сравнение навыков (PyTorch)"),
    service: MatchingService = Depends(get_matching_service),
) -> dict:
    """
    Получить подходящих кандидатов для всех вакансий.

    Этот эндпоинт выполняет массовый подбор кандидатов для всех вакансий в системе.
    Улучшен с помощью PyTorch для более точного подбора.

    **🚀 PyTorch улучшения:**
    1. **Cross-Encoder реранкинг** - точная оценка пары (вакансия, кандидат)
    2. **Семантическое сравнение навыков** - понимание похожих технологий
       - "Python" ≈ "Python3"
       - "Django" ≈ "Django REST Framework" 
       - "PostgreSQL" ≈ "Postgres"

    **Процесс:**
    1. Получение всех вакансий из системы
    2. Для каждой вакансии:
       - Векторный поиск похожих кандидатов в ChromaDB
       - [НОВОЕ] Cross-Encoder реранкинг для точной оценки
       - Мульти-этапный скрининг с семантическим сравнением навыков
       - Ранжирование по комбинированному score
    3. Возврат результатов для всех вакансий

    **Параметры:**
    - **top_k**: Количество кандидатов для каждой вакансии (по умолчанию 5, максимум 20)
    - **use_ai**: Использовать AI агентов (медленно, по умолчанию false)
    - **use_reranking**: Cross-Encoder реранкинг (рекомендуется, точнее)
    - **use_semantic_skills**: Семантическое сравнение навыков (рекомендуется)

    **Возвращает:**
    - `total_vacancies`: Общее количество вакансий
    - `total_matches`: Общее количество совпадений
    - `ranking_summary`: Простой список рангов (для быстрого просмотра)
        - `job_title`: Название вакансии
        - `rank`: Ранг кандидата (1 = лучший)
        - `candidate_name`: Имя кандидата
        - `score`: Оценка совпадения
    - `vacancies`: Детализация для каждой вакансии
        - `vacancy_id`: UUID вакансии
        - `vacancy_title`: Название вакансии
        - `vacancy_location`: Локация вакансии
        - `candidates_count`: Количество найденных кандидатов
        - `ranked_candidates`: Кандидаты с рангами
        - `candidates`: Полные детали кандидатов

    **Формат ответа:**
    
    Пример `ranking_summary` (простой список):
    ```json
    [
      {"job_title": "Senior Python Dev", "rank": 1, "candidate_name": "Resume87", "score": 0.92},
      {"job_title": "Senior Python Dev", "rank": 2, "candidate_name": "Resume27", "score": 0.87},
      {"job_title": "Senior Python Dev", "rank": 3, "candidate_name": "Resume25", "score": 0.85},
      ...
      {"job_title": "DevOps Engineer", "rank": 1, "candidate_name": "Resume15", "score": 0.88}
    ]
    ```
    
    **Оценки (scores):**
    - `vector_score`: Векторное сходство (0.0 - 1.0)
    - `screening_score`: Оценка скрининга (0.0 - 1.0)
    - `combined_score`: Комбинированная оценка (0.0 - 1.0)
    - `hard_skills_score`: Совпадение навыков
    - `experience_score`: Совпадение опыта
    - `location_score`: Совпадение локации

    **Ошибки:**
    - 500: Внутренняя ошибка сервера
    """
    try:
        results = await service.find_all_vacancies_with_candidates(
            top_k=top_k,
            use_ai=use_ai,
        )

        # Генерируем простой список рангов (job_title, rank, candidate_name)
        ranking_summary = []
        for vacancy_id, vacancy_data in results.items():
            if 'error' in vacancy_data:
                continue
            
            for ranked_candidate in vacancy_data.get('ranked_candidates', []):
                ranking_summary.append({
                    "job_title": vacancy_data['vacancy_title'],
                    "rank": ranked_candidate['rank'],
                    "candidate_name": ranked_candidate['candidate_name'],
                    "score": ranked_candidate['score'],
                })
        
        return {
            "total_vacancies": len(results),
            "total_matches": len(ranking_summary),
            "ranking_summary": ranking_summary,  # Простой формат: job_title, rank, candidate
            "vacancies": results,  # Полная детализация
        }

    except Exception as e:
        logger.error(f"Error finding candidates for all vacancies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/ask",
    response_model=dict,
    summary="Задать вопрос AI агенту",
    description="Задать вопрос AI агенту и получить интеллектуальный ответ с использованием Google Gemini",
    response_description="Ответ от AI агента",
)
async def ask_question(
    question: str = Query(..., min_length=3, description="Вопрос для AI агента (минимум 3 символа)"),
    gemini: GeminiClient = Depends(get_gemini_client),
) -> dict:
    """
    Задать вопрос AI агенту.

    Этот эндпоинт позволяет взаимодействовать с AI агентом напрямую.
    Агент может отвечать на вопросы о кандидатах, вакансиях, рекрутинге и других темах.

    **Примеры вопросов:**
    - "Какие навыки наиболее востребованы для Python разработчика?"
    - "Как составить хорошее описание вакансии?"
    - "Какие критерии важны при оценке кандидата?"
    - "Расскажи о процессе технического интервью"

    **Параметры:**
    - **question**: Вопрос для AI агента (минимум 3 символа)

    **Возвращает:**
    - `question`: Исходный вопрос
    - `answer`: Ответ от AI агента

    **Ошибки:**
    - 500: Ошибка при генерации ответа
    """
    try:
        answer = await gemini.answer_question(question)

        return {
            "question": question,
            "answer": answer,
        }

    except Exception as e:
        logger.error(f"Error answering question: {e}")
        raise HTTPException(status_code=500, detail=str(e))

