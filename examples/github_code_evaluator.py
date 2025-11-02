"""
Модуль для оценки кода кандидата по GitHub репозиторию.
Парсит GitHub ссылку из резюме и анализирует код с помощью Gemini AI.
"""

import asyncio
import re
import random
import logging
import sys
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass
import requests

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.ai.gemini_client import GeminiClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CodeEvaluation:
    """Результат оценки кода."""
    overall_score: float
    architecture_score: float
    code_quality_score: float
    best_practices_score: float
    documentation_score: float
    complexity_score: float
    summary: str
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]


class GitHubParser:
    """Парсер для извлечения GitHub ссылок из текста."""
    
    GITHUB_PATTERNS = [
        r'https?://github\.com/[\w-]+/[\w.-]+',
        r'github\.com/[\w-]+/[\w.-]+',
        r'www\.github\.com/[\w-]+/[\w.-]+',
    ]
    
    @staticmethod
    def extract_github_url(text: str) -> Optional[str]:
        """Извлекает GitHub URL из текста."""
        for pattern in GitHubParser.GITHUB_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                url = match.group(0)
                if not url.startswith('http'):
                    url = 'https://' + url
                # Убираем возможные trailing символы
                url = re.sub(r'[.,;)]+$', '', url)
                return url
        return None
    
    @staticmethod
    def parse_github_url(url: str) -> tuple[Optional[str], Optional[str]]:
        """
        Парсит GitHub URL и извлекает owner и repo.
        Возвращает (owner, repo) или (None, None).
        """
        match = re.search(r'github\.com/([^/]+)/([^/]+)', url)
        if match:
            owner = match.group(1)
            repo = match.group(2).rstrip('/')
            # Убираем расширения типа .git
            repo = re.sub(r'\.git$', '', repo)
            return owner, repo
        return None, None


class GitHubCodeFetcher:
    """Получает код из GitHub репозитория."""
    
    def __init__(self, github_token: Optional[str] = None):
        """
        Инициализация с опциональным GitHub токеном.
        Токен увеличивает rate limit API.
        """
        self.github_token = github_token
        self.base_url = "https://api.github.com"
        self.headers = {}
        if github_token:
            self.headers['Authorization'] = f'token {github_token}'
    
    def get_repository_tree(self, owner: str, repo: str) -> Optional[List[Dict]]:
        """Получает дерево файлов репозитория."""
        url = f"{self.base_url}/repos/{owner}/{repo}/git/trees/main?recursive=1"
        
        try:
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 404:
                url = f"{self.base_url}/repos/{owner}/{repo}/git/trees/master?recursive=1"
                response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return response.json().get('tree', [])
            elif response.status_code == 403:
                # Rate limit exceeded
                logger.error("="*80)
                logger.error("⚠️  ДОСТИГНУТ ЛИМИТ ЗАПРОСОВ К GITHUB API")
                logger.error("="*80)
                
                if 'X-RateLimit-Remaining' in response.headers:
                    remaining = response.headers['X-RateLimit-Remaining']
                    reset_time = response.headers.get('X-RateLimit-Reset', 'unknown')
                    logger.error(f"Осталось запросов: {remaining}")
                    if reset_time != 'unknown':
                        from datetime import datetime
                        reset_dt = datetime.fromtimestamp(int(reset_time))
                        logger.error(f"Лимит сбросится: {reset_dt.strftime('%H:%M:%S')}")
                
                return None
            else:
                logger.error(f"Ошибка получения дерева репозитория: {response.status_code}")
                if response.text:
                    logger.error(f"Детали: {response.text[:200]}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при запросе к GitHub API: {e}")
            return None
    
    def get_file_content(self, owner: str, repo: str, path: str) -> Optional[str]:
        """Получает содержимое файла."""
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                import base64
                content = response.json().get('content', '')
                decoded = base64.b64decode(content).decode('utf-8')
                return decoded
            else:
                logger.warning(f"Не удалось получить файл {path}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при получении файла {path}: {e}")
            return None
    
    def select_random_code_files(
        self, 
        tree: List[Dict], 
        count: int = 5,
        extensions: List[str] = None
    ) -> List[Dict]:
        """
        Выбирает случайные файлы кода для анализа.
        
        Args:
            tree: Дерево файлов репозитория
            count: Количество файлов для выбора
            extensions: Расширения файлов (по умолчанию популярные языки)
        """
        if extensions is None:
            extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs', '.rb', '.php']
        
        code_files = [
            item for item in tree 
            if item['type'] == 'blob' and any(item['path'].endswith(ext) for ext in extensions)
        ]
        
        excluded_dirs = ['node_modules', 'venv', 'dist', 'build', '__pycache__', 'vendor']
        code_files = [
            f for f in code_files 
            if not any(excluded in f['path'] for excluded in excluded_dirs)
        ]
        
        selected_count = min(count, len(code_files))
        return random.sample(code_files, selected_count) if code_files else []


