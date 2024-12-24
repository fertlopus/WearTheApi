from functools import lru_cache
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, field_validator
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import logging
from dotenv import load_dotenv


logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Recommendation Service settings"""
    # "dev" / "staging" or "production"
    ENVIRONMENT: str

    # API Settings
    API_V1_STR: str
    RECOMMENDATION_API_PROJECT_NAME: str

    # Weather Service API endpoint
    WEATHER_SERVICE_URL: str
    WEATHER_SERVICE_TIMEOUT: int = 10

    # Redis Settings
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0

    # LLM Settings
    # TODO: LLM Provider agnostic settings, e.g. openai, azure, claude, etc.
    LLM_PROVIDER: str = "openai"
    OPEN_AI_API_KEY: Optional[str] = None
    OPEN_AI_MODEL: Optional[str] = None
    OPENAI_API_VERSION: Optional[str] = "2024-07-18"
    OPEN_AI_TEMPERATURE: Optional[float] = 0.25
    # AZURE_OPENAI_API_KEY: Optional[str] = None
    # AZURE_OPENAI_LLM_ENDPOINT: Optional[str] = None

    # Assets Database
    # TODO: Assets source agnostic settings, e.g. json, postgres, mongodb, etc.
    ASSETS_SOURCE: str = "json"
    ASSETS_PATH: str = "/app/local_data/preprocessed/clothing_data.json"

    # Recommendation Cache TTL
    RECOMMENDATION_CACHE_EXPIRATION: int
    MAX_RECOMMENDATIONS: int = 5

    # Recommendation Cache TTL
    RECOMMENDATION_CACHE_EXPIRATION: int

    # Azure Key Vault
    AZURE_KEYVAULT_URL: Optional[str] = None

    def load_secrets_from_key_vault(self):
        """Load secrets from Azure Key Vault if in prod"""
        if self.ENVIRONMENT == "production" and self.AZURE_KEYVAULT_URL:
            try:
                logging.info("Loading secrets from Azure KV.")
                credential = DefaultAzureCredential()
                client = SecretClient(vault_url=self.AZURE_KEYVAULT_URL, credential=credential)
                for field in self.model_fields:
                    if not getattr(self, field):
                        try:
                            secret = client.get_secret(field)
                            setattr(self, field, secret.value)
                            logging.info(f"Loaded secret for {field} from Azure Key Vault Storage.")
                        except Exception as e:
                            logging.error(f"Could not retrieve the {field} from Azure Key Vault Storage.\n{str(e)}")
            except Exception as e:
                logging.error(f"Failed to connect to Azure Key Vault: {str(e)}")

    @field_validator("WEATHER_SERVICE_URL")
    def validate_weather_service_url(cls, v: str) -> str:
        if not v.endswith("/"):
            v += "/"
        return v

    class Config:
        load_dotenv()
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"


@lru_cache(maxsize=256)
def get_settings() -> Settings:
    settings = Settings()
    settings.load_secrets_from_key_vault()
    return settings
