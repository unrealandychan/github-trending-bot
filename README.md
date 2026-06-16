# 📊 Daily GitHub Trending Bot

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)

An elegant, robust, and modular automated agent that scrapes **GitHub Trending** repositories daily, performs history-based deduplication, enriches discoveries with web context via **Tavily Search**, summarizes them with **Google Gemini** or **OpenAI**, and publishes a sharp, professional technical report in **conversational Hong Kong Cantonese (廣東話口語)** to your **Notion Database** and **Telegram**.

Tailored for AI Engineers, Tech Investors, and solo Podcast creators who want to keep track of high-value open-source trends daily.

---

## ✨ Features

- 🐙 **Zero-Dependency Scraper:** Fetches and parses GitHub Trending directly using Python standard libraries — robust, extremely fast, and free of BeautifulSoup/Playwright overhead.
- 💡 **Dual-Source Deep Enrichment:** Combines raw repository data with online context from **Tavily Search** to understand *why* a repository is trending.
- 🗣️ **Conversational Cantonese Output:** Automatically synthesizes witty, engaging, and professional Cantonese reviews via LLMs while keeping technical terms (such as *LLM, agent, framework, sandbox*) in standard English.
- 📑 **Notion Database Publisher:** Employs a robust **two-step write pattern** (Create metadata page -> append block body) with safe CJK/UTF-8 encoding support and API payload chunking (blocks split into chunks of 50) to prevent Notion rejects.
- 🗃️ **Smart Deduplication:** Keeps track of historically recommended projects in `github_trending_history.json` (holds up to 600 items/roughly 2 months) so your daily reports never feel repetitive.
- 🔔 **Telegram Broadcasting:** Delivers clean HTML summaries with inline repo URLs and direct links to your Notion workspace.

---

## 📂 Repository Structure

Conforming to **Domain-Driven Design (DDD)** and **Clean Code** principles:

```
github-trending-bot/
├── .env.example              # Template for private API credentials
├── .gitignore                # Git untracked pattern file
├── requirements.txt          # Python dependencies (python-dotenv only!)
├── github_trending_bot.py    # Main CLI executable entry point
├── SKILL.md                  # Hermes-Agent reusable skill file
└── src/                      # Core domain package
    ├── __init__.py           # Package version definition
    ├── config.py             # Handles loading and validating environment variables
    ├── models.py             # Defines dataclasses: Repository, TrendReport
    ├── scraper.py            # Zero-dependency ScraperService (pure urllib/re)
    ├── history.py            # HistoryService to track and persist seen projects
    ├── llm.py                # LLMService (Gemini/OpenAI) & TavilyService
    ├── notion.py             # NotionService with chunked block writing
    └── telegram.py           # TelegramService for HTML summary broadcasting
```

---

## 🚀 Getting Started

### 1. Prerequisites & Installation

Clone this repository and set up a clean Python virtual environment:

```bash
git clone https://github.com/unrealandychan/github-trending-bot.git
cd github-trending-bot

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the environment template and fill in your private API tokens:

```bash
cp .env.example .env
```

Open `.env` and configure:
```ini
NOTION_API_KEY=ntn_your_notion_integration_secret
NOTION_DATABASE_ID=your_notion_database_uuid_here

TAVILY_API_KEY=your_tavily_api_key_here

# Choose 'gemini' (preferred default) or 'openai'
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
```

*Note: If you want to enable Telegram alerts, make sure to add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` too.*

### 3. Usage & CLI Command Recipes

Execute the pipeline immediately using the CLI:

```bash
# Run the standard daily trending loop
python3 github_trending_bot.py

# Run in debug mode (highly detailed network/parsing/LLM outputs)
python3 github_trending_bot.py --debug

# Pull weekly trending projects instead of daily
python3 github_trending_bot.py --since weekly --max-repos 8
```

---

## ⏰ Scheduling Automation (Cron)

### Standard Linux Crontab
To run the bot automatically every weekday at 11:00 AM HKT (03:00 UTC), add this entry to your crontab (`crontab -e`):

```cron
0 3 * * 1-5 /absolute/path/to/venv/bin/python3 /absolute/path/to/github_trending_bot.py >> /var/log/github_trending_bot.log 2>&1
```

### Hermes Agent Cron
If you are running this with a Hermes Agent, configure a scheduled job in your `cronjob` configuration:

```json
{
  "action": "create",
  "schedule": "0 3 * * 1-5",
  "name": "📊 GitHub Trending 日報",
  "prompt": "Run the daily GitHub Trending Bot to scrape trending projects, summarize them in Cantonese, publish to Notion, and send to Telegram.",
  "script": "github_trending_bot.py",
  "workdir": "/home/ubuntu/github-trending-bot"
}
```

---

## 🤝 Contributing & Standards

This project maintains rigorous coding standards:
- **Clean Code & DDD:** Single-responsibility services, clear boundary separation, zero standard `print()` calls (relying on Python standard `logging`), and no global mutation patterns.
- **Type Safety:** 100% complete type hinting on all public class interfaces, method signatures, and variables.
- **Google Style Docstrings:** Comprehensive docstrings on all modules, classes, and helper routines.

---

## 📄 License

This repository is licensed under the **MIT License**. See the `LICENSE` file for details (or standard MIT boilerplate).