class CodeEvaluator:
    """Оценивает код с помощью Gemini AI."""
    
    def __init__(self):
        self.gemini_client = GeminiClient()
    
    async def evaluate_code_files(
        self, 
        code_samples: List[Dict[str, str]],
        repo_info: str
    ) -> CodeEvaluation:
        """
        Оценивает код на основе нескольких файлов.
        
        Args:
            code_samples: Список словарей с 'path' и 'content'
            repo_info: Информация о репозитории
        """
        prompt = self._build_evaluation_prompt(code_samples, repo_info)
        
        try:
            response = await self.gemini_client.generate_response(
                prompt, 
                temperature=0.3,
                max_tokens=2000
            )
            return self._parse_evaluation_response(response)
            
        except Exception as e:
            logger.error(f"Ошибка при оценке кода: {e}")
            raise
    
    def _build_evaluation_prompt(
        self, 
        code_samples: List[Dict[str, str]],
        repo_info: str
    ) -> str:
        """Строит промпт для оценки кода."""
        
        prompt = f"""Ты опытный senior разработчик и code reviewer. 
Оцени качество кода кандидата на основе представленных файлов из его GitHub репозитория.

ИНФОРМАЦИЯ О РЕПОЗИТОРИИ:
{repo_info}

ФАЙЛЫ ДЛЯ АНАЛИЗА:
"""
        
        for i, sample in enumerate(code_samples, 1):
            prompt += f"\n--- Файл {i}: {sample['path']} ---\n"
            prompt += f"{sample['content'][:2000]}\n"  # Ограничиваем размер файла
            if len(sample['content']) > 2000:
                prompt += "[... файл обрезан ...]\n"
        
        prompt += """

ОЦЕНИ КОД ПО СЛЕДУЮЩИМ МЕТРИКАМ (от 0 до 10):

1. АРХИТЕКТУРА (Architecture):
   - Структура проекта
   - Разделение ответственности
   - Паттерны проектирования
   - Масштабируемость

2. КАЧЕСТВО КОДА (Code Quality):
   - Читаемость
   - Именование переменных/функций
   - Избыточность кода (DRY)
   - Сложность функций

3. BEST PRACTICES:
   - Следование стандартам языка
   - Обработка ошибок
   - Безопасность
   - Производительность

4. ДОКУМЕНТАЦИЯ:
   - Комментарии
   - Docstrings/JSDoc
   - README (если виден)
   - Понятность кода без комментариев

5. СЛОЖНОСТЬ (Complexity):
   - Управление сложностью
   - Модульность
   - Тестируемость
   - Зависимости

ФОРМАТ ОТВЕТА (СТРОГО ПРИДЕРЖИВАЙСЯ ЭТОГО ФОРМАТА):

ARCHITECTURE_SCORE: [число от 0 до 10]
CODE_QUALITY_SCORE: [число от 0 до 10]
BEST_PRACTICES_SCORE: [число от 0 до 10]
DOCUMENTATION_SCORE: [число от 0 до 10]
COMPLEXITY_SCORE: [число от 0 до 10]
OVERALL_SCORE: [средняя оценка от 0 до 10]

SUMMARY: [краткое резюме на 2-3 предложения]

STRENGTHS:
- [сильная сторона 1]
- [сильная сторона 2]
- [сильная сторона 3]

WEAKNESSES:
- [слабая сторона 1]
- [слабая сторона 2]
- [слабая сторона 3]

RECOMMENDATIONS:
- [рекомендация 1]
- [рекомендация 2]
- [рекомендация 3]
"""
        
        return prompt
    
    def _parse_evaluation_response(self, response: str) -> CodeEvaluation:
        """Парсит ответ от Gemini и извлекает оценки."""
        
        scores = {
            'architecture': 0.0,
            'code_quality': 0.0,
            'best_practices': 0.0,
            'documentation': 0.0,
            'complexity': 0.0,
            'overall': 0.0
        }
        
        summary = ""
        strengths = []
        weaknesses = []
        recommendations = []
        
        lines = response.strip().split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            # Парсим оценки
            if 'ARCHITECTURE_SCORE:' in line:
                scores['architecture'] = self._extract_score(line)
            elif 'CODE_QUALITY_SCORE:' in line:
                scores['code_quality'] = self._extract_score(line)
            elif 'BEST_PRACTICES_SCORE:' in line:
                scores['best_practices'] = self._extract_score(line)
            elif 'DOCUMENTATION_SCORE:' in line:
                scores['documentation'] = self._extract_score(line)
            elif 'COMPLEXITY_SCORE:' in line:
                scores['complexity'] = self._extract_score(line)
            elif 'OVERALL_SCORE:' in line:
                scores['overall'] = self._extract_score(line)
            
            # Парсим секции
            elif line == 'SUMMARY:':
                current_section = 'summary'
            elif line == 'STRENGTHS:':
                current_section = 'strengths'
            elif line == 'WEAKNESSES:':
                current_section = 'weaknesses'
            elif line == 'RECOMMENDATIONS:':
                current_section = 'recommendations'
            
            # Добавляем контент в секции
            elif line.startswith('-') or line.startswith('•'):
                item = line.lstrip('-•').strip()
                if current_section == 'strengths':
                    strengths.append(item)
                elif current_section == 'weaknesses':
                    weaknesses.append(item)
                elif current_section == 'recommendations':
                    recommendations.append(item)
            
            elif current_section == 'summary' and line and not line.endswith(':'):
                summary += line + " "
        
        # Если overall не был найден, вычисляем среднее
        if scores['overall'] == 0.0:
            scores['overall'] = sum([
                scores['architecture'],
                scores['code_quality'],
                scores['best_practices'],
                scores['documentation'],
                scores['complexity']
            ]) / 5
        
        return CodeEvaluation(
            overall_score=scores['overall'],
            architecture_score=scores['architecture'],
            code_quality_score=scores['code_quality'],
            best_practices_score=scores['best_practices'],
            documentation_score=scores['documentation'],
            complexity_score=scores['complexity'],
            summary=summary.strip(),
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations
        )
    
    @staticmethod
    def _extract_score(line: str) -> float:
        """Извлекает числовую оценку из строки."""
        try:
            match = re.search(r'(\d+\.?\d*)', line)
            if match:
                score = float(match.group(1))
                # Нормализация к диапазону 0-10
                return min(max(score, 0), 10)
        except (ValueError, AttributeError):
            pass
        return 0.0


