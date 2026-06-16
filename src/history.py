"""History tracking service for the GitHub Trending Bot.

This module manages tracking of already seen repositories to prevent
recommending duplicate items across days.
"""

import json
import logging
import os
from typing import List, Set

# Setup logger for history module
logger = logging.getLogger(__name__)


class HistoryService:
    """Manages reading, verifying, and writing recommended repositories."""

    def __init__(self, file_path: str, max_history_size: int = 600) -> None:
        """Initializes the history tracker.

        Args:
            file_path: Absolute path to the JSON file where history is stored.
            max_history_size: Maximum number of repository items to track
                (defaults to 600, which keeps roughly 2 months of history).
        """
        self.file_path = file_path
        self.max_history_size = max_history_size
        self._history: List[str] = self._load_history()
        self._history_set: Set[str] = set(self._history)

    def _load_history(self) -> List[str]:
        """Loads repository names from the history file.

        Returns:
            A list of seen repository names.
        """
        logger.debug("Loading trending history from %s...", self.file_path)
        if not os.path.exists(self.file_path):
            logger.info("History file %s not found. Creating a new history list.", self.file_path)
            return []

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    logger.info("Loaded %d repositories from history.", len(data))
                    return [str(item) for item in data]
                else:
                    logger.warning("History file format invalid (expected list). Starting fresh.")
                    return []
        except Exception as e:
            logger.error("Failed to read history file %s: %s", self.file_path, e)
            return []

    def is_new(self, repo: str) -> bool:
        """Checks if a repository has not been seen before in the history.

        Args:
            repo: Repo path (e.g. 'owner/repo').

        Returns:
            True if the repository is new, False if already seen.
        """
        # Case insensitive comparison for robustness
        return repo.lower() not in {r.lower() for r in self._history_set}

    def add_repos(self, repos: List[str]) -> None:
        """Adds repository names to the history and persists to the JSON file.

        Args:
            repos: A list of repository names to append to history.
        """
        if not repos:
            return

        # Add only new ones (case insensitive uniqueness)
        added_count = 0
        for r in repos:
            if self.is_new(r):
                self._history.append(r)
                self._history_set.add(r)
                added_count += 1

        if added_count == 0:
            logger.debug("No new repositories to write to history.")
            return

        # Enforce size limit to prevent file bloat
        if len(self._history) > self.max_history_size:
            self._history = self._history[-self.max_history_size:]
            self._history_set = set(self._history)
            logger.debug("History truncated to %d items.", self.max_history_size)

        # Attempt to create parent folders if they don't exist
        os.makedirs(os.path.dirname(os.path.abspath(self.file_path)), exist_ok=True)

        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self._history, f, indent=2, ensure_ascii=False)
            logger.info("Persisted %d new repositories to history file. Total tracked: %d", 
                        added_count, len(self._history))
        except Exception as e:
            logger.error("Failed to write history to %s: %s", self.file_path, e)

    def get_seen_count(self) -> int:
        """Returns the total number of tracked seen repositories."""
        return len(self._history)
