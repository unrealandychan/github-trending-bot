"""Coordinator service for the GitHub Trending Bot.

This module orchestrates the entire pipeline: scraping, filtering,
enriching with Tavily, summarizing with LLM, publishing to Notion,
recording to history, and notifying via Telegram.
"""

import datetime
import logging
from typing import List, Optional
from src.config import Config
from src.models import TrendReport, Repository
from src.scraper import ScraperService
from src.history import HistoryService
from src.llm import TavilyService, LLMService
from src.notion import NotionService
from src.telegram import TelegramService

# Setup logger for coordinator module
logger = logging.getLogger(__name__)


class TrendingCoordinator:
    """Orchestrates and runs the daily GitHub Trending pipeline."""

    def __init__(self, config: Config) -> None:
        """Initializes the coordinator with validated config.

        Args:
            config: A validated Config instance.
        """
        self.config = config
        self.scraper = ScraperService()
        self.history = HistoryService(config.history_file_path)
        self.tavily = TavilyService(config.tavily_api_key)
        self.llm = LLMService(
            provider=config.llm_provider,
            api_key=config.gemini_api_key if config.llm_provider == "gemini" else config.openai_api_key,
            model_name=config.gemini_model if config.llm_provider == "gemini" else config.openai_model,
            report_language=config.report_language
        )
        self.notion = NotionService(config.notion_api_key, config.notion_database_id)
        self.telegram = TelegramService(config.telegram_bot_token, config.telegram_chat_id)

    def format_telegram_html(self, report: TrendReport) -> str:
        """Formats the TrendReport into a beautiful HTML message for Telegram.

        Args:
            report: The compiled TrendReport.

        Returns:
            An HTML-formatted string suitable for Telegram sendMessage.
        """
        date_str = report.date
        theme = report.main_theme or "GitHub Trending"
        
        lines = [
            f"📊 <b>GitHub Trending 日報 ({date_str})</b>",
            f"🎯 <b>今日主題：</b> {theme}",
            "",
            "🔥 <b>今日熱門項目：</b>"
        ]

        for idx, repo in enumerate(report.repositories, 1):
            lang_lbl = f" | {repo.lang}" if repo.lang and repo.lang != "Unknown" else ""
            stars_lbl = f" | ⭐ 今日: +{repo.today_stars}" if repo.today_stars else ""
            lines.append(
                f"{idx}. <b>{repo.repo}</b> ({repo.stars} stars{lang_lbl}{stars_lbl})\n"
                f"🔗 https://github.com/{repo.repo}\n"
                f"💡 {repo.why_it_matters or repo.desc}"
            )
            # Add a small separator but not after the last item
            if idx < len(report.repositories):
                lines.append("")

        if report.theme_summary:
            lines.append("")
            lines.append("💡 <b>今日趨勢分析：</b>")
            lines.append(report.theme_summary)

        return "\n".join(lines)

    def run(self, max_repos: int = 10, since: str = "daily") -> Optional[str]:
        """Runs the complete automation workflow.

        Args:
            max_repos: Maximum number of new repositories to recommend.
            since: Scraping period ('daily', 'weekly', 'monthly').

        Returns:
            The URL of the published Notion page if successful, or None.
        """
        logger.info("Starting Daily GitHub Trending Pipeline...")
        today_str = datetime.date.today().strftime("%Y-%m-%d")

        # 1. Fetch raw trending repos from GitHub
        try:
            raw_html = self.scraper.fetch_html(since=since)
            all_repos = self.scraper.parse_trending(raw_html)
        except Exception as e:
            logger.error("Failed to scrape GitHub trending: %s. Aborting pipeline.", e)
            return None

        if not all_repos:
            logger.warning("No repositories found during scraping. Aborting pipeline.")
            return None

        # 2. Filter out already recommended repositories
        new_repos: List[Repository] = []
        for r in all_repos:
            if self.history.is_new(r.repo):
                new_repos.append(r)
                if len(new_repos) >= max_repos:
                    break

        logger.info("Filtered %d raw repos to %d new, unseen repositories.", len(all_repos), len(new_repos))

        if not new_repos:
            logger.info("No new repositories found to recommend today. (All were previously seen).")
            # We can still send an alert or finish silently
            return None

        # 3. Enrich selected repos with online context (Tavily Search)
        for idx, r in enumerate(new_repos, 1):
            logger.info("[%d/%d] Fetching Tavily search context for %s...", idx, len(new_repos), r.repo)
            r.context_analysis = self.tavily.search_repo_context(r.repo)

        # 4. Generate beautiful Cantonese explanations and theme analysis via LLM
        try:
            llm_analysis = self.llm.generate_report_content(today_str, new_repos)
            
            # Map LLM results back to Repository and TrendReport models
            main_theme = llm_analysis.get("main_theme", "GitHub Trending")
            theme_summary = llm_analysis.get("theme_summary", "")
            repos_why = llm_analysis.get("repos_why_it_matters", {})

            for r in new_repos:
                r.why_it_matters = repos_why.get(r.repo, r.desc)

            report = TrendReport(
                date=today_str,
                repositories=new_repos,
                theme_summary=theme_summary,
                main_theme=main_theme
            )
        except Exception as e:
            logger.error("LLM report generation failed: %s. Using default descriptions.", e)
            # Fallback to a basic report without LLM insights
            report = TrendReport(
                date=today_str,
                repositories=new_repos,
                theme_summary="今日 GitHub Trending 呈現出多元開發趨勢。 (LLM 服務不可用)",
                main_theme="GitHub Trending"
            )
            for r in new_repos:
                r.why_it_matters = r.desc

        # 5. Publish to Notion Database (Two-step write)
        notion_url = None
        try:
            notion_url = self.notion.publish_report(report)
            logger.info("Notion Page successfully published: %s", notion_url)
        except Exception as e:
            logger.error("Failed to publish to Notion: %s", e)

        # 6. Save newly recommended repos to history to avoid duplicates next time
        recommended_names = [r.repo for r in new_repos]
        self.history.add_repos(recommended_names)

        # 7. Format and send to Telegram Chat
        telegram_html = self.format_telegram_html(report)
        self.telegram.send_report_summary(telegram_html, notion_url)

        logger.info("Daily GitHub Trending Pipeline finished successfully!")
        return notion_url
