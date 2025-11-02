"""Specialized agents for different aspects of candidate analysis."""

import logging
from typing import Dict, Optional

from src.agents.base_agent import AgentResult, BaseAgent
from src.core.domain.models import Candidate, Vacancy

logger = logging.getLogger(__name__)


class DevOpsAgent(BaseAgent):
    """Agent specialized in DevOps skills analysis."""

    def get_name(self) -> str:
        return "DevOps эксперт"

    def get_description(self) -> str:
        return "Анализирует DevOps навыки: Docker, Kubernetes, CI/CD, облачные платформы"

    def is_relevant_for_vacancy(self, vacancy: Vacancy) -> bool:
        devops_keywords = [
            "docker",
            "kubernetes",
            "ci/cd",
            "devops",
            "aws",
            "azure",
            "gcp",
            "jenkins",
            "gitlab",
            "terraform",
        ]
        text = (vacancy.description + " ".join(vacancy.skills)).lower()
        return any(keyword in text for keyword in devops_keywords)

    async def analyze(
        self, candidate: Candidate, vacancy: Vacancy, context: Optional[Dict] = None
    ) -> AgentResult:
        prompt = f"""Ты эксперт DevOps. Оцени кандидата по DevOps навыкам.

ВАКАНСИЯ требует:
{vacancy.description}
Навыки: {', '.join(vacancy.skills)}

КАНДИДАТ:
{candidate.summary}
Навыки: {', '.join(candidate.skills)}
Опыт: {' | '.join(candidate.experience)}

Оцени ТОЛЬКО DevOps навыки: Docker, Kubernetes, CI/CD, облачные платформы, автоматизация.

Формат ответа:
SCORE: [0.0-1.0]
CONFIDENCE: [0.0-1.0]
FINDINGS: [твои выводы]
STRENGTHS: [сильная сторона 1 | сильная сторона 2]
WEAKNESSES: [слабость 1 | слабость 2]
RECOMMENDATIONS: [рекомендация 1 | рекомендация 2]
"""

        response = await self._get_ai_analysis(prompt)
        parsed = self._parse_agent_response(response)

        return AgentResult(
            agent_name=self.get_name(),
            agent_type=self.agent_type,
            score=parsed["score"],
            confidence=parsed["confidence"],
            findings=parsed["findings"],
            strengths=parsed["strengths"],
            weaknesses=parsed["weaknesses"],
            recommendations=parsed["recommendations"],
        )


class DatabaseAgent(BaseAgent):
    """Agent specialized in database and SQL skills."""

    def get_name(self) -> str:
        return "Database эксперт"

    def get_description(self) -> str:
        return "Анализирует навыки работы с базами данных: SQL, PostgreSQL, MongoDB, оптимизация запросов"

    def is_relevant_for_vacancy(self, vacancy: Vacancy) -> bool:
        db_keywords = [
            "sql",
            "database",
            "postgresql",
            "mysql",
            "mongodb",
            "redis",
            "orm",
            "sqlalchemy",
            "база данных",
        ]
        text = (vacancy.description + " ".join(vacancy.skills)).lower()
        return any(keyword in text for keyword in db_keywords)

    async def analyze(
        self, candidate: Candidate, vacancy: Vacancy, context: Optional[Dict] = None
    ) -> AgentResult:
        prompt = f"""Ты эксперт по базам данных. Оцени навыки работы с БД у кандидата.

ВАКАНСИЯ требует:
{vacancy.description}
Навыки: {', '.join(vacancy.skills)}

КАНДИДАТ:
{candidate.summary}
Навыки: {', '.join(candidate.skills)}
Опыт: {' | '.join(candidate.experience)}

Оцени ТОЛЬКО навыки работы с базами данных: SQL, PostgreSQL, MySQL, MongoDB, Redis, оптимизация запросов, индексы, транзакции.

Формат ответа:
SCORE: [0.0-1.0]
CONFIDENCE: [0.0-1.0]
FINDINGS: [твои выводы]
STRENGTHS: [сильная сторона 1 | сильная сторона 2]
WEAKNESSES: [слабость 1 | слабость 2]
RECOMMENDATIONS: [рекомендация 1 | рекомендация 2]
"""

        response = await self._get_ai_analysis(prompt)
        parsed = self._parse_agent_response(response)

        return AgentResult(
            agent_name=self.get_name(),
            agent_type=self.agent_type,
            score=parsed["score"],
            confidence=parsed["confidence"],
            findings=parsed["findings"],
            strengths=parsed["strengths"],
            weaknesses=parsed["weaknesses"],
            recommendations=parsed["recommendations"],
        )


