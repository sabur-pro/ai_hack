"""Candidate API endpoints."""

import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from src.api.dependencies import get_matching_service, get_pdf_parser_service
from src.core.domain.models import Candidate
from src.core.domain.schemas import CandidateCreate, CandidateResponse
from src.services import MatchingService, PDFParserService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.post(
    "/",
    response_model=CandidateResponse,
    status_code=201,
    summary="Создать кандидата",
    description="Создать нового кандидата с указанием всех полей вручную",
    response_description="Созданный кандидат со всеми данными",
)
async def create_candidate(
    candidate_data: CandidateCreate,
    service: MatchingService = Depends(get_matching_service),
) -> CandidateResponse:
    """
    Создать нового кандидата.

    Этот эндпоинт позволяет создать кандидата, указав все поля вручную.

    **Параметры:**
    - **name**: ФИО кандидата (обязательно, 1-100 символов)
    - **email**: Email кандидата (обязательно, валидный формат)
    - **phone**: Телефон (необязательно)
    - **summary**: Краткое резюме кандидата (обязательно, минимум 10 символов)
    - **skills**: Список навыков кандидата
    - **experience**: Список опыта работы
    - **education**: Список образования
    - **experience_years**: Общий опыт работы в годах (необязательно)
    - **desired_position**: Желаемая должность (необязательно)
    - **desired_salary**: Желаемая зарплата (необязательно)
    - **location**: Местоположение (необязательно)

    **Возвращает:**
    - Созданный кандидат со всеми данными включая ID и дату создания
    """
    try:
        candidate = Candidate(**candidate_data.model_dump())

        created_candidate = await service.create_candidate(candidate)

        logger.info(f"Candidate created: {created_candidate.id}")
        return CandidateResponse(**created_candidate.model_dump())

    except Exception as e:
        logger.error(f"Error creating candidate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/upload-pdf",
    response_model=CandidateResponse,
    status_code=201,
    summary="Загрузить резюме кандидата из PDF",
    description="Загрузить PDF файл резюме кандидата, извлечь текст и автоматически структурировать данные с помощью AI",
    response_description="Созданный кандидат с данными, извлеченными из PDF",
)
async def create_candidate_from_pdf(
    file: UploadFile = File(..., description="PDF файл с резюме кандидата"),
    matching_service: MatchingService = Depends(get_matching_service),
    pdf_service: PDFParserService = Depends(get_pdf_parser_service),
) -> CandidateResponse:
    """
    Создать кандидата из PDF файла.

    Этот эндпоинт позволяет загрузить PDF файл с резюме кандидата.
    Система автоматически извлечет текст из PDF и структурирует данные с помощью AI.

    **Процесс:**
    1. Загрузка PDF файла
    2. Извлечение текста из PDF
    3. Анализ текста с помощью AI (Google Gemini)
    4. Структурирование данных в формат кандидата
    5. Создание кандидата в системе

    **Требования к файлу:**
    - Формат: PDF
    - Максимальный размер: 10 MB
    - Файл должен содержать читаемый текст

    **Возвращает:**
    - Созданный кандидат со всеми извлеченными данными
    """
    try:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Неверный формат файла. Поддерживается только PDF"
            )

        # Read file content
        pdf_content = await file.read()
        
        # Check file size (10 MB limit)
        if len(pdf_content) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="Размер файла превышает 10 MB"
            )

        # Parse PDF and structure data
        structured_data = await pdf_service.parse_candidate_pdf(pdf_content)

        candidate_create = CandidateCreate(**structured_data)
        candidate = Candidate(**candidate_create.model_dump())
        
        created_candidate = await matching_service.create_candidate(candidate)

        logger.info(f"Candidate created from PDF: {created_candidate.id} - {created_candidate.name}")
        return CandidateResponse(**created_candidate.model_dump())

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Error parsing PDF: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating candidate from PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@router.post(
    "/upload-pdf-batch",
    response_model=List[CandidateResponse],
    status_code=201,
    summary="Загрузить несколько резюме из PDF (batch)",
    description="Загрузить до 100 PDF файлов резюме за один раз, извлечь тексты и структурировать с помощью AI одним запросом",
    response_description="Список созданных кандидатов",
)
async def create_candidates_from_pdf_batch(
    files: List[UploadFile] = File(..., description="PDF файлы с резюме кандидатов (максимум 100)"),
    matching_service: MatchingService = Depends(get_matching_service),
    pdf_service: PDFParserService = Depends(get_pdf_parser_service),
) -> List[CandidateResponse]:
    """
    Создать нескольких кандидатов из PDF файлов за один раз.
    
    **Преимущества batch загрузки:**
    - Быстрее: один запрос к AI вместо N запросов
    - Дешевле: экономия на API вызовах
    - Удобнее: загрузите все резюме сразу
    
    **Процесс:**
    1. Загрузка до 100 PDF файлов
    2. Извлечение текста из всех PDF
    3. Отправка всех текстов в AI одним запросом
    4. Структурирование данных для всех кандидатов
    5. Создание всех кандидатов в системе
    
    **Требования:**
    - Максимум 100 файлов за раз
    - Каждый файл: PDF, максимум 10 MB
    - Все файлы должны содержать читаемый текст
    
    **Возвращает:**
    - Список всех созданных кандидатов с данными
    
    **Ошибки:**
    - 400: Некорректные файлы или превышен лимит
    - 500: Ошибка обработки
    """
    try:
        # Проверка количества файлов
        if len(files) > 100:
            raise HTTPException(
                status_code=400,
                detail=f"Превышен лимит файлов. Максимум 100, загружено {len(files)}"
            )
        
        if len(files) == 0:
            raise HTTPException(
                status_code=400,
                detail="Не загружено ни одного файла"
            )
        
        logger.info(f"🚀 Начата batch загрузка {len(files)} резюме из PDF")
        
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
            structured_data_list = await pdf_service.parse_candidates_batch(
                pdf_contents=pdf_contents,
                filenames=filenames
            )
            logger.info(f"🤖 AI вернул {len(structured_data_list)} структурированных кандидатов")
        except Exception as e:
            logger.error(f"❌ ОШИБКА при обработке AI: {e}")
            raise
        
        # Создаем всех кандидатов
        logger.info(f"💾 Начинаю создавать {len(structured_data_list)} кандидатов...")
        created_candidates = []
        
        for idx, data in enumerate(structured_data_list, 1):
            try:
                logger.info(f"🔄 Создаю кандидата {idx}/{len(structured_data_list)}: {data.get('name', 'Unknown')}")
                
                candidate_create = CandidateCreate(**data)
                logger.info(f"  ✓ CandidateCreate создан")
                
                candidate = Candidate(**candidate_create.model_dump())
                logger.info(f"  ✓ Candidate model создан с ID: {candidate.id}")
                
                created_candidate = await matching_service.create_candidate(candidate)
                logger.info(f"  ✓ matching_service.create_candidate завершен")
                
                created_candidates.append(created_candidate)
                logger.info(f"✅ Создан кандидат {idx}/{len(structured_data_list)}: {created_candidate.name} (ID: {created_candidate.id})")
            except Exception as e:
                logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА при создании кандидата {idx}: {type(e).__name__}: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                # Продолжаем создавать остальных
                continue
        
        logger.info(f"🎉 Успешно создано {len(created_candidates)}/{len(structured_data_list)} кандидатов из PDF batch")
        
        # Проверяем, что кандидаты реально сохранены
        all_candidates = await matching_service.list_candidates()
        logger.info(f"📊 Всего кандидатов в системе сейчас: {len(all_candidates)}")
        
        return [CandidateResponse(**c.model_dump()) for c in created_candidates]
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Error parsing PDFs: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating candidates from PDF batch: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@router.get(
    "/stats",
    response_model=dict,
    summary="Статистика по кандидатам",
    description="Получить статистику: сколько кандидатов в системе",
    response_description="Статистика кандидатов",
)
async def get_candidates_stats(
    service: MatchingService = Depends(get_matching_service),
) -> dict:
    """
    Получить статистику по кандидатам.
    
    **Возвращает:**
    - `total`: Общее количество кандидатов в системе
    - `sample`: Примеры первых 5 кандидатов (name и id)
    """
    try:
        candidates = await service.list_candidates()
        
        sample = []
        for c in candidates[:5]:
            sample.append({
                "id": str(c.id),
                "name": c.name,
                "email": c.email,
                "created_at": c.created_at.isoformat()
            })
        
        return {
            "total": len(candidates),
            "sample": sample
        }
    
    except Exception as e:
        logger.error(f"Error getting candidates stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/",
    response_model=List[CandidateResponse],
    summary="Получить список всех кандидатов",
    description="Получить список всех созданных кандидатов в системе",
    response_description="Список всех кандидатов",
)
async def list_candidates(
    service: MatchingService = Depends(get_matching_service),
) -> List[CandidateResponse]:
    """
    Получить список всех кандидатов.

    **Возвращает:**
    - Список всех кандидатов в системе с полными данными
    """
    try:
        candidates = await service.list_candidates()
        logger.info(f"📋 Возвращаю {len(candidates)} кандидатов")
        return [CandidateResponse(**c.model_dump()) for c in candidates]

    except Exception as e:
        logger.error(f"Error listing candidates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{candidate_id}",
    response_model=CandidateResponse,
    summary="Получить кандидата по ID",
    description="Получить детальную информацию о конкретном кандидате по его ID",
    response_description="Данные кандидата",
)
async def get_candidate(
    candidate_id: UUID,
    service: MatchingService = Depends(get_matching_service),
) -> CandidateResponse:
    """
    Получить кандидата по ID.

    **Параметры:**
    - **candidate_id**: UUID кандидата

    **Возвращает:**
    - Полные данные кандидата

    **Ошибки:**
    - 404: Кандидат не найден
    """
    try:
        candidate = await service.get_candidate(candidate_id)

        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        return CandidateResponse(**candidate.model_dump())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting candidate: {e}")
        raise HTTPException(status_code=500, detail=str(e))

