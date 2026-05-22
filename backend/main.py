from dotenv import load_dotenv
load_dotenv()

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import chat, attacks, search, health
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start API immediately; load data in background so Docker healthcheck passes."""
    from data.attacks_db import ensure_data_loaded

    async def _load():
        await asyncio.to_thread(ensure_data_loaded)

    task = asyncio.create_task(_load())
    yield
    task.cancel()


app = FastAPI(
    title="Pakistan Terror Attacks Intelligence API",
    description="RAG-powered chatbot API for Pakistan terror attack data",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(attacks.router, prefix="/api/attacks", tags=["Attacks"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])

if __name__ == "__main__":
    import os
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host=host, port=port, reload=True)
