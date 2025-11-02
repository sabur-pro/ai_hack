"""FastAPI dependencies."""

import logging
from functools import lru_cache

from src.infrastructure.ai import GeminiClient
from src.infrastructure.vector_db import ChromaRepository
from src.services import MatchingService, PDFParserService, RAGService

logger = logging.getLogger(__name__)


_gemini_client = None
_vector_repository = None
_rag_service = None
_matching_service = None
_pdf_parser_service = None


def get_gemini_client() -> GeminiClient:
    """Get Gemini client singleton."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
        logger.info("Gemini client created")
    return _gemini_client


def get_vector_repository() -> ChromaRepository:
    """Get vector repository singleton."""
    global _vector_repository
    if _vector_repository is None:
        _vector_repository = ChromaRepository()
        logger.info("Vector repository created")
    return _vector_repository


def get_rag_service() -> RAGService:
    """Get RAG service singleton with PyTorch enhancements."""
    global _rag_service
    if _rag_service is None:
        gemini = get_gemini_client()
        vector_repo = get_vector_repository()
        _rag_service = RAGService(
            gemini, 
            vector_repo,
            use_reranking=True,  # Cross-Encoder реранкинг
            use_semantic_skills=True,  # Семантическое сравнение навыков
        )
        logger.info("RAG service created with PyTorch enhancements")
    return _rag_service


def get_matching_service() -> MatchingService:
    """Get matching service singleton."""
    global _matching_service
    if _matching_service is None:
        rag_service = get_rag_service()
        _matching_service = MatchingService(rag_service)
        logger.info("Matching service created")
    return _matching_service


def get_pdf_parser_service() -> PDFParserService:
    """Get PDF parser service singleton."""
    global _pdf_parser_service
    if _pdf_parser_service is None:
        gemini = get_gemini_client()
        _pdf_parser_service = PDFParserService(gemini)
        logger.info("PDF parser service created")
    return _pdf_parser_service

