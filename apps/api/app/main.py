from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.api.routes import budgets, chat, entries, health
from app.core.config import settings
from app.core.database import initialize_database


def create_app() -> FastAPI:
    app = FastAPI(
        title="Dodomoney API",
        description="AI-powered personal finance assistant backend.",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    initialize_database()

    app.include_router(health.router)
    app.include_router(chat.router, prefix="/chat", tags=["chat"])
    app.include_router(entries.router, prefix="/entries", tags=["entries"])
    app.include_router(budgets.router, prefix="/budgets", tags=["budgets"])
    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development",
    )
