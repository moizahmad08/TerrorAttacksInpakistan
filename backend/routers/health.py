from fastapi import APIRouter
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.attacks_db import ATTACKS_DATA, DATA_SOURCE
from services.grok_service import grok_service

router = APIRouter()


@router.get("/health")
async def health():
    grok_ok = grok_service.is_configured()
    return {
        "status": "ok",
        "grok_configured": grok_ok,
        "mode": "live" if grok_ok else "demo",
        "chat_mode": "ai_agent" if grok_ok else "database_agent",
        "grok_model": os.getenv("GROK_MODEL", "grok-4-1-fast-reasoning") if grok_ok else None,
        "total_incidents": len(ATTACKS_DATA),
        "data_source": DATA_SOURCE,
    }