class GitHubCodeEvaluationService:
    """Сервис для полной оценки кода кандидата по GitHub."""
    
    def __init__(self, github_token: Optional[str] = None):
        self.parser = GitHubParser()
        self.fetcher = GitHubCodeFetcher(github_token)
        self.evaluator = CodeEvaluator()
    
    async def evaluate_candidate_from_resume(
        self, 
        resume_text: str,
        num_files: int = 5
    ) -> Optional[CodeEvaluation]:
        """
        Оценивает код кандидата, находя GitHub ссылку в резюме.
        
        Args:
            resume_text: Текст резюме кандидата
            num_files: Количество файлов для анализа
        
        Returns:
            CodeEvaluation или None если GitHub не найден
        """
        github_url = self.parser.extract_github_url(resume_text)
        if not github_url:
            logger.warning("GitHub ссылка не найдена в резюме")
            return None
        
        logger.info(f"Найдена GitHub ссылка: {github_url}")
        
        owner, repo = self.parser.parse_github_url(github_url)
        if not owner or not repo:
            logger.error(f"Не удалось распарсить GitHub URL: {github_url}")
            return None
        
        logger.info(f"Репозиторий: {owner}/{repo}")
        
        # 3. Получаем дерево файлов
        tree = self.fetcher.get_repository_tree(owner, repo)
        if not tree:
            logger.error("Не удалось получить дерево репозитория")
            return None
        
        logger.info(f"Получено файлов в репозитории: {len(tree)}")
        
        selected_files = self.fetcher.select_random_code_files(tree, num_files)
        if not selected_files:
            logger.error("Не найдено файлов кода для анализа")
            return None
        
        logger.info(f"Выбрано файлов для анализа: {len(selected_files)}")
        
        # 5. Получаем содержимое файлов
        code_samples = []
        for file_info in selected_files:
            path = file_info['path']
            logger.info(f"Загрузка файла: {path}")
            content = self.fetcher.get_file_content(owner, repo, path)
            if content:
                code_samples.append({
                    'path': path,
                    'content': content
                })
        
        if not code_samples:
            logger.error("Не удалось загрузить ни одного файла")
            return None
        
        logger.info(f"Загружено файлов: {len(code_samples)}")
        
        # 6. Оцениваем код
        repo_info = f"GitHub: {github_url} (Owner: {owner}, Repo: {repo})"
        evaluation = await self.evaluator.evaluate_code_files(code_samples, repo_info)
        
        return evaluation


