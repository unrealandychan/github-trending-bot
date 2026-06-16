"""Configuration management for the GitHub Trending Bot.

This module loads, parses, and validates the environment variables
required to run the bot.
"""

import logging
import os
from typing import Optional

# Setup logger for configuration module
logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when required configuration settings are missing or invalid."""
    pass


class Config:
    """Manages system configuration and environment variables."""

    def __init__(self, dotenv_path: Optional[str] = None) -> None:
        """Initializes configuration and attempts to load env variables.

        Args:
            dotenv_path: Optional path to a .env file. If not provided,
                it looks for a local .env or fallback ~/.hermes/.env.
        """
        # Load dotenv if python-dotenv is installed
        try:
            from dotenv import load_dotenv
            if dotenv_path:
                load_dotenv(dotenv_path)
            else:
                # Try local first, then fallback to ~/.hermes/.env
                if os.path.exists(".env"):
                    load_dotenv(".env")
                else:
                    fallback = os.path.expanduser("~/.hermes/.env")
                    if os.path.exists(fallback):
                        load_dotenv(fallback)
        except ImportError:
            logger.debug("python-dotenv not installed; relying on system environment variables.")

        # Core API Credentials
        self.notion_api_key: str = os.getenv("NOTION_API_KEY", "")
        self.notion_database_id: str = os.getenv("NOTION_DATABASE_ID", "7080c1a5-ebf4-4b61-bcea-3267237ee6f6")
        self.tavily_api_key: str = os.getenv("TAVILY_API_KEY", "")
        self.telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")

        # LLM Configurations (Gemini is preferred default, fallback to OpenAI)
        self.llm_provider: str = os.getenv("LLM_PROVIDER", "gemini").lower()
        self.gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
        self.openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
        self.openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o")
        self.gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        
        # Report Configuration
        self.report_language: str = os.getenv("REPORT_LANGUAGE", "English")

        # History tracking
        self.history_file_path: str = os.getenv(
            "HISTORY_FILE_PATH", 
            os.path.expanduser("~/.hermes/scripts/github_trending_seen.json")
        )

        # Fallback to local if directories don't exist
        history_dir = os.path.dirname(self.history_file_path)
        if history_dir and not os.path.exists(history_dir):
            self.history_file_path = "github_trending_history.json"

    def validate_core(self) -> None:
        """Validates that essential configs are present.

        Raises:
            ConfigurationError: If crucial configurations are missing.
        """
        missing = []
        if not self.notion_api_key:
            missing.append("NOTION_API_KEY")
        if not self.notion_database_id:
            missing.append("NOTION_DATABASE_ID")

        # Must have at least one LLM key to run Cantonese analysis
        if self.llm_provider == "gemini" and not self.gemini_api_key:
            # Let's see if we can reuse the OpenAI key instead, or try loading from existing fields
            if self.openai_api_key:
                logger.warning("Gemini key missing, but OpenAI key is present. Switching provider to openai.")
                self.llm_provider = "openai"
            else:
                missing.append("GEMINI_API_KEY")
        elif self.llm_provider == "openai" and not self.openai_api_key:
            if self.gemini_api_key:
                logger.warning("OpenAI key missing, but Gemini key is present. Switching provider to gemini.")
                self.llm_provider = "gemini"
            else:
                missing.append("OPENAI_API_KEY")

        if missing:
            raise ConfigurationError(
                f"Missing required environment variables: {', '.join(missing)}. "
                "Please configure them in your environment or a .env file."
            )

        logger.info("Configuration validated successfully.")
