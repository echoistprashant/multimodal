"""Application Entrypoint and Factory.

Initializes FastAPI app instance, registers middleware, lifespan events,
and mounts API version routers.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.middleware import RequestContextMiddleware
from app.api.v1.documents import router as documents_router
from app.api.v1.fields import router as fields_router
from app.api.v1.health import router as health_router
from app.api.v1.metrics import router as metrics_router
from app.api.v1.process import router as process_router
from app.api.v1.rag import router as rag_router
from app.api.v1.reviews import router as reviews_router
from app.api.v1.routing import router as routing_router
from app.api.v1.schemas import router as schemas_router
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging

logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan context manager for startup and shutdown hooks."""
    settings = get_settings()
    setup_logging(debug=settings.DEBUG)
    logger.info(
        f"Starting {settings.PROJECT_NAME} in [{settings.ENV}] environment (Debug={settings.DEBUG})"
    )
    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME} gracefully")


def create_app() -> FastAPI:
    """FastAPI application factory."""
    settings = get_settings()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="0.1.0",
        description="Multimodal Document Intelligence System API",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        lifespan=lifespan,
    )

    # Cross-Origin Resource Sharing
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request ID and latency tracing
    app.add_middleware(RequestContextMiddleware)

    # Base probes
    app.include_router(health_router, tags=["Health"])
    app.include_router(documents_router)
    app.include_router(routing_router)
    app.include_router(schemas_router)
    app.include_router(fields_router)
    app.include_router(reviews_router)
    app.include_router(rag_router)
    app.include_router(metrics_router)
    app.include_router(process_router)

    return app


app = create_app()
