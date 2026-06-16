"""Telegram notification service.

This module provides programmatic access to the Telegram Bot API
to send report alerts and daily summaries.
"""

import json
import logging
import urllib.request
from typing import Dict, Any, Optional

# Setup logger for telegram module
logger = logging.getLogger(__name__)


class TelegramService:
    """Service to send alerts and formatted messages to a Telegram chat."""

    def __init__(self, bot_token: str, chat_id: str) -> None:
        """Initializes the Telegram service.

        Args:
            bot_token: The Telegram Bot API secret token.
            chat_id: The target chat or user ID.
        """
        self.bot_token = bot_token
        self.chat_id = chat_id

    def send_report_summary(self, summary_text: str, notion_url: Optional[str] = None) -> bool:
        """Sends a beautiful summary of the trending report to Telegram.

        Args:
            summary_text: The pre-formatted report text (HTML or Markdown).
            notion_url: Optional Notion URL to append at the bottom.

        Returns:
            True if the message was sent successfully, False otherwise.
        """
        if not self.bot_token or not self.chat_id:
            logger.info("Telegram credentials missing or not configured. Skipping Telegram notification.")
            return False

        logger.info("Sending GitHub Trending summary to Telegram chat %s...", self.chat_id)
        
        # Build the final message content
        text = summary_text
        if notion_url:
            text += f"\n\n📖 完整 Notion 報告：\n🔗 {notion_url}"

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",  # Using HTML parser for standard, reliable markup support
            "disable_web_page_preview": False
        }

        try:
            body = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                result = json.loads(response.read().decode("utf-8"))
                if result.get("ok"):
                    logger.info("Telegram notification sent successfully.")
                    return True
                else:
                    logger.warning("Telegram API returned non-ok: %s", result)
                    return False
        except Exception as e:
            logger.error("Failed to send message to Telegram: %s", e)
            return False
