import httpx
import os
from typing import List, Dict, Optional
import json
from dotenv import load_dotenv

load_dotenv()

GROK_API_URL = "https://api.x.ai/v1/chat/completions"
GROK_MODEL = "grok-4-1-fast"  # or grok-4-1-fast-reasoning

SYSTEM_PROMPT = """You are an expert intelligence analyst specializing in terrorism incidents in Pakistan. 
You have access to a structured database of terror attacks.

Your role is to:
1. Answer questions accurately using ONLY the provided context documents
2. Always cite the date, location, and source for each attack you mention
3. Clearly distinguish between confirmed facts and disputed claims
4. If asked about something NOT in the context, say: "This incident is not in my current knowledge base."
5. For casualty figures, always state they are from official/reported sources
6. Present information in a clear, factual, journalist-style format
7. When listing multiple attacks, format them clearly with dates and locations
8. Never speculate or fabricate details not present in the context

Format guidelines:
- Use bullet points for lists of attacks
- Bold important figures (deaths, dates, group names) using **text**
- Always end with the source citation

Remember: You are an informational resource, not an advocate for any position."""

class GrokService:
    def __init__(self):
        self.api_key = os.getenv("GROK_API_KEY", "")
        self.client = httpx.AsyncClient(timeout=60.0)

    async def chat(
        self, 
        user_message: str, 
        context: str, 
        history: List[Dict],
        use_reasoning: bool = True
    ) -> str:
        """
        Call Grok API with RAG context injected into the prompt.
        Falls back to context-only response if no API key set.
        """
        
        if not self.api_key or self.api_key == "your_grok_api_key_here":
            return self._fallback_response(user_message, context)

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
        except Exception as e:
            return self._fallback_response(user_message, context)

    def _fallback_response(self, query: str, context: str) -> str:
        """
        Demo mode: Returns structured context without API call.
        Used when no API key is configured.
        """
        if not context or "No relevant" in context:
            return (
                "I couldn't find specific records matching your query in the database. "
                "Try searching by location (e.g., Peshawar, Karachi), year (e.g., 2014), "
                "or group (e.g., TTP, ISKP)."
            )
        
        lines = context.split('\n')
        response_parts = ["Based on the knowledge base, here is what I found:\n"]
        
        current_record = {}
        for line in lines:
            if line.startswith('Date:'):
                current_record['date'] = line.replace('Date:', '').strip()
            elif line.startswith('Location:'):
                current_record['location'] = line.replace('Location:', '').strip()
            elif line.startswith('Perpetrator:'):
                current_record['perp'] = line.replace('Perpetrator:', '').strip()
            elif line.startswith('Deaths:'):
                current_record['deaths'] = line.replace('Deaths:', '').strip()
            elif line.startswith('Description:'):
                current_record['desc'] = line.replace('Description:', '').strip()
            elif line.startswith('---') and current_record:
                if current_record.get('date'):
                    response_parts.append(
                        f"**{current_record.get('date', 'N/A')}** — {current_record.get('location', 'N/A')}\n"
                        f"Perpetrator: {current_record.get('perp', 'Unknown')}\n"
                        f"Deaths: **{current_record.get('deaths', '?')}**\n"
                        f"{current_record.get('desc', '')}\n"
                    )
                current_record = {}
        
        if current_record.get('date'):
            response_parts.append(
                f"**{current_record.get('date', 'N/A')}** — {current_record.get('location', 'N/A')}\n"
                f"Perpetrator: {current_record.get('perp', 'Unknown')}\n"
                f"Deaths: **{current_record.get('deaths', '?')}**\n"
                f"{current_record.get('desc', '')}\n"
            )
        
        response_parts.append("\n*Note: Add your GROK_API_KEY to .env for AI-powered natural language responses.*")
        return "\n".join(response_parts)

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
