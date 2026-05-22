from pydantic import BaseModel
from typing import Optional, List
from datetime import date

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    response: str
    session_id: str
    sources: Optional[List[dict]] = []
    intent: Optional[str] = None
    mode: Optional[str] = None  # "ai" = Grok agent, "database" = search + local summary

class AttackRecord(BaseModel):
    id: str
    date: str
    location: str
    province: str
    attack_type: str
    target: str
    perpetrator: str
    deaths: int
    injuries: int
    description: str
    source: str

class SearchRequest(BaseModel):
    query: str
    province: Optional[str] = None
    year: Optional[int] = None
    perpetrator: Optional[str] = None
    limit: Optional[int] = 10

class SearchResponse(BaseModel):
    results: List[AttackRecord]
    total: int
    query: str
