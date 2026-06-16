"""Unit tests for the ScraperService."""

import unittest
from src.scraper import ScraperService


class TestScraperService(unittest.TestCase):
    """Verifies that the ScraperService parses GitHub Trending HTML correctly."""

    def setUp(self) -> None:
        """Sets up the scraper service and sample HTML snippets."""
        self.scraper = ScraperService()
        self.mock_html = """
        <article class="Box-row">
          <div class="float-right d-flex">
              <div class="BtnGroup d-flex">
                <a href="/login?return_to=%2Fiptv-org%2Fiptv" class="btn">Star</a>
              </div>
          </div>
          <h2 class="h3 lh-condensed">
            <a href="/iptv-org/iptv" class="Link">
              <span class="text-normal">iptv-org /</span> iptv
            </a>
          </h2>
          <p class="col-9 color-fg-muted my-1 tmp-pr-4">
            Collection of publicly available IPTV channels from all over the world
          </p>
          <div class="f6 color-fg-muted mt-2">
              <span class="tmp-mr-3 d-inline-block">
                <span class="repo-language-color" style="background-color: #3178c6"></span>
                <span itemprop="programmingLanguage">TypeScript</span>
              </span>
              <a href="/iptv-org/iptv/stargazers" class="Link">122,936</a>
              <span class="d-inline-block float-sm-right">
                2,657 stars today
              </span>
          </div>
        </article>
        """

    def test_parse_trending_success(self) -> None:
        """Should parse a single valid repository block correctly."""
        repos = self.scraper.parse_trending(self.mock_html)
        self.assertEqual(len(repos), 1)

        repo = repos[0]
        self.assertEqual(repo.repo, "iptv-org/iptv")
        self.assertEqual(repo.desc, "Collection of publicly available IPTV channels from all over the world")
        self.assertEqual(repo.lang, "TypeScript")
        self.assertEqual(repo.stars, "122,936")
        self.assertEqual(repo.today_stars, "2,657")
        self.assertEqual(repo.url, "https://github.com/iptv-org/iptv")

    def test_parse_trending_empty_html(self) -> None:
        """Parsing an empty HTML string or unrelated HTML should return an empty list."""
        repos = self.scraper.parse_trending("<html><body><h1>No repos here</h1></body></html>")
        self.assertEqual(len(repos), 0)


if __name__ == "__main__":
    unittest.main()
