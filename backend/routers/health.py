from fastapi import APIRouter
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.attacks_db import ATTACKS_DATA, DATA_SOURCE, is_data_loaded
from services.grok_service import grok_service

router = APIRouter()


@router.get("/health")
async def health():
    """Fast health check — does not block on Supabase/CSV load."""
    grok_ok = grok_service.is_configured()
    ready = is_data_loaded()
    return {
        "status": "ok",
        "ready": ready,
        "grok_configured": grok_ok,
        "mode": "live" if grok_ok else "demo",
        "chat_mode": "ai_agent" if grok_ok else "database_agent",
        "grok_model": os.getenv("GROK_MODEL", "grok-4-1-fast-reasoning") if grok_ok else None,
        "total_incidents": len(ATTACKS_DATA) if ready else 0,
        "data_source": DATA_SOURCE if ready else "loading",
    }
