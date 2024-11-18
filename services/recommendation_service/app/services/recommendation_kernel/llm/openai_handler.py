from typing import Dict, Any
import openai
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains.llm import LLMChain

from base import LLMHandler
from prompt_templates import STYLIST_PROMPT_TEMPLATE
from ....core.exceptions import LLMException


class OpenAIHandler(LLMHandler):
    def __init__(self, api_key: str):
        self.llm = OpenAI(
            temperature=0.3,
            openai_api_key=api_key
        )
        self.prompt = PromptTemplate(
            input_variables=["weather", "assets", "style_preferences"],
            template=STYLIST_PROMPT_TEMPLATE
        )
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)

    async def generate_recommendations(self, context: Dict[str, Any], weather_context: Dict[str, Any],
                                       temperature: float = 0.3) -> str:
        try:
            response = await self.chain.arun(
                weather=weather_context,
                assets=context["assets"],
                style_preferences=context["style_preferences"]
            )
            return response
        except Exception as e:
            raise LLMException(f"Failed to generate response recommendations: {str(e)}")
