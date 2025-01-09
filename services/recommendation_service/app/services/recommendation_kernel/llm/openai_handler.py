from typing import Dict, Any, Optional
import openai
import json
import re
from .base import LLMHandler
from .prompt_templates import STYLIST_PROMPT_TEMPLATE, SYSTEM_ROLE
from ....core.exceptions import LLMException
import logging

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,  # Set the logging level
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()  # Log to the console
    ]
)

class OpenAIHandler(LLMHandler):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", temperature: float = 0.3,
                 api_version: Optional[str]=None):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        openai.api_key = self.api_key

    async def generate_recommendations(self, context: Dict[str, Any], weather_context: Dict[str, Any]) -> str:
        try:
            # Prepare the prompt
            prompt = STYLIST_PROMPT_TEMPLATE.format(
                weather=context.get("weather", ""),
                assets=context.get("assets", ""),
                style_preferences=", ".join(context.get("style_preferences", []))
            )

            # Call the OpenAI API
            response = await self._call_openai_api(prompt)

            # Extract the assistant's reply
            recommendation_text = response.choices[0].message.content
            recommendation_json = self._parse_json_from_text(recommendation_text)

            logger.info(f"Response from generate_recommendations method: {recommendation_json}")
            return recommendation_json

        except Exception as e:
            logger.error(f"Method generate_recommendations failed due to the following error: {str(e)}")
            raise LLMException(f"Failed to generate recommendations: {str(e)}")

    async def _call_openai_api(self, prompt: str):
        import asyncio
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, self._sync_openai_call, prompt)
        return response

    def _sync_openai_call(self, prompt: str):
        response = openai.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_ROLE},
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature,
            max_tokens=600,
            n=1,
            stop=None
        )
        return response

    def _parse_json_from_text(self, text: str) -> Any:
        # Remove any leading/trailing whitespace
        text = text.strip()

        # Remove any code block markers or triple backticks
        if text.startswith("```") and text.endswith("```"):
            text = text[3:-3].strip()
        elif text.startswith("```json") and text.endswith("```"):
            text = text[7:-3].strip()

        try:
            return json.loads(text)

        except json.JSONDecodeError as e:
            # Handle parsing errors optionally, fix common issues like trailing commas
            text = self._fix_json(text)
            try:
                return json.loads(text)
            except json.JSONDecodeError as e2:
                raise LLMException(f"Failed to parse the assistant's reply into JSON: {str(e2)}")

    def _fix_json(self, text: str) -> str:
        # Remove comments and trailing commas
        text = re.sub(r'//.*', '', text)  # Remove // comments
        text = re.sub(r'#.*', '', text)   # Remove # comments
        text = re.sub(r',\s*}', '}', text)  # Remove trailing commas before }
        text = re.sub(r',\s*\]', ']', text)  # Remove trailing commas before ]
        return text
