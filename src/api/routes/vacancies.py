"""Vacancy API endpoints."""

import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from src.api.dependencies import get_matching_service, get_pdf_parser_service
from src.core.domain.models import Vacancy
from src.core.domain.schemas import VacancyCreate, VacancyResponse
from src.services import MatchingService, PDFParserService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vacancies", tags=["vacancies"])


@router.post(
    "/",
    response_model=VacancyResponse,
    status_code=201,
    summary="Создать вакансию",
    description="Создать новую вакансию с указанием всех полей вручную",
    response_description="Созданная вакансия со всеми данными",
)
async def create_vacancy(
    vacancy_data: VacancyCreate,
    service: MatchingService = Depends(get_matching_service),
) -> VacancyResponse:
    """
    Создать новую вакансию.

    Этот эндпоинт позволяет создать вакансию, указав все поля вручную.

    **Параметры:**
    - **title**: Название вакансии (обязательно, 1-200 символов)
    - **description**: Детальное описание вакансии (обязательно, минимум 10 символов)
    - **requirements**: Список требований к кандидату
    - **responsibilities**: Список обязанностей
    - **skills**: Список необходимых навыков
    - **experience_years**: Требуемый опыт работы в годах (необязательно)
    - **salary_range**: Диапазон зарплаты (необязательно)
    - **location**: Местоположение работы (необязательно)
    - **employment_type**: Тип занятости (по умолчанию "full-time")

    **Возвращает:**
    - Созданная вакансия со всеми данными включая ID и дату создания
    """
    try:
        vacancy = Vacancy(**vacancy_data.model_dump())

        created_vacancy = await service.create_vacancy(vacancy)

        logger.info(f"Vacancy created: {created_vacancy.id}")
        return VacancyResponse(**created_vacancy.model_dump())

    except Exception as e:
        logger.error(f"Error creating vacancy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/upload-pdf",
    response_model=VacancyResponse,
    status_code=201,
    summary="Загрузить вакансию из PDF",
    description="Загрузить PDF файл вакансии, извлечь текст и автоматически структурировать данные с помощью AI",
    response_description="Созданная вакансия с данными, извлеченными из PDF",
)
async def create_vacancy_from_pdf(
    file: UploadFile = File(..., description="PDF файл с описанием вакансии"),
    matching_service: MatchingService = Depends(get_matching_service),
    pdf_service: PDFParserService = Depends(get_pdf_parser_service),
) -> VacancyResponse:
    """
    Создать вакансию из PDF файла.

    Этот эндпоинт позволяет загрузить PDF файл с описанием вакансии.
    Система автоматически извлечет текст из PDF и структурирует данные с помощью AI.

    **Процесс:**
    1. Загрузка PDF файла
    2. Извлечение текста из PDF
    3. Анализ текста с помощью AI (Google Gemini)
    4. Структурирование данных в формат вакансии
    5. Создание вакансии в системе

    **Требования к файлу:**
    - Формат: PDF
    - Максимальный размер: 10 MB
    - Файл должен содержать читаемый текст

    **Возвращает:**
    - Созданная вакансия со всеми извлеченными данными
    """
    try:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Неверный формат файла. Поддерживается только PDF"
            )

        pdf_content = await file.read()
        
        if len(pdf_content) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="Размер файла превышает 10 MB"
            )

        structured_data = await pdf_service.parse_vacancy_pdf(pdf_content)

        vacancy_create = VacancyCreate(**structured_data)
        vacancy = Vacancy(**vacancy_create.model_dump())
        
        created_vacancy = await matching_service.create_vacancy(vacancy)

        logger.info(f"Vacancy created from PDF: {created_vacancy.id} - {created_vacancy.title}")
        return VacancyResponse(**created_vacancy.model_dump())

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Error parsing PDF: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating vacancy from PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@router.post(
    "/upload-pdf-batch",
    response_model=List[VacancyResponse],
    status_code=201,
    summary="Загрузить несколько вакансий из PDF (batch)",
    description="Загрузить до 40 PDF файлов вакансий за один раз, извлечь тексты и структурировать с помощью AI одним запросом",
    response_description="Список созданных вакансий",
)
async def create_vacancies_from_pdf_batch(
    files: List[UploadFile] = File(..., description="PDF файлы с описаниями вакансий (максимум 40)"),
    matching_service: MatchingService = Depends(get_matching_service),
    pdf_service: PDFParserService = Depends(get_pdf_parser_service),
) -> List[VacancyResponse]:
    """
    Создать несколько вакансий из PDF файлов за один раз.
    
    **Преимущества batch загрузки:**
    - Быстрее: один запрос к AI вместо N запросов
    - Дешевле: экономия на API вызовах
    - Удобнее: загрузите все файлы сразу
    
    **Процесс:**
    1. Загрузка до 40 PDF файлов
    2. Извлечение текста из всех PDF
    3. Отправка всех текстов в AI одним запросом
    4. Структурирование данных для всех вакансий
    5. Создание всех вакансий в системе
    
    **Требования:**
    - Максимум 40 файлов за раз
    - Каждый файл: PDF, максимум 10 MB
    - Все файлы должны содержать читаемый текст
    
    **Возвращает:**
    - Список всех созданных вакансий с данными
    
    **Ошибки:**
    - 400: Некорректные файлы или превышен лимит
    - 500: Ошибка обработки
    """
    try:
        # Проверка количества файлов
        if len(files) > 40:
            raise HTTPException(
                status_code=400,
                detail=f"Превышен лимит файлов. Максимум 40, загружено {len(files)}"
            )
        
        if len(files) == 0:
            raise HTTPException(
                status_code=400,
                detail="Не загружено ни одного файла"
            )
        
        logger.info(f"🚀 Начата batch загрузка {len(files)} вакансий из PDF")
        
        # Собираем все PDF
        pdf_contents = []
        filenames = []
        
        for file in files:
            logger.info(f"📄 Проверяю файл: {file.filename}")
            
            if not file.filename.lower().endswith('.pdf'):
                raise HTTPException(
                    status_code=400,
                    detail=f"Файл {file.filename}: неверный формат. Поддерживается только PDF"
                )
            
            content = await file.read()
            logger.info(f"📄 Прочитано {len(content)} байт из {file.filename}")
            
            if len(content) > 10 * 1024 * 1024:
                raise HTTPException(
                    status_code=400,
                    detail=f"Файл {file.filename}: размер превышает 10 MB"
                )
            
            pdf_contents.append(content)
            filenames.append(file.filename)
        
        logger.info(f"📦 Собрано {len(pdf_contents)} PDF файлов, отправляю в AI...")
        
        # Batch обработка всех PDF одним запросом к AI
        try:
            structured_data_list = await pdf_service.parse_vacancies_batch(
                pdf_contents=pdf_contents,
                filenames=filenames
            )
            logger.info(f"🤖 AI вернул {len(structured_data_list)} структурированных вакансий")
        except Exception as e:
            logger.error(f"❌ ОШИБКА при обработке AI: {e}")
            raise
        
        # Создаем все вакансии
        logger.info(f"💾 Начинаю создавать {len(structured_data_list)} вакансий...")
        created_vacancies = []
        
        for idx, data in enumerate(structured_data_list, 1):
            try:
                logger.info(f"🔄 Создаю вакансию {idx}/{len(structured_data_list)}: {data.get('title', 'Unknown')}")
                
                vacancy_create = VacancyCreate(**data)
                logger.info(f"  ✓ VacancyCreate создан")
                
                vacancy = Vacancy(**vacancy_create.model_dump())
                logger.info(f"  ✓ Vacancy model создан с ID: {vacancy.id}")
                
                created_vacancy = await matching_service.create_vacancy(vacancy)
                logger.info(f"  ✓ matching_service.create_vacancy завершен")
                
                created_vacancies.append(created_vacancy)
                logger.info(f"✅ Создана вакансия {idx}/{len(structured_data_list)}: {created_vacancy.title} (ID: {created_vacancy.id})")
            except Exception as e:
                logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА при создании вакансии {idx}: {type(e).__name__}: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                # Продолжаем создавать остальные
                continue
        
        logger.info(f"🎉 Успешно создано {len(created_vacancies)}/{len(structured_data_list)} вакансий из PDF batch")
        
        # Проверяем, что вакансии реально сохранены
        all_vacancies = await matching_service.list_vacancies()
        logger.info(f"📊 Всего вакансий в системе сейчас: {len(all_vacancies)}")
        
        return [VacancyResponse(**v.model_dump()) for v in created_vacancies]
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Error parsing PDFs: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating vacancies from PDF batch: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@router.get(
    "/stats",
    response_model=dict,
    summary="Статистика по вакансиям",
    description="Получить статистику: сколько вакансий в системе",
    response_description="Статистика вакансий",
)
async def get_vacancies_stats(
    service: MatchingService = Depends(get_matching_service),
) -> dict:
    """
    Получить статистику по вакансиям.
    
    **Возвращает:**
    - `total`: Общее количество вакансий в системе
    - `sample`: Примеры первых 5 вакансий (title и id)
    """
    try:
        vacancies = await service.list_vacancies()
        
        sample = []
        for v in vacancies[:5]:
            sample.append({
                "id": str(v.id),
                "title": v.title,
                "created_at": v.created_at.isoformat()
            })
        
        return {
            "total": len(vacancies),
            "sample": sample
        }
    
    except Exception as e:
        logger.error(f"Error getting vacancies stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/",
    response_model=List[VacancyResponse],
    summary="Получить список всех вакансий",
    description="Получить список всех созданных вакансий в системе",
    response_description="Список всех вакансий",
)
async def list_vacancies(
    service: MatchingService = Depends(get_matching_service),
) -> List[VacancyResponse]:
    """
    Получить список всех вакансий.

    **Возвращает:**
    - Список всех вакансий в системе с полными данными
    """
    try:
        vacancies = await service.list_vacancies()
        logger.info(f"📋 Возвращаю {len(vacancies)} вакансий")
        return [VacancyResponse(**v.model_dump()) for v in vacancies]

    except Exception as e:
        logger.error(f"Error listing vacancies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{vacancy_id}",
    response_model=VacancyResponse,
    summary="Получить вакансию по ID",
    description="Получить детальную информацию о конкретной вакансии по её ID",
    response_description="Данные вакансии",
)
async def get_vacancy(
    vacancy_id: UUID,
    service: MatchingService = Depends(get_matching_service),
) -> VacancyResponse:
    """
    Получить вакансию по ID.

    **Параметры:**
    - **vacancy_id**: UUID вакансии

    **Возвращает:**
    - Полные данные вакансии

    **Ошибки:**
    - 404: Вакансия не найдена
    """
    try:
        vacancy = await service.get_vacancy(vacancy_id)

        if not vacancy:
            raise HTTPException(status_code=404, detail="Vacancy not found")

        return VacancyResponse(**vacancy.model_dump())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vacancy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