class PythonExpertAgent(BaseAgent):
    """Agent specialized in Python expertise."""

    def get_name(self) -> str:
        return "Python эксперт"

    def get_description(self) -> str:
        return "Анализирует Python навыки: язык, фреймворки, библиотеки, best practices"

    def is_relevant_for_vacancy(self, vacancy: Vacancy) -> bool:
        return "python" in (vacancy.description + " ".join(vacancy.skills)).lower()

    async def analyze(
        self, candidate: Candidate, vacancy: Vacancy, context: Optional[Dict] = None
    ) -> AgentResult:
        prompt = f"""Ты эксперт Python разработки. Оцени глубину знаний Python у кандидата.

ВАКАНСИЯ требует:
{vacancy.description}
Навыки: {', '.join(vacancy.skills)}
Опыт: {vacancy.experience_years} лет

КАНДИДАТ:
{candidate.summary}
Навыки: {', '.join(candidate.skills)}
Опыт: {' | '.join(candidate.experience)}
Лет опыта: {candidate.experience_years}

Оцени ТОЛЬКО Python: знание языка, фреймворки (Django, Flask, FastAPI), библиотеки, async/await, OOP, best practices, тестирование.

Формат ответа:
SCORE: [0.0-1.0]
CONFIDENCE: [0.0-1.0]
FINDINGS: [твои выводы]
STRENGTHS: [сильная сторона 1 | сильная сторона 2]
WEAKNESSES: [слабость 1 | слабость 2]
RECOMMENDATIONS: [рекомендация 1 | рекомендация 2]
"""

        response = await self._get_ai_analysis(prompt)
        parsed = self._parse_agent_response(response)

        return AgentResult(
            agent_name=self.get_name(),
            agent_type=self.agent_type,
            score=parsed["score"],
            confidence=parsed["confidence"],
            findings=parsed["findings"],
            strengths=parsed["strengths"],
            weaknesses=parsed["weaknesses"],
            recommendations=parsed["recommendations"],
        )


class GitHubAnalystAgent(BaseAgent):
    """Agent for analyzing GitHub profile and code quality."""

    def get_name(self) -> str:
        return "GitHub аналитик"

    def get_description(self) -> str:
        return "Анализирует GitHub профиль, качество кода, активность, open-source вклад"

    def is_relevant_for_vacancy(self, vacancy: Vacancy) -> bool:
        return vacancy.experience_years and vacancy.experience_years >= 3

    async def analyze(
        self, candidate: Candidate, vacancy: Vacancy, context: Optional[Dict] = None
    ) -> AgentResult:
        github_info = context.get("github_info", "") if context else ""

        prompt = f"""Ты эксперт по анализу GitHub профилей. Оцени активность и качество кода кандидата.

ВАКАНСИЯ: {vacancy.title}
Уровень: {vacancy.experience_years}+ лет

КАНДИДАТ:
{candidate.summary}
Email: {candidate.email}

GITHUB информация:
{github_info if github_info else "Нет данных о GitHub профиле"}

Оцени: качество кода, стиль, документация, тесты, активность, вклад в open-source, популярность проектов.
Если нет данных о GitHub - укажи это как слабость для Senior позиции.

Формат ответа:
SCORE: [0.0-1.0]
CONFIDENCE: [0.0-1.0]
FINDINGS: [твои выводы]
STRENGTHS: [сильная сторона 1 | сильная сторона 2]
WEAKNESSES: [слабость 1 | слабость 2]
RECOMMENDATIONS: [рекомендация 1 | рекомендация 2]
"""

        response = await self._get_ai_analysis(prompt)
        parsed = self._parse_agent_response(response)

        return AgentResult(
            agent_name=self.get_name(),
            agent_type=self.agent_type,
            score=parsed["score"],
            confidence=parsed["confidence"],
            findings=parsed["findings"],
            strengths=parsed["strengths"],
            weaknesses=parsed["weaknesses"],
            recommendations=parsed["recommendations"],
            details={"github_available": bool(github_info)},
        )


