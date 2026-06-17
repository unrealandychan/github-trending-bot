---
name: github-trending-daily
description: "Use when scheduling or executing the daily automated GitHub Trending analysis. Scrapes trending repositories, performs history deduplication, enriches with Tavily context, and publishes a structured multi-language (default English) report to Notion and alerts Telegram."
version: 1.1.0
author: Eddie & Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [github, trending, cron, notion, telegram, english, multilingual, automation]
    related_skills: [cronjob-deduplication, github-repo-management]
---

# Daily GitHub Trending Automation Skill

## Overview
This skill provides structured procedures, instructions, and workflows to configure, schedule, and execute the modular **Daily GitHub Trending Bot** repository. This bot scrapes GitHub Trending (`https://github.com/trending`) daily, performs a history deduplication check against already seen projects, enriches new projects with Tavily search context, and calls an LLM (Gemini or OpenAI) to compile a sharp, professional technical report in any target language (such as English, Traditional Chinese, or conversational Hong Kong Cantonese). The resulting report is published as a new page in a Notion database and can be pushed to Telegram.

---

## When to Use
- **Scheduling Daily Updates:** Automatically compile GitHub trending repos every Monday–Friday morning.
- **Reporting & Broadcasting:** Send formatted, high-value technical briefs to developers, team chats, or personal Notion boards in your preferred language.
- **Deduplicated Scanning:** Keep track of trending AI/Open Source tools without seeing repetitive entries.

---

## 🚀 Execution & Configuration Guide

The bot is implemented in a modular Python structure under this repository.

### 1. Requirements & Setup
Ensure python3 and `python-dotenv` are available:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment Configurations
Copy `.env.example` to `.env` and fill in the required variables:
```bash
cp .env.example .env
```

Ensure the following variables are specified:
- `NOTION_API_KEY`: Your Notion integration token (`ntn_...`).
- `NOTION_DATABASE_ID`: The Notion database ID.
- `TAVILY_API_KEY`: Tavily Search Key (for online project context retrieval).
- `LLM_PROVIDER`: `gemini` or `openai`.
- `GEMINI_API_KEY` or `OPENAI_API_KEY`: API authentication for your chosen LLM.
- `REPORT_LANGUAGE`: Set your preferred language (e.g., `English`, `Traditional Chinese`, or `Cantonese`). Default is `English`.
- `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`: Credentials to broadcast alerts to Telegram.

---

## 🛠️ Execution Recipes

### One-Shot Manual Run
To execute the pipeline immediately (runs a daily scrape, recommends up to 10 unseen repos, and logs output):
```bash
python3 github_trending_bot.py
```

### Enable Debug Mode
To inspect detailed logs, network connections, or LLM payloads:
```bash
python3 github_trending_bot.py --debug
```

### Weekly or Monthly Scrape
To check what has been trending over a longer period (e.g., weekly):
```bash
python3 github_trending_bot.py --since weekly --max-repos 8
```

---

## ⏰ Scheduling with Hermes Cron
You can schedule this skill to run autonomously inside Hermes Agent using the `cronjob` tool.

### To Create the Cron Job:
Run the following tool command or prompt Hermes to schedule:
```json
{
  "action": "create",
  "schedule": "0 3 * * 1-5",
  "name": "📊 GitHub Trending Daily",
  "prompt": "Run the daily GitHub Trending Bot to scrape trending projects, summarize them, publish to Notion, and send to Telegram.",
  "script": "github_trending_bot.py",
  "workdir": "/home/ubuntu/github-trending-bot"
}
```
*Note: `0 3 * * 1-5` matches 03:00 UTC (11:00 AM HKT) on weekdays (Mon-Fri).*

---

## ⚠️ Common Pitfalls & Solutions

1. **Notion API blocks are empty or fail to write:**
   * **Cause:** Large reports can exceed Notion's API block limit if sent all at once.
   * **Solution:** The `NotionService` in this repository automatically chunks block payloads into batches of 50 to prevent size limit rejects.

2. **Characters rendering incorrectly (Unicode leaks):**
   * **Cause:** Writing JSON files without proper encoding overrides.
   * **Solution:** Standardize python IO operations with `encoding="utf-8"` and always pass `ensure_ascii=False` when calling `json.dumps` to write or call HTTP APIs.

3. **Duplicated Repositories recommended across consecutive days:**
   * **Cause:** The scraper checks the top trending page which doesn't change completely every day.
   * **Solution:** A local `github_trending_history.json` is maintained to filter out previously seen repositories (retaining up to 600 items).

---

## ✅ Verification Checklist
- [ ] Run `python3 github_trending_bot.py --debug` and verify that no API calls fail with `401` or `403`.
- [ ] Verify that a new page is successfully created in your Notion Database.
- [ ] Open the newly created Notion page and check that all child blocks (Callouts, Paragraphs, Dividers) are fully written in your target `REPORT_LANGUAGE`.
- [ ] Confirm that your local `github_trending_history.json` file is populated with recommended repo names.
- [ ] Confirm that the final Telegram message successfully delivers (if configured).