async def main():
    """Пример использования."""
    
    # Тестовое резюме с GitHub ссылкой
    test_resume = """
    Иван Иванов
    Python Backend Developer
    
    Опыт работы:
    - 3 года разработки на Python
    - Знание Django, FastAPI
    - Работа с PostgreSQL, Redis
    
    Мои проекты:
    - GitHub: https://github.com/fastapi/fastapi
    - Telegram бот для автоматизации
    
    Навыки: Python, Docker, CI/CD, REST API
    """
    
    print("=" * 80)
    print("ТЕСТИРОВАНИЕ МОДУЛЯ ОЦЕНКИ КОДА ИЗ GITHUB")
    print("=" * 80)
    print()
    
    import os
    github_token = os.getenv('GITHUB_TOKEN')
    
    if github_token:
        print(f"✅ Используется GitHub токен: {github_token[:10]}...")
    else:
        print("⚠️  GitHub токен не найден. Лимит: 60 запросов/час")
        print("   Установите: $env:GITHUB_TOKEN='ваш_токен'")
    print()
    
    service = GitHubCodeEvaluationService(github_token=github_token)
    
    print("Анализ резюме...")
    print("-" * 80)
    
    evaluation = await service.evaluate_candidate_from_resume(test_resume, num_files=5)
    
    if evaluation:
        print("\n" + "=" * 80)
        print("РЕЗУЛЬТАТЫ ОЦЕНКИ КОДА")
        print("=" * 80)
        print()
        
        print(f"📊 ОБЩАЯ ОЦЕНКА: {evaluation.overall_score:.1f}/10")
        print()
        
        print("📈 ДЕТАЛЬНЫЕ МЕТРИКИ:")
        print(f"  • Архитектура:      {evaluation.architecture_score:.1f}/10")
        print(f"  • Качество кода:    {evaluation.code_quality_score:.1f}/10")
        print(f"  • Best Practices:   {evaluation.best_practices_score:.1f}/10")
        print(f"  • Документация:     {evaluation.documentation_score:.1f}/10")
        print(f"  • Сложность:        {evaluation.complexity_score:.1f}/10")
        print()
        
        print("📝 РЕЗЮМЕ:")
        print(f"  {evaluation.summary}")
        print()
        
        if evaluation.strengths:
            print("✅ СИЛЬНЫЕ СТОРОНЫ:")
            for strength in evaluation.strengths:
                print(f"  • {strength}")
            print()
        
        if evaluation.weaknesses:
            print("⚠️ СЛАБЫЕ СТОРОНЫ:")
            for weakness in evaluation.weaknesses:
                print(f"  • {weakness}")
            print()
        
        if evaluation.recommendations:
            print("💡 РЕКОМЕНДАЦИИ:")
            for recommendation in evaluation.recommendations:
                print(f"  • {recommendation}")
        
        print()
        print("=" * 80)
    else:
        print("\n❌ Не удалось оценить код кандидата")


if __name__ == "__main__":
    asyncio.run(main())

