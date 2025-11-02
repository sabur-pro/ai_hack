"""Main application entry point."""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import candidates_router, matching_router, vacancies_router
from src.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.debug else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    yield
    logger.info("Shutting down application")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
# AI-Powered HR Matching System 🤖

Интеллектуальная система подбора персонала с использованием RAG (Retrieval-Augmented Generation), 
векторной базы данных и Google Gemini AI.

## Основные возможности

### 📄 Работа с вакансиями
- Создание вакансий вручную или загрузка из PDF
- Автоматическое извлечение и структурирование данных из PDF с помощью AI
- Получение списка всех вакансий
- Получение детальной информации о вакансии

### 👤 Работа с кандидатами
- Создание профилей кандидатов вручную или загрузка резюме из PDF
- Автоматическое извлечение и структурирование данных из резюме
- Получение списка всех кандидатов
- Получение детальной информации о кандидате

### 🎯 Интеллектуальный подбор (Matching)
- **Массовый подбор** кандидатов для всех вакансий (БЕЗ AI - быстро и дешево)
- Поиск подходящих кандидатов для вакансии с AI-анализом
- Поиск подходящих вакансий для кандидата
- Ранжирование результатов с оценками соответствия (0.0-1.0)
- Детальные пояснения для каждого совпадения

### 💬 AI Ассистент
- Задавайте вопросы AI агенту о рекрутинге, навыках, вакансиях

## Технологии

- **FastAPI** - современный веб-фреймворк для API
- **Google Gemini AI** - передовая языковая модель для анализа и генерации
- **ChromaDB** - векторная база данных для семантического поиска
- **RAG** - Retrieval-Augmented Generation для точного подбора
- **PDF парсинг** - автоматическое извлечение текста из документов

## Быстрый старт

1. Создайте вакансию: `POST /api/v1/vacancies/` или `POST /api/v1/vacancies/upload-pdf`
2. Создайте кандидатов: `POST /api/v1/candidates/` или `POST /api/v1/candidates/upload-pdf`
3. **Массовый подбор** для всех вакансий: `GET /api/v1/matching/all-vacancies-with-candidates`
4. Найдите подходящих кандидатов для вакансии: `POST /api/v1/matching/find-candidates/{vacancy_id}`
5. Найдите подходящие вакансии для кандидата: `POST /api/v1/matching/find-vacancies/{candidate_id}`

---
**Документация**: Используйте `/docs` для интерактивной документации Swagger UI
""",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "vacancies",
            "description": "Операции с вакансиями: создание, получение, загрузка из PDF",
        },
        {
            "name": "candidates", 
            "description": "Операции с кандидатами: создание, получение, загрузка резюме из PDF",
        },
        {
            "name": "matching",
            "description": "Интеллектуальный подбор кандидатов и вакансий с использованием AI и RAG",
        },
    ],
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(vacancies_router, prefix="/api/v1")
app.include_router(candidates_router, prefix="/api/v1")
app.include_router(matching_router, prefix="/api/v1")


@app.get(
    "/",
    summary="Главная страница API",
    description="Основная информация об API и доступных эндпоинтах",
    tags=["info"],
)
async def root():
    """
    Главная страница API.
    
    Возвращает основную информацию о системе и ссылки на документацию.
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "description": "AI-Powered HR Matching System",
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_json": "/openapi.json",
        },
        "endpoints": {
            "vacancies": "/api/v1/vacancies",
            "candidates": "/api/v1/candidates",
            "matching": "/api/v1/matching",
        },
        "features": [
            "PDF upload and parsing for vacancies and candidates",
            "AI-powered data extraction and structuring",
            "Intelligent candidate-vacancy matching using RAG",
            "Vector similarity search with ChromaDB",
            "Google Gemini AI integration",
        ],
    }


@app.get(
    "/health",
    summary="Проверка здоровья системы",
    description="Эндпоинт для проверки доступности и работоспособности API",
    tags=["info"],
)
async def health():
    """
    Проверка здоровья системы.
    
    Используется для мониторинга и проверки доступности API.
    """
    return {
        "status": "healthy",
        "version": settings.app_version,
        "services": {
            "api": "online",
            "gemini_ai": "configured",
            "vector_db": "configured",
        }
    }


def main():
    """Run the application."""
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning",
    )


if __name__ == "__main__":
    main()

