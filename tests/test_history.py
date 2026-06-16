"""Unit tests for the HistoryService."""

import json
import os
import tempfile
import unittest
from src.history import HistoryService


class TestHistoryService(unittest.TestCase):
    """Verifies that the HistoryService handles deduplication and file persistence correctly."""

    def setUp(self) -> None:
        """Sets up a temporary history file for each test."""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.temp_file.close()
        self.file_path = self.temp_file.name

    def tearDown(self) -> None:
        """Cleans up the temporary history file."""
        if os.path.exists(self.file_path):
            os.remove(self.file_path)

    def test_load_empty_history(self) -> None:
        """Should return an empty list if file doesn't exist or is empty."""
        # Test non-existing file
        os.remove(self.file_path)
        service = HistoryService(self.file_path)
        self.assertEqual(service.get_seen_count(), 0)

    def test_load_existing_history(self) -> None:
        """Should load historical entries correctly from the JSON file."""
        initial_data = ["owner/repo1", "owner/repo2"]
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        service = HistoryService(self.file_path)
        self.assertEqual(service.get_seen_count(), 2)
        self.assertFalse(service.is_new("owner/repo1"))
        self.assertTrue(service.is_new("owner/repo3"))

    def test_is_new_case_insensitive(self) -> None:
        """Check for case insensitivity in is_new checks."""
        initial_data = ["Owner/Repo1"]
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        service = HistoryService(self.file_path)
        self.assertFalse(service.is_new("owner/repo1"))
        self.assertFalse(service.is_new("OWNER/REPO1"))

    def test_add_new_repos_persists_to_file(self) -> None:
        """Adding new repositories should update the in-memory set and file."""
        service = HistoryService(self.file_path)
        service.add_repos(["owner/repo-a", "owner/repo-b"])

        self.assertEqual(service.get_seen_count(), 2)
        self.assertFalse(service.is_new("owner/repo-a"))

        # Verify file content
        with open(self.file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data, ["owner/repo-a", "owner/repo-b"])

    def test_max_history_limit_enforced(self) -> None:
        """History should prune older entries once max_history_size is reached."""
        # Set max_size to 3
        service = HistoryService(self.file_path, max_history_size=3)
        service.add_repos(["repo1", "repo2", "repo3"])
        
        # This addition should trigger a truncation of the oldest entry ("repo1")
        service.add_repos(["repo4"])

        self.assertEqual(service.get_seen_count(), 3)
        self.assertTrue(service.is_new("repo1"))  # should be pruned
        self.assertFalse(service.is_new("repo4"))  # should exist


if __name__ == "__main__":
    unittest.main()
