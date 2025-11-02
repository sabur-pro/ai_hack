"""ChromaDB repository for vector storage and retrieval."""

import logging
from typing import Dict, List, Optional
from uuid import UUID

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from src.core.config import settings

logger = logging.getLogger(__name__)


class ChromaRepository:
    """Repository for managing vectors in ChromaDB."""

    def __init__(self):
        """Initialize ChromaDB client and embedding model."""
        self.client = chromadb.PersistentClient(
            path=settings.vector_db_path,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        self.embedding_model = SentenceTransformer(settings.embedding_model)

        self.vacancy_collection = self.client.get_or_create_collection(
            name=f"{settings.collection_name}_vacancies",
            metadata={"description": "Vacancy embeddings"},
        )

        self.candidate_collection = self.client.get_or_create_collection(
            name=f"{settings.collection_name}_candidates",
            metadata={"description": "Candidate embeddings"},
        )

        logger.info("ChromaDB repository initialized")

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        embedding = self.embedding_model.encode(text)
        return embedding.tolist()

    async def add_vacancy(
        self,
        vacancy_id: UUID,
        vacancy_text: str,
        metadata: Optional[Dict] = None,
    ) -> None:
        """
        Add vacancy to vector database.

        Args:
            vacancy_id: Unique vacancy identifier
            vacancy_text: Text representation of vacancy
            metadata: Additional metadata
        """
        try:
            embedding = self._generate_embedding(vacancy_text)

            self.vacancy_collection.add(
                ids=[str(vacancy_id)],
                embeddings=[embedding],
                documents=[vacancy_text],
                metadatas=[metadata or {}],
            )

            logger.info(f"Added vacancy {vacancy_id} to vector database")

        except Exception as e:
            logger.error(f"Error adding vacancy to vector database: {e}")
            raise

    async def add_candidate(
        self,
        candidate_id: UUID,
        candidate_text: str,
        metadata: Optional[Dict] = None,
    ) -> None:
        """
        Add candidate to vector database.

        Args:
            candidate_id: Unique candidate identifier
            candidate_text: Text representation of candidate
            metadata: Additional metadata
        """
        try:
            embedding = self._generate_embedding(candidate_text)

            self.candidate_collection.add(
                ids=[str(candidate_id)],
                embeddings=[embedding],
                documents=[candidate_text],
                metadatas=[metadata or {}],
            )

            logger.info(f"Added candidate {candidate_id} to vector database")

        except Exception as e:
            logger.error(f"Error adding candidate to vector database: {e}")
            raise

    async def search_candidates(
        self,
        vacancy_text: str,
        top_k: int = 5,
    ) -> List[Dict]:
        """
        Search for candidates matching vacancy.

        Args:
            vacancy_text: Text representation of vacancy
            top_k: Number of top candidates to return

        Returns:
            List of matching candidates with scores
        """
        try:
            embedding = self._generate_embedding(vacancy_text)

            results = self.candidate_collection.query(
                query_embeddings=[embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )

            matches = []
            if results["ids"]:
                for idx, candidate_id in enumerate(results["ids"][0]):

                    distance = results["distances"][0][idx]
                    similarity = 1 / (1 + distance)

                    matches.append({
                        "id": candidate_id,
                        "document": results["documents"][0][idx],
                        "metadata": results["metadatas"][0][idx],
                        "score": similarity,
                        "distance": distance,
                    })

            logger.info(f"Found {len(matches)} matching candidates")
            return matches

        except Exception as e:
            logger.error(f"Error searching candidates: {e}")
            raise

    async def search_vacancies(
        self,
        candidate_text: str,
        top_k: int = 5,
    ) -> List[Dict]:
        """
        Search for vacancies matching candidate.

        Args:
            candidate_text: Text representation of candidate
            top_k: Number of top vacancies to return

        Returns:
            List of matching vacancies with scores
        """
        try:
            embedding = self._generate_embedding(candidate_text)

            results = self.vacancy_collection.query(
                query_embeddings=[embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )

            matches = []
            if results["ids"]:
                for idx, vacancy_id in enumerate(results["ids"][0]):
                    distance = results["distances"][0][idx]
                    similarity = 1 / (1 + distance)

                    matches.append({
                        "id": vacancy_id,
                        "document": results["documents"][0][idx],
                        "metadata": results["metadatas"][0][idx],
                        "score": similarity,
                        "distance": distance,
                    })

            logger.info(f"Found {len(matches)} matching vacancies")
            return matches

        except Exception as e:
            logger.error(f"Error searching vacancies: {e}")
            raise

    async def get_vacancy(self, vacancy_id: UUID) -> Optional[Dict]:
        """Get vacancy by ID."""
        try:
            result = self.vacancy_collection.get(
                ids=[str(vacancy_id)],
                include=["documents", "metadatas"],
            )

            if result["ids"]:
                return {
                    "id": result["ids"][0],
                    "document": result["documents"][0],
                    "metadata": result["metadatas"][0],
                }

            return None

        except Exception as e:
            logger.error(f"Error getting vacancy: {e}")
            return None

    async def get_candidate(self, candidate_id: UUID) -> Optional[Dict]:
        """Get candidate by ID."""
        try:
            result = self.candidate_collection.get(
                ids=[str(candidate_id)],
                include=["documents", "metadatas"],
            )

            if result["ids"]:
                return {
                    "id": result["ids"][0],
                    "document": result["documents"][0],
                    "metadata": result["metadatas"][0],
                }

            return None

        except Exception as e:
            logger.error(f"Error getting candidate: {e}")
            return None

    def reset(self) -> None:
        """Reset all collections (for testing)."""
        self.client.reset()
        logger.warning("ChromaDB collections reset")

