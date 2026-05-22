from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import chat, attacks, search, health
import uvicorn

app = FastAPI(
    title="Pakistan Terror Attacks Intelligence API",
    description="RAG-powered chatbot API for Pakistan terror attack data",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(attacks.router, prefix="/api/attacks", tags=["Attacks"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
