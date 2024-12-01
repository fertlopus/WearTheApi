from abc import ABC, abstractmethod
from typing import Dict, Any


class LLMHandler(ABC):
    """Base abstract class for the LLM handlers"""
    @abstractmethod
    async def generate_recommendations(self, context: Dict[str, Any], weather_context: Dict[str, Any]) -> str:
        """Generate recommendations using LLM"""
        pass
