from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.api.routes import auth, budgets, chat, entries, health, ledgers, loans, reimbursements, uploads, users
from app.api.routes.uploads import UPLOAD_DIR
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
        allow_origin_regex=settings.cors_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    initialize_database()
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/media", StaticFiles(directory=UPLOAD_DIR), name="media")

    app.include_router(health.router)
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(users.router, prefix="/users", tags=["users"])
    app.include_router(ledgers.router, prefix="/ledgers", tags=["ledgers"])
    app.include_router(chat.router, prefix="/chat", tags=["chat"])
    app.include_router(entries.router, prefix="/entries", tags=["entries"])
    app.include_router(budgets.router, prefix="/budgets", tags=["budgets"])
    app.include_router(loans.router, prefix="/loans", tags=["loans"])
    app.include_router(reimbursements.router, prefix="/reimbursements", tags=["reimbursements"])
    app.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development",
    )