class TestResultsAgent(BaseAgent):
    """Agent for analyzing test results."""

    def get_name(self) -> str:
        return "Тестирование"

    def get_description(self) -> str:
        return "Анализирует результаты технических тестов и заданий"

    def is_relevant_for_vacancy(self, vacancy: Vacancy) -> bool:
        return True

    async def analyze(
        self, candidate: Candidate, vacancy: Vacancy, context: Optional[Dict] = None
    ) -> AgentResult:
        test_results = context.get("test_results", "") if context else ""

        prompt = f"""Ты эксперт по оценке технических тестов. Проанализируй результаты кандидата.

ВАКАНСИЯ: {vacancy.title}
Требования: {', '.join(vacancy.skills)}

КАНДИДАТ: {candidate.name}

РЕЗУЛЬТАТЫ ТЕСТОВ:
{test_results if test_results else "Тесты еще не пройдены"}

Оцени: правильность решений, качество кода, подход к проблемам, скорость выполнения.
Если тестов нет - рекомендуй их пройти.

Формат ответа:
SCORE: [0.0-1.0]
CONFIDENCE: [0.0-1.0]
FINDINGS: [твои выводы]
STRENGTHS: [сильная сторона 1 | сильная сторона 2]
WEAKNESSES: [слабость 1 | слабость 2]
RECOMMENDATIONS: [рекомендация 1 | рекомендация 2]
"""

        response = await self._get_ai_analysis(prompt)
        parsed = self._parse_agent_response(response)

        return AgentResult(
            agent_name=self.get_name(),
            agent_type=self.agent_type,
            score=parsed["score"],
            confidence=parsed["confidence"],
            findings=parsed["findings"],
            strengths=parsed["strengths"],
            weaknesses=parsed["weaknesses"],
            recommendations=parsed["recommendations"],
            details={"test_completed": bool(test_results)},
        )


class AchievementVerifierAgent(BaseAgent):
    """Agent for verifying achievements and accomplishments."""

    def get_name(self) -> str:
        return "Верификатор достижений"

    def get_description(self) -> str:
        return "Проверяет заявленные достижения, сертификаты, награды"

    def is_relevant_for_vacancy(self, vacancy: Vacancy) -> bool:
        return True

    async def analyze(
        self, candidate: Candidate, vacancy: Vacancy, context: Optional[Dict] = None
    ) -> AgentResult:
        achievements_info = context.get("achievements", "") if context else ""

        prompt = f"""Ты эксперт по верификации достижений. Проанализируй заявленные достижения кандидата.

КАНДИДАТ: {candidate.name}
Образование: {', '.join(candidate.education)}
Опыт: {' | '.join(candidate.experience)}

ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ:
{achievements_info if achievements_info else "Нет дополнительной информации о достижениях"}

Оцени: реалистичность достижений, соответствие опыту, наличие подтверждений, ценность для вакансии.

Формат ответа:
SCORE: [0.0-1.0]
CONFIDENCE: [0.0-1.0]
FINDINGS: [твои выводы]
STRENGTHS: [сильная сторона 1 | сильная сторона 2]
WEAKNESSES: [слабость 1 | слабость 2]
RECOMMENDATIONS: [рекомендация 1 | рекомендация 2]
"""

        response = await self._get_ai_analysis(prompt)
        parsed = self._parse_agent_response(response)

        return AgentResult(
            agent_name=self.get_name(),
            agent_type=self.agent_type,
            score=parsed["score"],
            confidence=parsed["confidence"],
            findings=parsed["findings"],
            strengths=parsed["strengths"],
            weaknesses=parsed["weaknesses"],
            recommendations=parsed["recommendations"],
        )


