from fastapi import APIRouter
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.rag_service import rag_service
from models.schemas import SearchRequest
from data.attacks_db import ensure_data_loaded

router = APIRouter()

@router.post("/")
async def search(request: SearchRequest):
    """Semantic search over attack records"""
    ensure_data_loaded()
    rag_service.refresh()
    filters = {}
    if request.province:
        filters['province'] = request.province
    if request.year:
        filters['year'] = request.year
    if request.perpetrator:
        filters['perpetrator'] = request.perpetrator
    
    retrieved = rag_service.retrieve(
        request.query, 
        top_k=request.limit or 10,
        filters=filters if filters else None
    )
    
    results = [doc for doc, score in retrieved]
    return {
        "query": request.query,
        "total": len(results),
        "results": results
    }
