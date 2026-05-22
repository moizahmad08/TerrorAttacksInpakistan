from typing import List, Dict, Tuple
import re
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.attacks_db import ATTACKS_DATA

class RAGService:
    """
    Lightweight RAG service using TF-IDF style keyword matching + BM25-like scoring.
    No heavy ML dependencies required — works out of the box.
    For production, swap _score_document() with sentence-transformers embeddings.
    """

    def __init__(self):
        self.documents = ATTACKS_DATA
        self.doc_texts = [self._build_doc_text(d) for d in self.documents]

    def _build_doc_text(self, doc: dict) -> str:
        return (
            f"{doc['date']} {doc['location']} {doc['province']} "
            f"{doc['attack_type']} {doc['target']} {doc['perpetrator']} "
            f"{doc['description']} deaths:{doc['deaths']} injuries:{doc['injuries']}"
        ).lower()

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r'\b\w+\b', text.lower())

    def _score_document(self, query: str, doc_text: str) -> float:
        query_tokens = set(self._tokenize(query))
        doc_tokens = self._tokenize(doc_text)
        doc_token_set = set(doc_tokens)
        
        # Stop words to ignore
        stop_words = {'the', 'a', 'an', 'in', 'on', 'at', 'of', 'and', 'or', 
                      'to', 'is', 'was', 'were', 'are', 'be', 'been', 'by', 
                      'for', 'with', 'this', 'that', 'it', 'as', 'from', 'what',
                      'who', 'when', 'where', 'how', 'did', 'do', 'does'}
        
        query_tokens = query_tokens - stop_words
        
        if not query_tokens:
            return 0.0
        
        matches = query_tokens & doc_token_set
        base_score = len(matches) / len(query_tokens)
        
        # Boost for key field matches
        boost = 0.0
        for token in query_tokens:
            if token in doc_text[:100]:  # date/location area
                boost += 0.3
        
        return min(base_score + boost, 1.0)

    def retrieve(self, query: str, top_k: int = 5, filters: dict = None) -> List[Tuple[dict, float]]:
        scores = []
        for i, doc in enumerate(self.documents):
            # Apply filters
            if filters:
                if filters.get('province') and filters['province'].lower() not in doc['province'].lower():
                    continue
                if filters.get('year') and str(filters['year']) not in doc['date']:
                    continue
                if filters.get('perpetrator') and filters['perpetrator'].lower() not in doc['perpetrator'].lower():
                    continue
            
            score = self._score_document(query, self.doc_texts[i])
            if score > 0:
                scores.append((doc, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def build_context(self, retrieved: List[Tuple[dict, float]]) -> str:
        if not retrieved:
            return "No relevant attack records found in the database."
        
        context_parts = []
        for doc, score in retrieved:
            context_parts.append(
                f"--- ATTACK RECORD ---\n"
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
        total_deaths = sum(d['deaths'] for d in self.documents)
        total_injuries = sum(d['injuries'] for d in self.documents)
        provinces = {}
        perpetrators = {}
        years = {}
        
        for d in self.documents:
            provinces[d['province']] = provinces.get(d['province'], 0) + 1
            perp = d['perpetrator']
            perpetrators[perp] = perpetrators.get(perp, 0) + 1
            year = d['date'][:4]
            years[year] = years.get(year, 0) + 1
        
        return {
            "total_incidents": len(self.documents),
            "total_deaths": total_deaths,
            "total_injuries": total_injuries,
            "by_province": provinces,
            "by_perpetrator": perpetrators,
            "by_year": years
        }


rag_service = RAGService()
