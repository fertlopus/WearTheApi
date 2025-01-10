from functools import lru_cache
import logging
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl
from dotenv import load_dotenv


logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Weather App settings. Local dev: .env file or Azure Key Vault"""

    # "dev" / "staging" or "production"
    ENVIRONMENT: str = "dev"

    # API Settings
    API_V1_STR: str
    WEATHER_API_PROJECT_NAME: str

    # OpenWeather API
    OPENWEATHER_API_KEY: Optional[str] = None
    OPENWEATHER_API_URL: AnyHttpUrl
    OPENWEATHER_API_RETRIES: int = 3
    OPENWEATHER_BACKOFF_FACTOR: Optional[float] = 0.5

    # Redis Cache
    REDIS_PRIMARY_CONNECTION_STRING: str

    # Cache Settings
    WEATHER_CACHE_EXPIRATION: int = 3600

    # Azure Key Vault
    AZURE_KEYVAULT_URL: Optional[str] = None
    AZURE_APP_CONFIG_CONNECTION_STRING: Optional[str] = None

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() in ["development", "dev"]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() in ["production", "prod"]

    # def get_redis_connection_info(self) -> Dict[str, Any]:
    #     if self.is_production and self.REDIS_CONNECTION_STRING:
    #         return {
    #             "connection_string": self.REDIS_CONNECTION_STRING
    #         }
    #     else:
    #         return {
    #             "host": self.REDIS_HOST,
    #             "port": self.REDIS_PORT,
    #             "password": self.REDIS_PASSWORD
    #         }

    # def load_secrets_from_key_vault(self):
    #     """Load secrets from Azure Key Vault if in prod"""
    #     if not self.is_production or not self.AZURE_KEYVAULT_URL:
    #         return
    #     try:
    #         logger.info("Loading secrets from AZ Key-vault service")
    #         print("Loading secrets from AZ Key-Vault service")
    #
    #         try:
    #             credential = ManagedIdentityCredential()
    #             client = SecretClient(vault_url=self.AZURE_KEYVAULT_URL, credential=credential)
    #             # Connection test
    #             client.get_secret("test-secret")
    #         except Exception as e:
    #             logger.info("Falling back to DefaultAzureCredential")
    #             print("Falling back to DefaultAzureCredential")
    #             credential = DefaultAzureCredential()
    #             client = SecretClient(vault_url=self.AZURE_KEYVAULT_URL, credential=credential)
    #         secret_mapping = {
    #             "OPENWEATHER_API_KEY": "openweather-api-key",
    #             "OPENWEATHER_API_URL": "openweather-api-url",
    #             "REDIS_PRIMARY_CONNECTION_STRING": "redis-connection-string",
    #         }
    #         for env_var, secret_name in secret_mapping.items():
    #             try:
    #                 secret = client.get_secret(secret_name)
    #                 setattr(self, env_var, secret.value)
    #                 logger.info(f"Loaded secret: {secret_name}")
    #                 print(f"Loaded secret: {secret_name}")
    #             except Exception as e:
    #                 logger.info(f"Failed to load secret {secret_name}: {str(e)}")
    #
    #     except Exception as e:
    #         logger.error(f"Failed to connect to Azure Key Vault: {str(e)}")
    #         print(f"Failed to connect to Azure Key Vault: {str(e)}")
    #         if self.is_production:
    #             raise

    class Config:
        # load_dotenv()
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"


@lru_cache(maxsize=16)
def get_settings() -> Settings:
    load_dotenv()
    settings = Settings()
    # if settings.is_production:
    #     settings.load_secrets_from_key_vault()
    # settings.load_secrets_from_key_vault()
    return settings
