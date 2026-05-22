from typing import List, Dict, Tuple
import re
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.attacks_db import ATTACKS_DATA

# Common query terms → help retrieval
LOCATION_ALIASES = {
    "kpk": "khyber",
    "kp": "khyber",
    "fata": "waziristan",
    "ict": "islamabad",
    "ajk": "kashmir",
    "aka": "karachi",
}

STOP_WORDS = {
    "the", "a", "an", "in", "on", "at", "of", "and", "or", "to", "is", "was", "were",
    "are", "be", "been", "by", "for", "with", "this", "that", "it", "as", "from",
    "what", "who", "when", "where", "how", "did", "do", "does", "tell", "me", "about",
    "any", "attack", "attacks", "happened", "there", "have", "been", "many", "much",
}


class RAGService:
    """Search the attack database, then pass results to the AI agent."""

    def __init__(self):
        self.refresh()

    def refresh(self):
        self.documents = ATTACKS_DATA
        self.doc_texts = [self._build_doc_text(d) for d in self.documents]

    def _build_doc_text(self, doc: dict) -> str:
        return (
            f"{doc['id']} {doc['date']} {doc['location']} {doc['province']} "
            f"{doc['attack_type']} {doc['target']} {doc['perpetrator']} "
            f"{doc['description']} deaths:{doc['deaths']} injuries:{doc['injuries']}"
        ).lower()

    def _tokenize(self, text: str) -> List[str]:
        tokens = re.findall(r"\b\w+\b", text.lower())
        expanded = []
        for t in tokens:
            expanded.append(t)
            if t in LOCATION_ALIASES:
                expanded.append(LOCATION_ALIASES[t])
        return expanded

    def _query_tokens(self, query: str) -> set:
        return set(self._tokenize(query)) - STOP_WORDS

    def _extract_years(self, query: str) -> List[str]:
        return re.findall(r"\b(19|20)\d{2}\b", query)

    def _score_document(self, query_tokens: set, doc_text: str, query: str) -> float:
        if not query_tokens:
            return 0.0

        doc_token_set = set(self._tokenize(doc_text))
        matches = query_tokens & doc_token_set
        if not matches:
            # Substring match for longer words (e.g. peshawar in location)
            for token in query_tokens:
                if len(token) >= 4 and token in doc_text:
                    matches.add(token)
            if not matches:
                return 0.0

        base_score = len(matches) / len(query_tokens)

        boost = 0.0
        for year in self._extract_years(query):
            if year in doc_text:
                boost += 0.35
        for token in query_tokens:
            if len(token) >= 5 and token in doc_text:
                boost += 0.15

        return min(base_score + boost, 1.0)

    def retrieve(
        self, query: str, top_k: int = 8, filters: dict = None, min_score: float = 0.12
    ) -> List[Tuple[dict, float]]:
        query_tokens = self._query_tokens(query)
        years = self._extract_years(query)
        scores = []

        for i, doc in enumerate(self.documents):
            if filters:
                if filters.get("province") and filters["province"].lower() not in doc["province"].lower():
                    continue
                if filters.get("year") and not doc["date"].startswith(str(filters["year"])):
                    continue
                if filters.get("perpetrator") and filters["perpetrator"].lower() not in doc["perpetrator"].lower():
                    continue

            score = self._score_document(query_tokens, self.doc_texts[i], query)

            # Year-only queries: include all attacks from that year
            if years and any(doc["date"].startswith(y) for y in years):
                score = max(score, 0.5)

            if score >= min_score:
                scores.append((doc, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        results = scores[:top_k]

        if not results and query_tokens:
            return self.retrieve(query, top_k=top_k, filters=filters, min_score=0.05)

        return results

    def search_for_agent(self, query: str, intent: str) -> List[Tuple[dict, float]]:
        """Intent-aware database search before the agent responds."""
        top_k = {
            "statistics": 5,
            "ranking": 10,
            "incident": 8,
            "general": 8,
            "temporal": 8,
            "location": 10,
            "perpetrator": 10,
        }.get(intent, 8)

        results = self.retrieve(query, top_k=top_k)

        if intent == "ranking":
            deadliest = sorted(self.documents, key=lambda x: x["deaths"], reverse=True)[:10]
            seen = {d["id"] for d, _ in results}
            for doc in deadliest:
                if doc["id"] not in seen:
                    results.append((doc, 1.0))
                    seen.add(doc["id"])

        return results[:top_k]

    def build_context(self, retrieved: List[Tuple[dict, float]]) -> str:
        if not retrieved:
            return "DATABASE SEARCH: No matching attack records found."

        context_parts = [
            f"DATABASE SEARCH: Found {len(retrieved)} record(s).\n",
        ]
        for doc, score in retrieved:
            context_parts.append(
                f"--- RECORD (relevance {score:.2f}) ---\n"
                f"ID: {doc['id']}\n"
                f"Date: {doc['date']}\n"
                f"Location: {doc['location']}, {doc['province']}\n"
                f"Attack Type: {doc['attack_type']}\n"
                f"Target: {doc['target']}\n"
                f"Perpetrator: {doc['perpetrator']}\n"
                f"Deaths: {doc['deaths']}\n"
                f"Injuries: {doc['injuries']}\n"
                f"Description: {doc['description']}\n"
                f"Source: {doc['source']}\n"
            )

        return "\n".join(context_parts)

    def get_stats(self) -> dict:
        total_deaths = sum(d["deaths"] for d in self.documents)
        total_injuries = sum(d["injuries"] for d in self.documents)
        provinces = {}
        perpetrators = {}
        years = {}

        for d in self.documents:
            provinces[d["province"]] = provinces.get(d["province"], 0) + 1
            perp = d["perpetrator"]
            perpetrators[perp] = perpetrators.get(perp, 0) + 1
            year = d["date"][:4]
            years[year] = years.get(year, 0) + 1

        return {
            "total_incidents": len(self.documents),
            "total_deaths": total_deaths,
            "total_injuries": total_injuries,
            "by_province": provinces,
            "by_perpetrator": perpetrators,
            "by_year": years,
        }


rag_service = RAGService()