class SoftSkillsAgent(BaseAgent):
    """Agent for analyzing soft skills."""

    def get_name(self) -> str:
        return "Soft Skills"

    def get_description(self) -> str:
        return "Анализирует soft skills: коммуникация, работа в команде, лидерство"

    def is_relevant_for_vacancy(self, vacancy: Vacancy) -> bool:
        return True

    async def analyze(
        self, candidate: Candidate, vacancy: Vacancy, context: Optional[Dict] = None
    ) -> AgentResult:
        prompt = f"""Ты эксперт по soft skills. Оцени нетехнические навыки кандидата на основе резюме.

ВАКАНСИЯ: {vacancy.title}
Обязанности: {', '.join(vacancy.responsibilities)}

КАНДИДАТ:
{candidate.summary}
Опыт: {' | '.join(candidate.experience)}

Оцени из резюме: коммуникативные навыки, работу в команде, лидерство, менторство, презентация идей.

Формат ответа:
SCORE: [0.0-1.0]
CONFIDENCE: [0.0-1.0]
FINDINGS: [твои выводы]
STRENGTHS: [сильная сторона 1 | сильная сторона 2]
WEAKNESSES: [слабость 1 | слабость 2]
RECOMMENDATIONS: [рекомендация 1 | рекомендация 2]
"""

        response = await self._get_ai_analysis(prompt)
        parsed = self._parse_agent_response(response)

        return AgentResult(
            agent_name=self.get_name(),
            agent_type=self.agent_type,
            score=parsed["score"],
            confidence=parsed["confidence"],
            findings=parsed["findings"],
            strengths=parsed["strengths"],
            weaknesses=parsed["weaknesses"],
            recommendations=parsed["recommendations"],
        )


class SecurityExpertAgent(BaseAgent):
    """Agent specialized in security knowledge."""

    def get_name(self) -> str:
        return "Security эксперт"

    def get_description(self) -> str:
        return "Анализирует знания безопасности: authentication, authorization, OWASP"

    def is_relevant_for_vacancy(self, vacancy: Vacancy) -> bool:
        security_keywords = [
            "security",
            "безопасность",
            "authentication",
            "authorization",
            "oauth",
            "jwt",
            "encryption",
        ]
        text = (vacancy.description + " ".join(vacancy.skills)).lower()
        return any(keyword in text for keyword in security_keywords)

    async def analyze(
        self, candidate: Candidate, vacancy: Vacancy, context: Optional[Dict] = None
    ) -> AgentResult:
        prompt = f"""Ты эксперт по безопасности. Оцени знания security у кандидата.

ВАКАНСИЯ требует:
{vacancy.description}

КАНДИДАТ:
{candidate.summary}
Навыки: {', '.join(candidate.skills)}

Оцени знания: authentication, authorization, OWASP Top 10, secure coding, encryption, best practices.

Формат ответа:
SCORE: [0.0-1.0]
CONFIDENCE: [0.0-1.0]
FINDINGS: [твои выводы]
STRENGTHS: [сильная сторона 1 | сильная сторона 2]
WEAKNESSES: [слабость 1 | слабость 2]
RECOMMENDATIONS: [рекомендация 1 | рекомендация 2]
"""

        response = await self._get_ai_analysis(prompt)
        parsed = self._parse_agent_response(response)

        return AgentResult(
            agent_name=self.get_name(),
            agent_type=self.agent_type,
            score=parsed["score"],
            confidence=parsed["confidence"],
            findings=parsed["findings"],
            strengths=parsed["strengths"],
            weaknesses=parsed["weaknesses"],
            recommendations=parsed["recommendations"],
        )


