from typing import Dict, Any, Optional
import openai
from openai import AsyncOpenAI
import json
import re
import asyncio
from .base import LLMHandler
from .prompt_templates import STYLIST_PROMPT_TEMPLATE, SYSTEM_ROLE, STYLIST_PROMPT_TEMPLATE_CATEGORIZED
from ....core.exceptions import LLMException
import logging
from tenacity import (retry,
                      stop_after_attempt,
                      wait_exponential,
                      retry_if_exception_type)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    handlers=[logging.StreamHandler()])


class OpenAIHandler(LLMHandler):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", temperature: float = 1.5, max_retries: int = 3,
                 timeout: float = 30.0, api_version: Optional[str]=None):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        self.timeout = timeout
        self.client = AsyncOpenAI(api_key=self.api_key, timeout=timeout)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10),
           retry=retry_if_exception_type((openai.APITimeoutError, openai.APIConnectionError, openai.RateLimitError)))
    async def generate_recommendations(self, context: Dict[str, Any], weather_context: Dict[str, Any]) -> str:
        try:
            # Prepare the prompt
            prompt = STYLIST_PROMPT_TEMPLATE.format(
                weather=context.get("weather", ""),
                assets=context.get("assets", ""),
                style_preferences=", ".join(context.get("style_preferences", []))
            )

            # Call the OpenAI API
            # response = await self._call_openai_api(prompt)
            logger.info(f"Async call of the OpenAI API with defined prompts.")
            response = await self._make_async_completion(prompt)

            # Extract the assistant's reply
            recommendation_text = response.choices[0].message.content
            recommendation_json = self._parse_json_from_text(recommendation_text)

            logger.info(
                f"Response from generate_recommendations method succeeded: {recommendation_json}",
                extra={
                    "response_length": len(recommendation_text),
                    "model": self.model,
                    "context_size": len(str(context))
                }
            )

            return recommendation_json

        except asyncio.TimeoutError as e:
            logger.error(f"OpenAI API call timed out: {str(e)}")
            raise LLMException("Request timed out while generating recommendations")

        except openai.RateLimitError as e:
            logger.error(f"Rate limit exceeded: {str(e)}")
            raise LLMException("Rate limit exceeded, please try again later")

        except openai.APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise LLMException(f"OpenAI API error: {str(e)}")

        except Exception as e:
            logger.error(f"Method generate_recommendations failed due to the following error: {str(e)}")
            raise LLMException(f"Failed to generate recommendations: {str(e)}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10),
           retry=retry_if_exception_type((openai.APITimeoutError, openai.APIConnectionError, openai.RateLimitError)))
    async def generate_categorized_recommendations(self, context: Dict[str, Any], weather_context: Dict[str, Any]
                                                   ) -> Dict[str, Any]:
        try:
            # TODO: Delete this logging for production
            weather_data = context.get('weather', '')
            # logger.info(
            #     f"Passing to the prompt the following weather data via context.get('weather', ''): {weather_data}")

            prompt = STYLIST_PROMPT_TEMPLATE_CATEGORIZED.format(
                weather=context.get("weather", ""),
                assets=context.get("assets", []),
                style_preferences=", ".join(context.get("style_preferences", []))
            )

            logger.debug(f"Generated prompt: {prompt}")


            response = await self._make_async_completion(prompt)
            recommendation_text = response.choices[0].message.content

            logger.info(f"Raw LLM response: {recommendation_text}")

            try:
                recommendation_json = self._parse_json_from_text(recommendation_text)
                logger.debug(f"Parsed JSON: {json.dumps(recommendation_json, indent=2)}")
                self._validate_categorized_response(recommendation_json)
                return recommendation_json
            except json.JSONDecodeError as je:
                logger.error(f"JSON parsing error: {str(je)}")
                logger.error(f"Problematic text: {recommendation_text}")
                raise LLMException(f"Failed to parse LLM response: {str(je)}")
            except ValueError as ve:
                logger.error(f"Validation error: {str(ve)}")
                raise LLMException(f"Invalid response format: {str(ve)}")

        except Exception as e:
            logger.error(f"Error generating categorized recommendations: {str(e)}")
            raise LLMException(f"Failed to generate categorized recommendations: {str(e)}")

    async def _make_async_completion(self, prompt: str):
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_ROLE},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=600,
                n=1,
                timeout=self.timeout,
                top_p=0.8
            )
            return response

        except Exception as e:
            logger.error(f"Error in _make_async_completion: {str(e)}")
            raise

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
            logger.error(f"Error in json parsing: {str(e)}")
            text = self._fix_json(text)
            try:
                return json.loads(text)
            except json.JSONDecodeError as e2:
                raise LLMException(f"Failed to parse the assistant's reply into JSON: {str(e2)}")

    def _fix_json(self, text: str) -> str:
        # Remove comments
        text = re.sub(r'//.*', '', text)  # Remove // comments
        text = re.sub(r'#.*', '', text)   # Remove # comments
        # and trailing commas
        text = re.sub(r',\s*}', '}', text)  # Remove trailing commas before }
        text = re.sub(r',\s*\]', ']', text)  # Remove trailing commas before ]

        return text

    def _validate_categorized_response(self, response: Dict[str, Any]) -> None:
        try:
            if not isinstance(response, dict):
                raise ValueError(f"Expected dict, got {type(response)}")

            logger.debug(f"Validating response: {json.dumps(response, indent=2)}")

            # Check top-level structure
            required_fields = ["recommendations", "weather_summary", "style_notes"]
            missing_fields = [field for field in required_fields if field not in response]
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

            # Validate recommendations
            recommendations = response["recommendations"]
            if not isinstance(recommendations, dict):
                raise ValueError(f"recommendations must be a dict, got {type(recommendations)}")

            # Check categories
            categories = ["head", "top", "bottom", "footwear"]
            for category in categories:
                if category not in recommendations:
                    raise ValueError(f"Missing category: {category}")
                if not isinstance(recommendations[category], list):
                    raise ValueError(f"Category {category} must be a list")

            # Validate description
            if "description" not in recommendations:
                raise ValueError("Missing description in recommendations")

            return response

        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            raise ValueError(f"Invalid response structure: {str(e)}")
