from fastapi import FastAPI

from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.core.config import get_settings
from app.telegram.router import router as telegram_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.include_router(health_router)
    app.include_router(chat_router)
    app.include_router(telegram_router)
    return app


app = create_app()
