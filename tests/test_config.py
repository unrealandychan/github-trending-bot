"""Unit tests for Config loader."""

import os
import unittest
from src.config import Config, ConfigurationError


class TestConfig(unittest.TestCase):
    """Verifies that Config handles environmental variables and validation guard clauses."""

    def setUp(self) -> None:
        """Cleans environmental overrides before each test."""
        self.original_env = os.environ.copy()
        for key in ["NOTION_API_KEY", "NOTION_DATABASE_ID", "GEMINI_API_KEY", "OPENAI_API_KEY", "LLM_PROVIDER"]:
            if key in os.environ:
                del os.environ[key]

    def tearDown(self) -> None:
        """Restores original environment."""
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_missing_notion_key_raises_error(self) -> None:
        """validate_core should raise ConfigurationError if Notion API key is missing."""
        os.environ["NOTION_DATABASE_ID"] = "12345"
        os.environ["GEMINI_API_KEY"] = "gemini_key"
        
        config = Config()
        with self.assertRaises(ConfigurationError):
            config.validate_core()

    def test_successful_validation_gemini(self) -> None:
        """Should validate successfully if both Notion and LLM (Gemini) keys are present."""
        os.environ["NOTION_API_KEY"] = "notion_secret"
        os.environ["NOTION_DATABASE_ID"] = "12345"
        os.environ["GEMINI_API_KEY"] = "gemini_secret"
        os.environ["LLM_PROVIDER"] = "gemini"

        config = Config()
        config.validate_core()  # Should not raise any error
        self.assertEqual(config.llm_provider, "gemini")

    def test_fallback_to_openai_if_gemini_missing(self) -> None:
        """Should switch provider to openai if Gemini key is missing but OpenAI key is available."""
        os.environ["NOTION_API_KEY"] = "notion_secret"
        os.environ["NOTION_DATABASE_ID"] = "12345"
        os.environ["OPENAI_API_KEY"] = "openai_secret"
        os.environ["LLM_PROVIDER"] = "gemini"  # requested gemini but missing key

        config = Config()
        config.validate_core()  # Should perform graceful fallback
        self.assertEqual(config.llm_provider, "openai")


if __name__ == "__main__":
    unittest.main()
