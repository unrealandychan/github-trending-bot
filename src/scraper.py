"""Scraping service for GitHub Trending.

This module fetches and parses the daily GitHub Trending page
without external HTML-parsing dependencies like BeautifulSoup.
"""

import logging
import urllib.request
import re
from typing import List
from src.models import Repository

# Setup logger for scraper module
logger = logging.getLogger(__name__)


class ScraperError(Exception):
    """Raised when scraping GitHub Trending fails."""
    pass


class ScraperService:
    """Service to handle fetching and parsing of GitHub trending repositories."""

    TRENDING_URL = "https://github.com/trending"
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    def fetch_html(self, since: str = "daily") -> str:
        """Fetches the HTML of the GitHub Trending page.

        Args:
            since: The trending period ('daily', 'weekly', 'monthly').

        Returns:
            The raw HTML content of the page as a string.

        Raises:
            ScraperError: If the HTTP request fails.
        """
        url = self.TRENDING_URL
        if since != "daily":
            url = f"{self.TRENDING_URL}?since={since}"

        logger.info("Fetching GitHub Trending page from %s...", url)
        req = urllib.request.Request(
            url,
            headers={"User-Agent": self.USER_AGENT}
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                html_bytes = response.read()
                return html_bytes.decode("utf-8")
        except Exception as e:
            logger.error("Failed to fetch trending page: %s", e)
            raise ScraperError(f"HTTP request to GitHub Trending failed: {e}") from e

    def parse_trending(self, html: str) -> List[Repository]:
        """Parses the GitHub Trending HTML and extracts repository details.

        Args:
            html: Raw HTML content of the trending page.

        Returns:
            A list of Repository objects containing parsed details.
        """
        logger.info("Parsing trending repositories from HTML...")
        articles = re.findall(r'<article class="Box-row">.*?</article>', html, re.DOTALL)
        logger.info("Found %d raw repository blocks in HTML.", len(articles))

        parsed_repos: List[Repository] = []

        for index, art in enumerate(articles, 1):
            try:
                # 1. Extract repository name (e.g. "owner/repo")
                # Search for any standard href link pointing to the repository
                repo_match = re.search(r'href="/([^/"]+/[^/"]+)"', art)
                if not repo_match:
                    continue
                
                repo = repo_match.group(1).strip()
                # Clean up if login/trending endpoints were caught accidentally
                if "login" in repo or "trending" in repo:
                    hrefs = re.findall(r'href="/([^/"]+/[^/"]+)"', art)
                    for h in hrefs:
                        if all(k not in h for k in ["login", "trending", "stargazers", "forks", "settings"]):
                            repo = h
                            break

                # 2. Extract description
                desc_match = re.search(r'<p class="col-9 color-fg-muted my-1[^"]*">([\s\S]*?)</p>', art)
                desc = desc_match.group(1).strip() if desc_match else ""
                desc = re.sub(r'<[^>]+>', '', desc)  # strip internal tags
                desc = " ".join(desc.split())

                # 3. Extract programming language
                lang_match = re.search(r'itemprop="programmingLanguage">([^<]+)<', art)
                lang = lang_match.group(1).strip() if lang_match else "Unknown"

                # 4. Extract stars gained today (or since daily/weekly)
                today_match = re.search(r'([\d,]+)\s+stars?\s+today', art)
                if not today_match:
                    # Alternative regex check
                    today_match = re.search(r'([\d,]+)\s+stars?\s+this\s+(?:week|month)', art)
                today_stars = today_match.group(1).strip() if today_match else "0"

                # 5. Extract total stars
                stars_match = re.search(r'href="/' + re.escape(repo) + r'/stargazers"[^>]*>([\s\S]*?)</a>', art)
                if not stars_match:
                    stars_match = re.search(r'href="[^"]+/stargazers"[^>]*>([\s\S]*?)</a>', art)
                
                stars = "0"
                if stars_match:
                    stars_raw = stars_match.group(1).strip()
                    stars_clean = re.sub(r'<[^>]+>', '', stars_raw).strip()
                    stars = " ".join(stars_clean.split())

                repository = Repository(
                    repo=repo,
                    desc=desc,
                    lang=lang,
                    today_stars=today_stars,
                    stars=stars
                )
                parsed_repos.append(repository)
                logger.debug("Parsed repo [%d]: %s", index, repo)

            except Exception as e:
                logger.warning("Error parsing repository block %d: %s. Skipping.", index, e)
                continue

        logger.info("Successfully parsed %d repositories.", len(parsed_repos))
        return parsed_repos
