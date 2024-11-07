from functools import lru_cache
import logging
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from dotenv import load_dotenv

class Settings(BaseSettings):
    """Weather App settings. Local dev: .env file or Azure Key Vault"""
    # "dev" / "staging" or "production"
    ENVIRONMENT: str

    # API Settings
    API_V1_STR: str
    WEATHER_API_PROJECT_NAME: str

    # OpenWeather API
    OPENWEATHER_API_KEY: Optional[str] = None
    OPENWEATHER_API_URL: AnyHttpUrl

    # Redis Cache
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: Optional[str] = None

    # Cache Settings
    WEATHER_CACHE_EXPIRATION: int

    # Azure Key Vault
    AZURE_KEYVAULT_URL: Optional[str] = None

    def load_secrets_from_key_vault(self):
        """Load secrets from Azure Key Vault if in prod"""
        if self.ENVIRONMENT == "production" and self.AZURE_KEY_VAULT_URL:
            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=self.AZURE_KEY_VAULT_URL, credential=credential)
            for field in self.model_fields:
                if not getattr(self, field):
                    try:
                        secret = client.get_secret(field)
                        setattr(self, field, secret.value)
                    except Exception as e:
                        logging.log(f"Could not retrieve the {field} from Azure KV: {e}")

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


test = get_settings()
print(test)

