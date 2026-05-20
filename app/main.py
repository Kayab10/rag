# main.py - FastAPI application entry point.
# Registers all routers and starts the app.

from fastapi import FastAPI
from app.api.routes_health import router as health_router
from app.api.routes_documents import router as documents_router
from app.api.routes_chat import router as chat_router

app = FastAPI(
    title="RAG Chatbot API",
    description="Upload documents and ask questions powered by Google Gemini.",
    version="0.1.0",
)

# Register routers
app.include_router(health_router)
app.include_router(documents_router)
app.include_router(chat_router)
