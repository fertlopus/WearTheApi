import logging
import os
import sys
from typing import Dict, Any

def setup_logging() -> Dict[str, Any]:
    """Logging configuration settings"""
    environment = os.getenv("ENVIRONMENT", "dev")

    log_level = "DEBUG" if environment == "dev" else "INFO"
    if environment == "production":
        log_level = "WARNING"

    # Base logging configuration:
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "default",
            },
        },
        "root": {"level": log_level, "handlers": ["console"]},
    }

    # logging in production
    if environment == "production":
        logging_config["handlers"]["file"] = {
            "class": "logging.FileHandler",
            "filename": "app.log",
            "formatter": "default",
        }
        logging_config["root"]["handlers"].append("file")

    return logging_config
