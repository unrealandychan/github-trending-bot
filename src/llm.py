"""LLM and Tavily Search integration services.

This module provides programmatic access to Gemini and OpenAI API endpoints
for Cantonese report generation, and Tavily API for background research.
Uses only standard python libraries (urllib) to avoid third-party dependencies.
"""

import json
import logging
import urllib.request
from typing import Dict, Any, List, Optional
from src.models import Repository

# Setup logger for llm module
logger = logging.getLogger(__name__)


class APIError(Exception):
    """Raised when an API request to a search provider or LLM fails."""
    pass


class TavilyService:
    """Service to interact with the Tavily Search API for background research."""

    API_URL = "https://api.tavily.com/search"

    def __init__(self, api_key: str) -> None:
        """Initializes the Tavily Search client.

        Args:
            api_key: The Tavily API secret key.
        """
        self.api_key = api_key

    def search_repo_context(self, repo_name: str) -> str:
        """Searches Tavily for deep context about a specific repository.

        Args:
            repo_name: Full repository name (e.g. 'owner/repo').

        Returns:
            A consolidated string of search results or an empty string.
        """
        if not self.api_key:
            logger.debug("Tavily API key not configured. Skipping online search for %s.", repo_name)
            return ""

        query = f"github {repo_name} open source project summary what it is why it is trending"
        logger.info("Searching Tavily for repo context: %s...", repo_name)

        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "basic",
            "max_results": 3,
            "include_domains": ["github.com", "github.blog", "medium.com", "dev.to", "reddit.com"]
        }

        try:
            body = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self.API_URL,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))
                
                results_list = result.get("results", [])
                if not results_list:
                    logger.debug("No search results returned for %s.", repo_name)
                    return ""

                context_blocks = []
                for idx, r in enumerate(results_list, 1):
                    title = r.get("title", "Untitled")
                    content = r.get("content", "")
                    url = r.get("url", "")
                    context_blocks.append(f"[{idx}] Title: {title}\nURL: {url}\nContent: {content}\n")
                
                return "\n".join(context_blocks)

        except Exception as e:
            logger.warning("Tavily search failed for %s: %s. Continuing with default data.", repo_name, e)
            return ""


