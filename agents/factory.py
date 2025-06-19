from typing import Dict, Type
from .base import BaseAgent
from .specialized.strategist import StrategistAgent
from .specialized.code_generator import CodeGeneratorAgent
from .specialized.test_generator import TestGeneratorAgent
from .specialized.build import BuildAgent

class AgentFactory:
    _agent_types: Dict[str, Type[BaseAgent]] = {
        "strategist": StrategistAgent,
        "code_generator": CodeGeneratorAgent,
        "test_generator": TestGeneratorAgent,
        "build": BuildAgent
    }

    @classmethod
    def create_agent(cls, agent_type: str, config, message_bus, resource_manager) -> BaseAgent:
        if agent_type not in cls._agent_types:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        agent_class = cls._agent_types[agent_type]
        return agent_class(config, message_bus, resource_manager)

    @classmethod
    def register_agent_type(cls, name: str, agent_class: Type[BaseAgent]):
        cls._agent_types[name] = agent_class

    @classmethod
    def list_agent_types(cls) -> list:
        return list(cls._agent_types.keys())

# agents/specialized/strategist.py
import json
from typing import Dict, Any
from ..base import BaseAgent
from ...core.models import Capability

class StrategistAgent(BaseAgent):
    async def initialize(self):
        await self.add_capability(Capability(
            name="plan_project",
            handler=self._plan_project
        ))
        
        await self.add_capability(Capability(
            name="analyze_requirements",
            handler=self._analyze_requirements
        ))

    async def _plan_project(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        requirements = payload.get("requirements", "")
        
        plan = {
            "phases": [
                {"name": "Analysis", "duration": "1-2 days", "tasks": ["Requirements analysis", "Tech stack selection"]},
                {"name": "Design", "duration": "2-3 days", "tasks": ["Architecture design", "API design"]},
                {"name": "Development", "duration": "5-10 days", "tasks": ["Core implementation", "Testing"]},
                {"name": "Deployment", "duration": "1-2 days", "tasks": ["CI/CD setup", "Production deployment"]}
            ],
            "resources": ["2-3 developers", "1 architect", "1 tester"],
            "technologies": self._suggest_technologies(requirements)
        }
        
        return plan

    async def _analyze_requirements(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        text = payload.get("text", "")
        
        analysis = {
            "functional_requirements": self._extract_functional_requirements(text),
            "non_functional_requirements": self._extract_non_functional_requirements(text),
            "constraints": self._extract_constraints(text),
            "risks": self._identify_risks(text)
        }
        
        return analysis

    def _suggest_technologies(self, requirements: str) -> Dict[str, list]:
        tech_map = {
            "web": ["React", "FastAPI", "PostgreSQL"],
            "api": ["FastAPI", "SQLAlchemy", "Redis"],
            "data": ["Python", "Pandas", "PostgreSQL"],
            "mobile": ["React Native", "Expo", "Firebase"]
        }
        
        suggested = []
        requirements_lower = requirements.lower()
        
        for key, techs in tech_map.items():
            if key in requirements_lower:
                suggested.extend(techs)
        
        return {"recommended": list(set(suggested)) or ["Python", "FastAPI", "PostgreSQL"]}

    def _extract_functional_requirements(self, text: str) -> list:
        return ["User authentication", "Data processing", "API endpoints"]

    def _extract_non_functional_requirements(self, text: str) -> list:
        return ["Performance", "Security", "Scalability"]

    def _extract_constraints(self, text: str) -> list:
        return ["Budget limitations", "Time constraints", "Technology restrictions"]

    def _identify_risks(self, text: str) -> list:
        return ["Technical complexity", "Resource availability", "Timeline pressure"]