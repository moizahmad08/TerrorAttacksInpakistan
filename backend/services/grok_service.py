import httpx
import os
from typing import List, Dict, Tuple, Optional
from dotenv import load_dotenv

from services.response_formatter import format_incidents_markdown, format_statistics_markdown

load_dotenv()

GROK_API_URL = "https://api.x.ai/v1/chat/completions"
GROK_MODEL = "grok-4-1-fast"  # or grok-4-1-fast-reasoning

SYSTEM_PROMPT = """You are an expert intelligence analyst for terrorism incidents in Pakistan.
Answer ONLY from the RETRIEVED KNOWLEDGE BASE CONTEXT. Never invent facts.

RESPONSE FORMAT (use markdown exactly):

## Summary
One or two sentences answering the user's question directly.

## Incidents
For each relevant record use this structure:

### [Number]. [Location] — [Date]
- **Attack type:** ...
- **Target:** ...
- **Perpetrator:** ...
- **Casualties:** **X** killed, **Y** injured
- **Details:** one concise sentence from context
- **Source:** citation from context

## Notes (optional)
Only if needed: limitations, disputed claims, or "not in database".

RULES:
- Bold key numbers and names with **double asterisks**
- Use bullet lists; separate incidents with blank lines
- If context has no match: say so under ## Summary and suggest filters (city, year, group)
- Casualty figures are from reported/official sources in the database
- Do not use emoji; keep a neutral, factual tone"""

class GrokService:
    def __init__(self):
        self.api_key = os.getenv("GROK_API_KEY", "")
        self.client = httpx.AsyncClient(timeout=60.0)

    async def chat(
        self,
        user_message: str,
        context: str,
        history: List[Dict],
        use_reasoning: bool = True,
        intent: str = "general",
        retrieved_docs: Optional[List[Tuple[dict, float]]] = None,
        stats: Optional[dict] = None,
    ) -> str:
        """
        Call Grok API with RAG context injected into the prompt.
        Falls back to context-only response if no API key set.
        """
        
        if not self.api_key or self.api_key == "your_grok_api_key_here":
            return self._fallback_response(
                user_message, context, intent=intent,
                retrieved_docs=retrieved_docs, stats=stats,
            )

        messages = []
        
        # Add history
        for msg in history[-6:]:  # last 6 turns for context window management
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Build the user message with context
        full_user_message = f"""RETRIEVED KNOWLEDGE BASE CONTEXT:
{context}

---
USER QUESTION: {user_message}

Answer based strictly on the context above. If the answer is not in the context, say so clearly."""

        messages.append({"role": "user", "content": full_user_message})

        payload = {
            "model": GROK_MODEL,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            "max_tokens": 1500,
            "temperature": 0.1,  # Low temp for factual accuracy
        }

        if use_reasoning:
            payload["reasoning"] = {"effort": "medium"}

        try:
            response = await self.client.post(
                GROK_API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception:
            return self._fallback_response(
                user_message, context, intent=intent,
                retrieved_docs=retrieved_docs, stats=stats,
            )

    def _fallback_response(
        self,
        query: str,
        context: str,
        intent: str = "general",
        retrieved_docs: Optional[List[Tuple[dict, float]]] = None,
        stats: Optional[dict] = None,
    ) -> str:
        """Demo mode: structured markdown without API call."""
        if intent == "statistics" and stats:
            return format_statistics_markdown(stats, query)

        if retrieved_docs:
            return format_incidents_markdown(retrieved_docs, query)

        if not context or "No relevant" in context:
            return format_incidents_markdown([], query)

        return format_incidents_markdown([], query)

    async def detect_intent(self, message: str) -> str:
        """Lightweight intent detection without API call"""
        msg_lower = message.lower()
        
        if any(w in msg_lower for w in ['how many', 'total', 'count', 'statistics', 'stats']):
            return 'statistics'
        elif any(w in msg_lower for w in ['when', 'date', 'year', 'timeline']):
            return 'temporal'
        elif any(w in msg_lower for w in ['where', 'location', 'city', 'province', 'peshawar', 'karachi', 'quetta', 'lahore']):
            return 'location'
        elif any(w in msg_lower for w in ['who', 'which group', 'claimed', 'perpetrator', 'ttp', 'iskp', 'bla']):
            return 'perpetrator'
        elif any(w in msg_lower for w in ['deadliest', 'worst', 'biggest', 'largest']):
            return 'ranking'
        else:
            return 'general'


grok_service = GrokService()
