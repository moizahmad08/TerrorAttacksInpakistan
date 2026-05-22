import httpx
import os
import logging
from typing import List, Dict, Tuple, Optional
from dotenv import load_dotenv

from services.response_formatter import format_agent_fallback

load_dotenv()
logger = logging.getLogger(__name__)

GROK_API_URL = "https://api.x.ai/v1/chat/completions"
GROK_MODEL = os.getenv("GROK_MODEL", "grok-4-1-fast-reasoning")

SYSTEM_PROMPT = """You are an intelligence research assistant for terrorism incidents in Pakistan.
The system has ALREADY searched a database of 1,700+ attacks and provided matching records below.

YOUR JOB:
1. Read the user's question and the DATABASE SEARCH RESULTS.
2. Answer in clear, natural language — explain, summarize, compare, or describe specific attacks.
3. Use ONLY facts from the search results. Never invent dates, locations, death tolls, or group names.
4. If the user asks about a specific attack, describe what happened using the best matching record(s).
5. If results are weak or empty, say what you could not find and suggest a clearer question (city, year, group).

STYLE:
- Start with a direct answer (## Summary or opening paragraph).
- Then give details; use markdown headings and bullets when listing multiple incidents.
- Bold important numbers and names with **double asterisks**.
- Be conversational and helpful, not a raw database dump.
- No emoji."""


class GrokService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=120.0)

    def _get_api_key(self) -> str:
        return (os.getenv("GROK_API_KEY") or "").strip()

    def is_configured(self) -> bool:
        key = self._get_api_key()
        return bool(key and key != "your_grok_api_key_here")

    async def _call_grok(self, messages: List[Dict]) -> str:
        api_key = self._get_api_key()
        payload = {
            "model": GROK_MODEL,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            "max_tokens": 2000,
            "temperature": 0.3,
        }

        # Reasoning model: enable effort when using grok-4-1-fast-reasoning
        if "reasoning" in GROK_MODEL.lower():
            payload["reasoning"] = {"effort": "medium"}

        response = await self.client.post(
            GROK_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        if response.status_code >= 400:
            logger.error("Grok API %s: %s", response.status_code, response.text[:400])
            # Retry without reasoning if API rejects the field
            if "reasoning" in payload:
                del payload["reasoning"]
                response = await self.client.post(
                    GROK_API_URL,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                if response.status_code >= 400:
                    logger.error("Grok retry %s: %s", response.status_code, response.text[:400])
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    async def chat(
        self,
        user_message: str,
        context: str,
        history: List[Dict],
        intent: str = "general",
        retrieved_docs: Optional[List[Tuple[dict, float]]] = None,
        stats: Optional[dict] = None,
    ) -> Tuple[str, str]:
        if self.is_configured():
            messages = []
            for msg in history[-8:]:
                messages.append({"role": msg["role"], "content": msg["content"]})

            search_note = (
                f"{len(retrieved_docs)} record(s) found."
                if retrieved_docs
                else "No matching records found."
            )

            user_prompt = f"""DATABASE SEARCH RESULTS ({search_note}):
{context}

---
USER QUESTION: {user_message}

Search the results above, then answer the user's question in natural language."""

            messages.append({"role": "user", "content": user_prompt})

            try:
                answer = await self._call_grok(messages)
                return answer, "ai"
            except Exception as e:
                logger.error("Grok failed, using database agent fallback: %s", e)

        fallback = format_agent_fallback(
            user_message,
            retrieved_docs or [],
            stats=stats,
            intent=intent,
        )
        return fallback, "database"

    async def detect_intent(self, message: str) -> str:
        msg_lower = message.lower()

        if any(w in msg_lower for w in ["how many", "total", "count", "statistics", "stats"]):
            return "statistics"
        if any(w in msg_lower for w in ["when", "date", "year", "timeline", "recent", "latest"]):
            return "temporal"
        if any(
            w in msg_lower
            for w in [
                "where", "location", "city", "province",
                "peshawar", "karachi", "quetta", "lahore", "islamabad", "balochistan",
            ]
        ):
            return "location"
        if any(
            w in msg_lower
            for w in ["who", "which group", "claimed", "perpetrator", "ttp", "iskp", "bla", "taliban"]
        ):
            return "perpetrator"
        if any(
            w in msg_lower
            for w in ["deadliest", "worst", "biggest", "largest", "most deadly", "highest death"]
        ):
            return "ranking"
        if any(w in msg_lower for w in ["tell me about", "what happened", "describe", "explain", "attack on", "attack in"]):
            return "incident"
        return "general"


grok_service = GrokService()
