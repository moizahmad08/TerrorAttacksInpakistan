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
    Main chat endpoint.
    Flow: sanitize → intent detect → RAG retrieve → Grok generate → store history
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    if len(request.message) > 1000:
        raise HTTPException(status_code=400, detail="Message too long (max 1000 chars)")
    
    # Session management
    session_id = request.session_id or session_memory.create_session()
    history = session_memory.get_history(session_id)
    
    # Intent detection (lightweight, no API call)
    intent = await grok_service.detect_intent(request.message)
    
    # RAG Retrieval
    retrieved_docs = rag_service.retrieve(request.message, top_k=5)
    context = rag_service.build_context(retrieved_docs)
    
    # Grok generation
    response_text = await grok_service.chat(
        user_message=request.message,
        context=context,
        history=history,
        use_reasoning=(intent in ['ranking', 'statistics', 'general'])
    )
    
    # Store in session memory
    session_memory.add_message(session_id, "user", request.message)
    session_memory.add_message(session_id, "assistant", response_text)
    
    # Build sources list for citation
    sources = [
        {
            "id": doc["id"],
            "date": doc["date"],
            "location": doc["location"],
            "deaths": doc["deaths"],
            "source": doc["source"]
        }
        for doc, _ in retrieved_docs[:3]
    ]
    
    return ChatResponse(
        response=response_text,
        session_id=session_id,
        sources=sources,
        intent=intent
    )

@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """Clear conversation history for a session"""
    if session_id in session_memory.sessions:
        del session_memory.sessions[session_id]
    return {"message": "Session cleared"}

@router.get("/session/{session_id}/history")
async def get_history(session_id: str):
    """Get conversation history for a session"""
    history = session_memory.get_history(session_id)
    return {"session_id": session_id, "history": history}
