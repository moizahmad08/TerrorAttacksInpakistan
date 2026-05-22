import uuid
from typing import List, Dict, Optional
from datetime import datetime, timedelta

class SessionMemory:
    """
    In-memory session store. 
    For production: swap with Redis using aioredis.
    """
    
    def __init__(self, max_sessions: int = 1000, ttl_hours: int = 2):
        self.sessions: Dict[str, dict] = {}
        self.max_sessions = max_sessions
        self.ttl = timedelta(hours=ttl_hours)

    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "history": [],
            "created_at": datetime.utcnow(),
            "last_active": datetime.utcnow()
        }
        self._cleanup()
        return session_id

    def get_history(self, session_id: str) -> List[Dict]:
        session = self.sessions.get(session_id)
        if not session:
            return []
        session["last_active"] = datetime.utcnow()
        return session["history"]

    def add_message(self, session_id: str, role: str, content: str):
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "history": [],
                "created_at": datetime.utcnow(),
                "last_active": datetime.utcnow()
            }
        
        self.sessions[session_id]["history"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.sessions[session_id]["last_active"] = datetime.utcnow()
        
        # Keep last 20 messages per session
        if len(self.sessions[session_id]["history"]) > 20:
            self.sessions[session_id]["history"] = self.sessions[session_id]["history"][-20:]

    def _cleanup(self):
        """Remove expired sessions"""
        now = datetime.utcnow()
        expired = [
            sid for sid, data in self.sessions.items()
            if now - data["last_active"] > self.ttl
        ]
        for sid in expired:
            del self.sessions[sid]
        
        # If still too many, remove oldest
        if len(self.sessions) > self.max_sessions:
            sorted_sessions = sorted(
                self.sessions.items(), 
                key=lambda x: x[1]["last_active"]
            )
            for sid, _ in sorted_sessions[:len(self.sessions) - self.max_sessions]:
                del self.sessions[sid]


session_memory = SessionMemory()
