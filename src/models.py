"""Domain models for the GitHub Trending Bot.

This module defines the core data classes used across the system,
representing repositories and trending reports.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Repository:
    """Represents a trending GitHub repository.

    Attributes:
        repo: The full repository name (e.g., 'owner/repo').
        desc: The description of the repository.
        lang: The primary programming language of the repository.
        today_stars: The number of stars gained today (or during the trending period).
        stars: The total number of stars.
        why_it_matters: A summary explaining why this repo is significant.
        context_analysis: Deeper context gathered from search engines/Tavily.
    """
    repo: str
    desc: str
    lang: str
    today_stars: str
    stars: str
    why_it_matters: Optional[str] = None
    context_analysis: Optional[str] = None

    @property
    def url(self) -> str:
        """Returns the absolute URL of the repository."""
        return f"https://github.com/{self.repo}"


@dataclass
class TrendReport:
    """Represents the compiled daily trending report.

    Attributes:
        date: The date of the report (YYYY-MM-DD).
        repositories: The list of featured trending repositories.
        theme_summary: A Cantonese summary of today's key trending themes.
        main_theme: The primary theme of the day.
    """
    date: str
    repositories: List[Repository] = field(default_factory=list)
    theme_summary: str = ""
    main_theme: str = ""
