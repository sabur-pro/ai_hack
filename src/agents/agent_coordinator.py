"""Agent coordinator for selecting and managing specialized agents."""

import asyncio
import logging
from typing import Dict, List, Optional

from src.agents.base_agent import AgentResult, BaseAgent
from src.agents.specialized_agents import (
    AchievementVerifierAgent,
    ArchitectureAgent,
    CommunicationAgent,
    DatabaseAgent,
    DevOpsAgent,
    GitHubAnalystAgent,
    PythonExpertAgent,
    SecurityExpertAgent,
    SoftSkillsAgent,
    TestResultsAgent,
)
from src.core.domain.models import Candidate, Vacancy

logger = logging.getLogger(__name__)


class AgentCoordinator:
    """Coordinates multiple specialized agents for candidate analysis."""

    def __init__(self, gemini_client):
        """
        Initialize coordinator with all available agents.

        Args:
            gemini_client: Gemini API client
        """
        self.gemini = gemini_client

        self.all_agents: List[BaseAgent] = [
            DevOpsAgent(gemini_client),
            DatabaseAgent(gemini_client),
            PythonExpertAgent(gemini_client),
            GitHubAnalystAgent(gemini_client),
            TestResultsAgent(gemini_client),
            AchievementVerifierAgent(gemini_client),
            SoftSkillsAgent(gemini_client),
            SecurityExpertAgent(gemini_client),
            ArchitectureAgent(gemini_client),
            CommunicationAgent(gemini_client),
        ]

        logger.info(f"Agent Coordinator initialized with {len(self.all_agents)} agents")

    async def select_agents_for_vacancy(self, vacancy: Vacancy) -> List[BaseAgent]:
        """
        Select relevant agents for a vacancy using AI.

        Args:
            vacancy: Vacancy to analyze

        Returns:
            List of relevant agents
        """
        agent_descriptions = "\n".join(
            [
                f"- {agent.get_name()}: {agent.get_description()}"
                for agent in self.all_agents
            ]
        )

        prompt = f"""Ты HR AI координатор. Выбери подходящих агентов для анализа кандидатов на вакансию.

ВАКАНСИЯ:
Название: {vacancy.title}
Описание: {vacancy.description}
Требования: {', '.join(vacancy.requirements)}
Навыки: {', '.join(vacancy.skills)}
Опыт: {vacancy.experience_years} лет

ДОСТУПНЫЕ АГЕНТЫ:
{agent_descriptions}

Выбери 5-8 наиболее релевантных агентов. Ответь списком названий через запятую:
"""

        try:
            response = await self.gemini.generate_response(prompt, temperature=0.3)
            logger.info(f"AI selected agents: {response}")

            selected_names = [name.strip() for name in response.split(",")]

            rule_based_agents = [
                agent
                for agent in self.all_agents
                if agent.is_relevant_for_vacancy(vacancy)
            ]

            selected_agents = rule_based_agents

            logger.info(
                f"Selected {len(selected_agents)} agents for vacancy '{vacancy.title}'"
            )
            for agent in selected_agents:
                logger.info(f"  - {agent.get_name()}: {agent.get_description()}")

            return selected_agents

        except Exception as e:
            logger.error(f"Error selecting agents with AI: {e}")
            return [
                agent
                for agent in self.all_agents
                if agent.is_relevant_for_vacancy(vacancy)
            ]

    async def analyze_candidate(
        self,
        candidate: Candidate,
        vacancy: Vacancy,
        agents: Optional[List[BaseAgent]] = None,
        context: Optional[Dict] = None,
        sequential: bool = True,  
    ) -> Dict:
        """
        Analyze candidate using multiple specialized agents.

        Args:
            candidate: Candidate to analyze
            vacancy: Vacancy requirements
            agents: List of agents to use (if None, will select automatically)
            context: Additional context (GitHub info, test results, etc.)
            sequential: If True, run agents sequentially with delays (safer for API limits)

        Returns:
            Analysis results from all agents + aggregated score
        """
        if agents is None:
            agents = await self.select_agents_for_vacancy(vacancy)
            if sequential and agents:
                logger.info("Waiting 5s after agent selection...")
                await asyncio.sleep(10)

        if not agents:
            logger.warning("No agents selected for analysis")
            return {
                "agent_results": [],
                "overall_score": 0.0,
                "summary": "Нет подходящих агентов для анализа",
            }

        logger.info(f"Running {len(agents)} agents for candidate {candidate.name} ({'sequential' if sequential else 'parallel'})")

        agent_results: List[AgentResult] = []

        if sequential:
            for i, agent in enumerate(agents):
                try:
                    logger.info(f"Running agent {i+1}/{len(agents)}: {agent.get_name()}")
                    result = await agent.analyze(candidate, vacancy, context or {})
                    agent_results.append(result)
                    

                    if i < len(agents) - 1:  
                        logger.info(f"Waiting 5s before next agent...")
                        await asyncio.sleep(10)
                        
                except Exception as e:
                    logger.error(f"Agent {agent.get_name()} error: {e}")
                    continue
        else:
            tasks = [
                agent.analyze(candidate, vacancy, context or {}) for agent in agents
            ]

            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)

                valid_results = [
                    result
                    for result in results
                    if isinstance(result, AgentResult)
                ]

                errors = [
                    result for result in results if isinstance(result, Exception)
                ]
                for error in errors:
                    logger.error(f"Agent analysis error: {error}")

                agent_results = valid_results

            except Exception as e:
                logger.error(f"Error running agents: {e}")

        if not agent_results:
            return {
                "agent_results": [],
                "overall_score": 0.0,
                "summary": "Ошибка анализа агентами",
            }

        # Calculate weighted overall score
        total_weight = sum(result.confidence for result in agent_results)
        if total_weight > 0:
            overall_score = sum(
                result.score * result.confidence for result in agent_results
            ) / total_weight
        else:
            overall_score = sum(result.score for result in agent_results) / len(
                agent_results
            )

        if sequential:
            logger.info("Waiting 5s before generating summary...")
            await asyncio.sleep(10)
        
        summary = await self._generate_summary(agent_results, candidate, vacancy)

        logger.info(
            f"Analysis complete: {len(agent_results)} agents, overall score: {overall_score:.2f}"
        )

        return {
            "agent_results": agent_results,
            "overall_score": overall_score,
            "summary": summary,
            "total_agents": len(agent_results),
        }

    async def _generate_summary(
        self,
        agent_results: List[AgentResult],
        candidate: Candidate,
        vacancy: Vacancy,
    ) -> str:
        """Generate overall summary from agent results."""
        agents_summary = "\n\n".join(
            [
                f"{result.agent_name} (score: {result.score:.2f}):\n{result.findings}"
                for result in agent_results
            ]
        )

        prompt = f"""На основе анализа специализированных агентов, создай краткое резюме о кандидате.

ВАКАНСИЯ: {vacancy.title}

КАНДИДАТ: {candidate.name}

РЕЗУЛЬТАТЫ АГЕНТОВ:
{agents_summary}

Создай краткое (3-4 предложения) общее резюме, выделив ключевые моменты.
"""

        try:
            summary = await self.gemini.generate_response(prompt, temperature=0.5)
            return summary
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return "Анализ завершен. Смотрите детали по каждому агенту."

