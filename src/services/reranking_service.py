"""Advanced reranking service using PyTorch models."""

import logging
from typing import Dict, List

import torch
from sentence_transformers import CrossEncoder, SentenceTransformer, util

logger = logging.getLogger(__name__)


class RerankingService:
    """
    Advanced reranking service using PyTorch-based models.
    
    Provides:
    1. Cross-Encoder reranking for precise candidate-vacancy matching
    2. Semantic skill similarity using embeddings
    """

    def __init__(self):
        """Initialize reranking models."""
        try:
            # Cross-Encoder для точной оценки пар (вакансия, кандидат)
            # Эта модель обучена специально для задач reranking
            self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            
            # Модель для эмбеддингов навыков
            self.skill_encoder = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Кэш для эмбеддингов навыков (чтобы не пересчитывать)
            self.skill_embeddings_cache = {}
            
            logger.info("Reranking service initialized with PyTorch models")
            logger.info(f"Using device: {self.cross_encoder.device}")
            
        except Exception as e:
            logger.error(f"Error initializing reranking service: {e}")
            raise

    def rerank_candidates(
        self,
        vacancy_text: str,
        candidates: List[Dict],
        top_k: int = 10
    ) -> List[Dict]:
        """
        Rerank candidates using Cross-Encoder for precise scoring.
        
        Cross-Encoder анализирует пару (вакансия, кандидат) целиком,
        что дает более точную оценку чем просто cosine similarity.
        
        Args:
            vacancy_text: Text representation of vacancy
            candidates: List of candidate dictionaries
            top_k: Number of top candidates to rerank
            
        Returns:
            Reranked candidates with added 'rerank_score'
        """
        if not candidates:
            return []
        
        # Берем топ-N кандидатов для реранкинга (чтобы не было слишком медленно)
        candidates_to_rerank = candidates[:top_k]
        
        # Подготавливаем пары (вакансия, кандидат) для Cross-Encoder
        pairs = []
        for candidate in candidates_to_rerank:
            candidate_text = candidate.get('document', '')
            pairs.append([vacancy_text, candidate_text])
        
        # Получаем точные scores от Cross-Encoder
        # Это займет больше времени чем bi-encoder, но даст лучшие результаты
        try:
            rerank_scores = self.cross_encoder.predict(pairs)
            
            # Нормализуем scores в диапазон 0-1
            rerank_scores = torch.sigmoid(torch.tensor(rerank_scores)).numpy()
            
            # Добавляем rerank_score к кандидатам
            for i, candidate in enumerate(candidates_to_rerank):
                candidate['rerank_score'] = float(rerank_scores[i])
                
                # Пересчитываем комбинированный score с учетом реранкинга
                original_score = candidate.get('score', 0)
                # 40% original vector score + 60% rerank score
                candidate['score'] = original_score * 0.4 + candidate['rerank_score'] * 0.6
            
            # Сортируем по новому score
            candidates_to_rerank.sort(key=lambda x: x['score'], reverse=True)
            
            logger.info(f"Reranked {len(candidates_to_rerank)} candidates using Cross-Encoder")
            
            return candidates_to_rerank
            
        except Exception as e:
            logger.error(f"Error during reranking: {e}")
            # Если ошибка, возвращаем кандидатов без реранкинга
            return candidates_to_rerank

    def calculate_semantic_skill_match(
        self,
        candidate_skills: List[str],
        required_skills: List[str],
        threshold: float = 0.7
    ) -> Dict[str, float]:
        """
        Calculate semantic skill matching using embeddings.
        
        Вместо точного совпадения строк, используем семантическую близость:
        - "Python" близко к "Python3", "python"
        - "Django" близко к "Django REST Framework", "DRF"
        - "PostgreSQL" близко к "Postgres", "psql"
        
        Args:
            candidate_skills: List of candidate's skills
            required_skills: List of required skills
            threshold: Minimum similarity threshold (0.0-1.0)
            
        Returns:
            Dictionary with match_score and matched_skills details
        """
        if not required_skills:
            return {
                "match_score": 1.0,
                "matched_skills": [],
                "unmatched_skills": [],
                "semantic_matches": []
            }
        
        if not candidate_skills:
            return {
                "match_score": 0.0,
                "matched_skills": [],
                "unmatched_skills": required_skills,
                "semantic_matches": []
            }
        
        # Получаем эмбеддинги для навыков (с кэшированием)
        candidate_embeddings = self._get_skill_embeddings(candidate_skills)
        required_embeddings = self._get_skill_embeddings(required_skills)
        
        # Вычисляем cosine similarity между всеми парами навыков
        similarity_matrix = util.cos_sim(required_embeddings, candidate_embeddings)
        
        matched_skills = []
        unmatched_skills = []
        semantic_matches = []
        
        # Для каждого требуемого навыка ищем лучшее совпадение
        for i, required_skill in enumerate(required_skills):
            # Находим максимальную similarity для этого навыка
            max_similarity = float(similarity_matrix[i].max())
            best_match_idx = int(similarity_matrix[i].argmax())
            best_match_skill = candidate_skills[best_match_idx]
            
            if max_similarity >= threshold:
                matched_skills.append(required_skill)
                semantic_matches.append({
                    "required": required_skill,
                    "matched": best_match_skill,
                    "similarity": max_similarity
                })
            else:
                unmatched_skills.append(required_skill)
        
        # Рассчитываем итоговый score
        match_score = len(matched_skills) / len(required_skills)
        
        logger.debug(
            f"Semantic skill matching: {len(matched_skills)}/{len(required_skills)} "
            f"matched (score: {match_score:.2f})"
        )
        
        return {
            "match_score": match_score,
            "matched_skills": matched_skills,
            "unmatched_skills": unmatched_skills,
            "semantic_matches": semantic_matches
        }

    def _get_skill_embeddings(self, skills: List[str]) -> torch.Tensor:
        """
        Get embeddings for skills with caching.
        
        Args:
            skills: List of skill names
            
        Returns:
            Tensor of embeddings
        """
        embeddings = []
        skills_to_encode = []
        skills_indices = []
        
        # Проверяем кэш
        for i, skill in enumerate(skills):
            skill_lower = skill.lower().strip()
            if skill_lower in self.skill_embeddings_cache:
                embeddings.append(self.skill_embeddings_cache[skill_lower])
            else:
                skills_to_encode.append(skill)
                skills_indices.append(i)
        
        # Кодируем новые навыки
        if skills_to_encode:
            new_embeddings = self.skill_encoder.encode(
                skills_to_encode,
                convert_to_tensor=True,
                show_progress_bar=False
            )
            
            # Сохраняем в кэш
            for skill, embedding in zip(skills_to_encode, new_embeddings):
                skill_lower = skill.lower().strip()
                self.skill_embeddings_cache[skill_lower] = embedding
                embeddings.insert(skills_indices[0] if skills_indices else 0, embedding)
                if skills_indices:
                    skills_indices.pop(0)
        
        # Если все было в кэше
        if not embeddings and not skills_to_encode:
            return torch.stack(list(self.skill_embeddings_cache.values())[:len(skills)])
        
        # Получаем все эмбеддинги в правильном порядке
        final_embeddings = []
        for skill in skills:
            skill_lower = skill.lower().strip()
            final_embeddings.append(self.skill_embeddings_cache[skill_lower])
        
        return torch.stack(final_embeddings)

    def clear_cache(self):
        """Clear skill embeddings cache."""
        self.skill_embeddings_cache.clear()
        logger.info("Skill embeddings cache cleared")

