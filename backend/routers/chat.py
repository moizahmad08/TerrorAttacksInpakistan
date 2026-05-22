from fastapi import APIRouter, HTTPException
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schemas import ChatRequest, ChatResponse
from services.rag_service import rag_service
from services.grok_service import grok_service
from services.session_service import session_memory
import uuid

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Agent flow: understand question → search database → answer user (Grok AI or smart fallback).
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    if len(request.message) > 1000:
        raise HTTPException(status_code=400, detail="Message too long (max 1000 chars)")

    session_id = request.session_id or session_memory.create_session()
    history = session_memory.get_history(session_id)

    intent = await grok_service.detect_intent(request.message)

    # Step 1: Search database for relevant attacks
    retrieved_docs = rag_service.search_for_agent(request.message, intent)
    context = rag_service.build_context(retrieved_docs)

    stats = None
    if intent == "statistics":
        stats = rag_service.get_stats()
        context = (
            f"DATABASE STATISTICS:\n"
            f"Total incidents: {stats['total_incidents']}\n"
            f"Total deaths: {stats['total_deaths']}\n"
            f"Total injuries: {stats['total_injuries']}\n"
            f"By province (top): {dict(list(sorted(stats['by_province'].items(), key=lambda x: x[1], reverse=True))[:8])}\n"
            f"By perpetrator (top): {dict(list(sorted(stats['by_perpetrator'].items(), key=lambda x: x[1], reverse=True))[:8])}\n\n"
            + context
        )

    # Step 2: Agent answers using search results (Grok when configured)
    response_text, mode = await grok_service.chat(
        user_message=request.message,
        context=context,
        history=history,
        intent=intent,
        retrieved_docs=retrieved_docs,
        stats=stats,
    )

    session_memory.add_message(session_id, "user", request.message)
    session_memory.add_message(session_id, "assistant", response_text)

    sources = [
        {
            "id": doc["id"],
            "date": doc["date"],
            "location": doc["location"],
            "province": doc.get("province", ""),
            "attack_type": doc.get("attack_type", ""),
            "perpetrator": doc.get("perpetrator", ""),
            "deaths": doc["deaths"],
            "injuries": doc.get("injuries", 0),
            "source": doc["source"],
        }
        for doc, _ in retrieved_docs[:5]
    ]

    return ChatResponse(
        response=response_text,
        session_id=session_id,
        sources=sources,
        intent=intent,
        mode=mode,
    )


@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    if session_id in session_memory.sessions:
        del session_memory.sessions[session_id]
    return {"message": "Session cleared"}


@router.get("/session/{session_id}/history")
async def get_history(session_id: str):
    history = session_memory.get_history(session_id)
    return {"session_id": session_id, "history": history}
