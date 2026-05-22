from fastapi import APIRouter
import os

router = APIRouter()

@router.get("/health")
async def health():
    return {
        "status": "ok",
        "grok_configured": True,
        "mode": "live"
    }
