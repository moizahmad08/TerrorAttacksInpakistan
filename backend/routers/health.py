from fastapi import APIRouter
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.attacks_db import ATTACKS_DATA, DATA_SOURCE

router = APIRouter()


@router.get("/health")
async def health():
    grok_key = os.getenv("GROK_API_KEY", "")
    grok_configured = bool(grok_key and grok_key != "your_grok_api_key_here")
    return {
        "status": "ok",
        "grok_configured": grok_configured,
        "mode": "live" if grok_configured else "demo",
        "total_incidents": len(ATTACKS_DATA),
        "data_source": DATA_SOURCE,
    }
