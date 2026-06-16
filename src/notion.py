"""Notion database integration service.

This module provides programmatic access to the Notion API, implementing
a robust two-step write pattern (Create Page metadata -> Append Blocks children)
fully compatible with Chinese characters/CJK encoding.
"""

import json
import logging
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional
from src.models import TrendReport, Repository

# Setup logger for notion module
logger = logging.getLogger(__name__)


class NotionError(Exception):
    """Raised when Notion API interaction fails."""
    pass


class NotionService:
    """Service to handle creating pages and writing reports to Notion databases."""

    API_BASE_URL = "https://api.notion.com/v1"
    NOTION_VERSION = "2022-06-28"

    def __init__(self, api_key: str, database_id: str) -> None:
        """Initializes the Notion service.

        Args:
            api_key: The Notion Integration Secret Token.
            database_id: The Target Database ID.
        """
        self.api_key = api_key
        self.database_id = database_id

    @property
    def _headers(self) -> Dict[str, str]:
        """Returns standard headers required by Notion API."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Notion-Version": self.NOTION_VERSION,
            "Content-Type": "application/json"
        }

    def _send_request(self, endpoint: str, data: Dict[str, Any], method: str = "POST") -> Dict[str, Any]:
        """Helper to send HTTP requests to Notion API safely.

        Args:
            endpoint: Relative path from API_BASE_URL.
            data: Payload as dictionary.
            method: HTTP Verb.

        Returns:
            JSON response from Notion as dictionary.

        Raises:
            NotionError: If the request fails.
        """
        url = f"{self.API_BASE_URL}{endpoint}"
        body_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=body_bytes,
            headers=self._headers,
            method=method
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            logger.error("Notion API Error (%d): %s", e.code, error_body)
            raise NotionError(f"Notion request {method} {endpoint} failed with code {e.code}: {error_body}") from e
        except Exception as e:
            logger.error("Notion Connection Failed: %s", e)
            raise NotionError(f"Failed to communicate with Notion API: {e}") from e

    def create_page(self, title: str, date_str: str, main_theme: str, summary: str) -> str:
        """Step 1: Creates a new page in the database with metadata.

        Args:
            title: The title of the Notion page.
            date_str: Date formatted as YYYY-MM-DD.
            main_theme: The main theme rich_text.
            summary: The quick summary rich_text.

        Returns:
            The created page's ID.

        Raises:
            NotionError: If page creation fails.
        """
        logger.info("Creating new Notion page in Database: %s...", self.database_id)
        
        payload = {
            "parent": {"database_id": self.database_id},
            "properties": {
                "Name": {
                    "title": [{"text": {"content": title}}]
                },
                "Date": {
                    "date": {"start": date_str}
                },
                "Content Type": {
                    "select": {"name": "GitHub Trending"}
                },
                "Main Topic": {
                    "rich_text": [{"text": {"content": main_theme or "GitHub Trending"}}]
                },
                "Quick Summary": {
                    "rich_text": [{"text": {"content": summary or "今日 GitHub Trending 開源項目日報"}}]
                },
                "Status": {
                    "select": {"name": "New"}
                },
                "Priority": {
                    "select": {"name": "Medium"}
                },
                "Tags": {
                    "multi_select": [
                        {"name": "GitHub"},
                        {"name": "Trending"},
                        {"name": "Open Source"}
                    ]
                }
            }
        }

        response = self._send_request("/pages", payload, "POST")
        page_id = response.get("id")
        if not page_id:
            raise NotionError("Failed to retrieve Page ID from Notion response.")

        logger.info("Created Notion page successfully. Page ID: %s", page_id)
        return page_id

    def append_blocks(self, page_id: str, report: TrendReport) -> None:
        """Step 2: Appends the detailed report as children blocks of the page.

        Args:
            page_id: The ID of the page to append blocks to.
            report: The full TrendReport object.

        Raises:
            NotionError: If block appending fails.
        """
        logger.info("Appending report block children to Notion page %s...", page_id)

        blocks: List[Dict[str, Any]] = [
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [
                        {
                            "text": {
                                "content": f"🔥 GitHub Trending 日報 — {report.date}\n主題：{report.main_theme}\n此報告由 AI 分析、過濾並自動整理，旨在發掘最值得關注的開源項目。"
                            }
                        }
                    ],
                    "icon": {"emoji": "🔥"}
                }
            },
            {"object": "block", "type": "divider", "divider": {}}
        ]

        # Add each repository block
        for idx, repo in enumerate(report.repositories, 1):
            # Heading 2 for Repo Name and Stars
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "text": {
                                "content": f"{idx}. {repo.repo} ⭐ {repo.stars}"
                            }
                        }
                    ]
                }
            })

            # Paragraph for Stats and Description
            lang_str = f"語言：{repo.lang}" if repo.lang else "語言：未知"
            stars_today_str = f"今日新增：+{repo.today_stars}" if repo.today_stars else ""
            meta_str = f"🔗 {repo.url}\n📦 {lang_str} | {stars_today_str}\n\n描述：\n{repo.desc}"
            
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "text": {
                                "content": meta_str
                            }
                        }
                    ]
                }
            })

            # Callout for why it matters (analysis)
            if repo.why_it_matters:
                blocks.append({
                    "object": "block",
                    "type": "callout",
                    "callout": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": f"💡 點解重要？\n{repo.why_it_matters}"
                                }
                            }
                        ],
                        "icon": {"emoji": "💡"}
                    }
                })

            # Add divider between repos
            blocks.append({"object": "block", "type": "divider", "divider": {}})

        # Add overall summary block
        if report.theme_summary:
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"text": {"content": "📊 今日趨勢總結"}}]
                }
            })
            blocks.append({
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"text": {"content": report.theme_summary}}],
                    "icon": {"emoji": "📊"}
                }
            })

        # Append blocks in chunks of 50 (Notion API max limits)
        chunk_size = 50
        for i in range(0, len(blocks), chunk_size):
            chunk = blocks[i : i + chunk_size]
            payload = {"children": chunk}
            self._send_request(f"/blocks/{page_id}/children", payload, "PATCH")

        logger.info("Successfully appended all blocks to Notion.")

    def publish_report(self, report: TrendReport) -> str:
        """Coordinates creating the page and appending details in Notion.

        Args:
            report: The full TrendReport object.

        Returns:
            The Notion Web URL of the published page.
        """
        title = f"📊 GitHub Trending 日報 {report.date}"
        
        # Step 1: Create page
        page_id = self.create_page(
            title=title,
            date_str=report.date,
            main_theme=report.main_theme,
            summary=report.theme_summary[:100] + "..." if len(report.theme_summary) > 100 else report.theme_summary
        )

        # Step 2: Append body blocks
        self.append_blocks(page_id, report)

        clean_page_id = page_id.replace("-", "")
        web_url = f"https://www.notion.so/{clean_page_id}"
        logger.info("Published to Notion. Web URL: %s", web_url)
        return web_url
