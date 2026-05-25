from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes_health import router as health_router
from app.api.routes_documents import router as documents_router 
from app.api.routes_chat import router as chat_router
def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="A portfolio-ready RAG knowledge base API.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router,prefix="/api",tags=["health"])
    app.include_router(documents_router,prefix="/api/documents",tags=["documents"])
    app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
    return app


app = create_app()
