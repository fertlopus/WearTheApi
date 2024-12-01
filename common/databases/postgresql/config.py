import os
from functools import lru_cache
from typing import Optional

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from dotenv import load_dotenv
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """
    Database configuration settings
    """

    ENVIRONMENT: str = "dev"
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str

    # Azure Key-Vault settings
    AZURE_KEYVAULT_URL: Optional[str] = None

    # Redis Settings
    REDIS_HOST: str
    REDIS_PORT: str = "6379"
    REDIS_PASSWORD: Optional[str] = None

    @property
    def postgres_dsn(self) -> str:
        """Generate PostgreSQL DSN as f-string"""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}" f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def redis_dsn(self) -> str:
        """Generate Redis DSN as f-string"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:" f"{self.REDIS_PORT}/0"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


class SecretManager:
    """Manage secrets for local and cloud secrets"""

    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "dev")
        self.key_vault_url = os.getenv("AZURE_KEYVAULT_URL", "")

        if self.environment == "dev":
            load_dotenv()
        elif self.key_vault_url:
            self.credential = DefaultAzureCredential()
            self.secret_client = SecretClient(vault_url=self.key_vault_url, credential=self.credential)

    def get_secret(self, secret_name: str) -> str | ValueError:
        """Get secret from env/KV by name"""
        if self.environment == "dev":
            val = os.getenv(secret_name)
            if val is None:
                raise ValueError(f"Secret || {secret_name} || not found in env file.")
            return val

        if self.key_vault_url:
            try:
                return self.secret_client.get_secret(secret_name).value
            except Exception as e:
                raise ValueError(f"Failed to get secret from KV\nSecret Name: {secret_name}: {str(e)}")

        return ValueError("No secret source configured")


@lru_cache()
def get_db_settings() -> DatabaseSettings:
    """Get cached database settings"""
    secret_manager = SecretManager()

    # Cloud -> secrets from KV
    if os.getenv("ENVIRONMENT") != "dev":
        try:
            return DatabaseSettings(
                POSTGRES_USER=secret_manager.get_secret("POSTGRES_USER"),
                POSTGRES_PASSWORD=secret_manager.get_secret("POSTGRES_PASSWORD"),
                POSTGRES_HOST=secret_manager.get_secret("POSTGRES_HOST"),
                POSTGRES_DB=secret_manager.get_secret("POSTGRES_DB"),
                REDIS_HOST=secret_manager.get_secret("REDIS_HOST"),
                REDIS_PASSWORD=secret_manager.get_secret("REDIS_PASSWORD"),
                REDIS_PORT=secret_manager.get_secret("REDIS_PORT"),
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize database settings: {str(e)}")

    # Local dev
    try:
        return DatabaseSettings()
    except Exception as e:
        raise RuntimeError(f"Failed to initialize/load dev settings for database: {str(e)}")