class ArchitectureAgent(BaseAgent):
    """Agent specialized in architecture and design patterns."""

    def get_name(self) -> str:
        return "Архитектура"

    def get_description(self) -> str:
        return "Анализирует знания архитектуры: patterns, microservices, system design"

    def is_relevant_for_vacancy(self, vacancy: Vacancy) -> bool:
        # Relevant for senior+ positions
        arch_keywords = ["architect", "архитектур", "design", "microservices"]
        text = (vacancy.title + vacancy.description).lower()
        return (vacancy.experience_years and vacancy.experience_years >= 5) or any(
            keyword in text for keyword in arch_keywords
        )

    async def analyze(
        self, candidate: Candidate, vacancy: Vacancy, context: Optional[Dict] = None
    ) -> AgentResult:
        prompt = f"""Ты эксперт по архитектуре ПО. Оцени архитектурные знания кандидата.

ВАКАНСИЯ: {vacancy.title}
Требует: {vacancy.experience_years}+ лет опыта

КАНДИДАТ:
{candidate.summary}
Опыт: {' | '.join(candidate.experience)}

Оцени: design patterns, SOLID, microservices, scalability, system design, архитектурные решения.

Формат ответа:
SCORE: [0.0-1.0]
CONFIDENCE: [0.0-1.0]
FINDINGS: [твои выводы]
STRENGTHS: [сильная сторона 1 | сильная сторона 2]
WEAKNESSES: [слабость 1 | слабость 2]
RECOMMENDATIONS: [рекомендация 1 | рекомендация 2]
"""

        response = await self._get_ai_analysis(prompt)
        parsed = self._parse_agent_response(response)

        return AgentResult(
            agent_name=self.get_name(),
            agent_type=self.agent_type,
            score=parsed["score"],
            confidence=parsed["confidence"],
            findings=parsed["findings"],
            strengths=parsed["strengths"],
            weaknesses=parsed["weaknesses"],
            recommendations=parsed["recommendations"],
        )


class CommunicationAgent(BaseAgent):
    """Agent for analyzing communication skills from resume."""

    def get_name(self) -> str:
        return "Коммуникация"

    def get_description(self) -> str:
        return "Анализирует коммуникативные навыки по резюме и опыту"

    def is_relevant_for_vacancy(self, vacancy: Vacancy) -> bool:
        return True

    async def analyze(
        self, candidate: Candidate, vacancy: Vacancy, context: Optional[Dict] = None
    ) -> AgentResult:
        prompt = f"""Ты эксперт по оценке коммуникативных навыков. Проанализируй по резюме.

ВАКАНСИЯ: {vacancy.title}
Обязанности: {', '.join(vacancy.responsibilities)}

КАНДИДАТ:
{candidate.summary}
Опыт: {' | '.join(candidate.experience)}

Оцени по тексту: качество изложения, структурированность, опыт презентаций, взаимодействия с командой/клиентами.

Формат ответа:
SCORE: [0.0-1.0]
CONFIDENCE: [0.0-1.0]
FINDINGS: [твои выводы]
STRENGTHS: [сильная сторона 1 | сильная сторона 2]
WEAKNESSES: [слабость 1 | слабость 2]
RECOMMENDATIONS: [рекомендация 1 | рекомендация 2]
"""

        response = await self._get_ai_analysis(prompt)
        parsed = self._parse_agent_response(response)

        return AgentResult(
            agent_name=self.get_name(),
            agent_type=self.agent_type,
            score=parsed["score"],
            confidence=parsed["confidence"],
            findings=parsed["findings"],
            strengths=parsed["strengths"],
            weaknesses=parsed["weaknesses"],
            recommendations=parsed["recommendations"],
        )

