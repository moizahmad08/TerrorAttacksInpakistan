from fastapi import APIRouter
import os

router = APIRouter()

@router.get("/health")
async def health():
    return {
        "status": "ok",
        "grok_configured": bool(os.getenv("GROK_API_KEY", "")),
        "mode": "live" if os.getenv("GROK_API_KEY") else "demo"
    }
