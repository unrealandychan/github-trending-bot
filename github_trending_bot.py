#!/usr/bin/env python3
"""CLI entrypoint for the GitHub Trending Bot.

This script parses arguments, configures logging, loads configuration,
and executes the coordinator to run the automated trending process.
"""

import argparse
import logging
import sys
from src.config import Config, ConfigurationError
from src.coordinator import TrendingCoordinator

# Configure logging to go to stdout/stderr with readable formatting
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("github_trending_bot")


def parse_arguments() -> argparse.Namespace:
    """Parses command-line arguments.

    Returns:
        argparse.Namespace containing parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Daily GitHub Trending Bot — Auto Scraper, LLM Summarizer & Notion Publisher"
    )
    parser.add_argument(
        "--dotenv",
        type=str,
        default=None,
        help="Optional path to custom .env file (defaults to local .env or ~/.hermes/.env)"
    )
    parser.add_argument(
        "--max-repos",
        type=int,
        default=10,
        help="Maximum number of new trending repositories to recommend (default: 10)"
    )
    parser.add_argument(
        "--since",
        type=str,
        choices=["daily", "weekly", "monthly"],
        default="daily",
        help="GitHub trending period (default: daily)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable fine-grained debug logging output"
    )
    return parser.parse_args()


def main() -> None:
    """Main execution function."""
    args = parse_arguments()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled.")

    logger.info("Initializing GitHub Trending Bot...")

    try:
        # Load and validate configs
        config = Config(dotenv_path=args.dotenv)
        config.validate_core()

        # Instantiate and run coordinator
        coordinator = TrendingCoordinator(config)
        notion_url = coordinator.run(max_repos=args.max_repos, since=args.since)

        if notion_url:
            logger.info("Bot execution completed successfully! Notion URL: %s", notion_url)
        else:
            logger.info("Bot execution completed (No new repositories recommended today or Notion skip).")

    except ConfigurationError as ce:
        logger.error("Configuration Validation Failed: %s", ce)
        sys.exit(1)
    except Exception as e:
        logger.critical("An unexpected error occurred during execution: %s", e, exc_info=args.debug)
        sys.exit(1)


if __name__ == "__main__":
    main()