class LLMService:
    """Service to handle generating summaries and analyses in Cantonese."""

    def __init__(
        self,
        provider: str,
        api_key: str,
        model_name: Optional[str] = None
    ) -> None:
        """Initializes the LLM integration.

        Args:
            provider: Either 'gemini' or 'openai'.
            api_key: The matching API key.
            model_name: Overrides the default model if provided.
        """
        self.provider = provider.lower()
        self.api_key = api_key
        
        if self.provider == "gemini":
            self.model_name = model_name or "gemini-2.5-flash"
        else:
            self.model_name = model_name or "gpt-4o"

    def _call_gemini(self, system_prompt: str, user_prompt: str) -> str:
        """Executes a Gemini generation call using pure urllib.request.

        Args:
            system_prompt: System behavior instructions.
            user_prompt: The main query prompt.

        Returns:
            The raw text completion from Gemini.
        """
        # Gemini 1.5/2.5 API structure
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        
        # We supply system instruction if supported
        payload = {
            "contents": [
                {
                    "parts": [{"text": user_prompt}]
                }
            ],
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 4096
            }
        }

        try:
            body = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
                # Path to text: candidates[0].content.parts[0].text
                candidates = result.get("candidates", [])
                if not candidates:
                    raise APIError("No candidates returned from Gemini.")
                
                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts:
                    raise APIError("No text parts returned from Gemini.")
                
                return str(parts[0].get("text", "")).strip()

        except Exception as e:
            logger.error("Gemini API request failed: %s", e)
            raise APIError(f"Gemini generation failed: {e}") from e

    def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        """Executes an OpenAI Chat Completion call using pure urllib.request.

        Args:
            system_prompt: System behavior instructions.
            user_prompt: The main query prompt.

        Returns:
            The raw text completion from OpenAI.
        """
        url = "https://api.openai.com/v1/chat/completions"
        
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 3000
        }

        try:
            body = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
                choices = result.get("choices", [])
                if not choices:
                    raise APIError("No choices returned from OpenAI.")
                
                return str(choices[0].get("message", {}).get("content", "")).strip()

        except Exception as e:
            logger.error("OpenAI API request failed: %s", e)
            raise APIError(f"OpenAI generation failed: {e}") from e

    def generate_report_content(self, date_str: str, repos: List[Repository]) -> Dict[str, Any]:
        """Sends the trending repos and context to the LLM to generate analysis.

        Args:
            date_str: Date of the report.
            repos: List of filtered trending Repository objects (already with search context).

        Returns:
            A dictionary containing:
                - 'theme_summary': Cantonese overview of today's trend.
                - 'main_theme': Short English/Chinese main topic.
                - 'repos': Dict mapping repo name to Cantonese 'why_it_matters'.
        """
        logger.info("Requesting Cantonese analysis and summary from %s model...", self.provider)
        
        # Prepare structured repo context for prompt
        repos_data = []
        for r in repos:
            repo_block = {
                "repo": r.repo,
                "desc": r.desc,
                "lang": r.lang,
                "stars": r.stars,
                "today_stars": r.today_stars,
                "online_context": r.context_analysis or "No online context found."
            }
            repos_data.append(repo_block)

        system_prompt = (
            "You are a GitHub Trending Analyst helping Eddie, a tech-investing AI Engineer "
            "from Hong Kong. Your job is to analyze the daily GitHub trending repositories and "
            "provide a sharp, professional, yet witty and engaging report.\n\n"
            "CRITICAL RULES:\n"
            "1. You MUST respond ONLY in valid JSON format. Do not wrap inside ```json...``` markdown.\n"
            "2. All explanations and analysis MUST be written in conversational Hong Kong Cantonese (廣東話口語, "
            "e.g., 用「佢地」、「呢個」、「搞掂」而唔係「他們」、「這個」、「搞定」), keeping technical terms (such as "
            "LLM, agent, framework, sandbox, dataset, fine-tune, RAG) in English.\n"
            "3. The output JSON must have exactly this keys structure:\n"
            "{\n"
            "  \"main_theme\": \"A short description of today's primary trend (max 10 words, e.g., 'AI Agents 與 MCP 生態爆發')\",\n"
            "  \"theme_summary\": \"A rich 3-5 sentence Cantonese paragraph summarizing today's key trends across these repos.\",\n"
            "  \"repos_why_it_matters\": {\n"
            "    \"owner/repo1\": \"A short 2-3 sentence Cantonese explanation of what this repo does and why it is historically/technically significant today.\"\n"
            "  }\n"
            "}"
        )

        user_prompt = (
            f"Here are today's trending repositories on GitHub for {date_str}. "
            "Please analyze them and fill out the JSON schema. Use the provided online context "
            "to make your explanations incredibly accurate, deep, and contextual.\n\n"
            f"Repositories:\n{json.dumps(repos_data, indent=2, ensure_ascii=False)}"
        )

        raw_response = ""
        if self.provider == "gemini":
            raw_response = self._call_gemini(system_prompt, user_prompt)
        else:
            raw_response = self._call_openai(system_prompt, user_prompt)

        # Handle potential markdown wrapping
        if raw_response.startswith("```"):
            # Strip first line
            lines = raw_response.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            raw_response = "\n".join(lines).strip()

        try:
            parsed_res = json.loads(raw_response)
            logger.info("Successfully received and parsed JSON from LLM.")
            return parsed_res
        except Exception as e:
            logger.error("LLM failed to output valid JSON. Raw response length: %d. Error: %s", len(raw_response), e)
            logger.debug("Raw invalid LLM response: %s", raw_response)
            
            # Fail-safe mock generation if JSON parse fails
            return {
                "main_theme": "GitHub Open Source Projects",
                "theme_summary": "今日 GitHub Trending 呈現出多元開發趨勢，特別係 AI 基建與工具類別有大量開發者關注。 (由於 LLM JSON 解析失敗，此處為自動備份總結。)",
                "repos_why_it_matters": {r.repo: f"呢個項目係一個好實用嘅 {r.lang} 開源工具，今日有額外 {r.today_stars} 位開發者標星，好值得跟進佢嘅發展。" for r in repos}
            }
