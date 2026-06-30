from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.teacher import router as teacher_router
from app.core.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialise SQLite database
    from app.services.database import init_db
    await init_db()
    # Preload pedagogical documents
    from app.services.rag_service import rag_service
    rag_service.load_documents()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all for development MVP
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(chat_router)
    app.include_router(teacher_router)
    return app


app = create_app()

