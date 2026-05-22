from fastapi import APIRouter, Query
from typing import Optional
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.attacks_db import ATTACKS_DATA, PROVINCES, PERPETRATORS, DATA_SOURCE, ensure_data_loaded
from services.rag_service import rag_service

router = APIRouter()

MAX_PAGE_SIZE = 200


def _record_search_text(doc: dict) -> str:
    return " ".join(
        str(doc.get(k, ""))
        for k in ("id", "date", "location", "province", "attack_type", "target", "perpetrator", "description")
    ).lower()


@router.get("/")
async def list_attacks(
    province: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    perpetrator: Optional[str] = Query(None),
    q: Optional[str] = Query(None, description="Search across location, group, type, description"),
    limit: int = Query(50, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(0, ge=0),
):
    """List attacks with filters, search, and pagination."""
    ensure_data_loaded()
    filtered = ATTACKS_DATA.copy()

    if province:
        filtered = [d for d in filtered if province.lower() in d["province"].lower()]
    if year:
        filtered = [d for d in filtered if d["date"].startswith(str(year))]
    if perpetrator:
        filtered = [d for d in filtered if perpetrator.lower() in d["perpetrator"].lower()]
    if q:
        query = q.lower().strip()
        filtered = [d for d in filtered if query in _record_search_text(d)]

    filtered.sort(key=lambda x: x["date"], reverse=True)
    total = len(filtered)
    page = filtered[offset : offset + limit]

    return {
        "total": total,
        "data": page,
        "offset": offset,
        "limit": limit,
        "has_more": offset + limit < total,
        "data_source": DATA_SOURCE,
    }


@router.get("/meta")
async def get_meta():
    """Dataset metadata for the frontend."""
    ensure_data_loaded()
    return {
        "total_incidents": len(ATTACKS_DATA),
        "data_source": DATA_SOURCE,
        "provinces": PROVINCES,
        "perpetrators": PERPETRATORS,
    }


@router.get("/stats")
async def get_statistics():
    """Get aggregate statistics from the knowledge base"""
    ensure_data_loaded()
    rag_service.refresh()
    stats = rag_service.get_stats()
    stats["data_source"] = DATA_SOURCE
    return stats


@router.get("/provinces")
async def get_provinces():
    ensure_data_loaded()
    return {"provinces": PROVINCES}


@router.get("/perpetrators")
async def get_perpetrators():
    ensure_data_loaded()
    return {"perpetrators": PERPETRATORS}


@router.get("/deadliest")
async def get_deadliest(limit: int = Query(5, ge=1, le=20)):
    """Get deadliest attacks sorted by death toll"""
    ensure_data_loaded()
    sorted_attacks = sorted(ATTACKS_DATA, key=lambda x: x["deaths"], reverse=True)
    return {"data": sorted_attacks[:limit]}


@router.get("/{attack_id}")
async def get_attack(attack_id: str):
    """Get a single attack by ID"""
    ensure_data_loaded()
    attack = next((d for d in ATTACKS_DATA if d["id"] == attack_id), None)
    if not attack:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Attack record not found")
    return attack
