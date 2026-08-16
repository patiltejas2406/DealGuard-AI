"""Main FastAPI Application Entrypoint."""

import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import get_logger, setup_logging

# Initialize structured logging
setup_logging()
logger = get_logger("dealguard.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle management."""
    logger.info(
        "Starting DealGuard AI Backend",
        extra={"version": settings.VERSION, "environment": settings.ENVIRONMENT}
    )
    yield
    logger.info("Shutting down DealGuard AI Backend")


def create_application() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="Institutional M&A Due Diligence, Risk Intelligence & Post-Deal Value Creation Platform",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan,
    )

    # Cross-Origin Resource Sharing (CORS) Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Observability & Request Tracing Middleware
    @app.middleware("http")
    async def request_tracing_middleware(request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start_time = time.perf_counter()
        
        response: Response = await call_next(request)
        
        process_time_ms = (time.perf_counter() - start_time) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = f"{process_time_ms:.2f}"
        
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} ({process_time_ms:.2f}ms)",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(process_time_ms, 2),
            }
        )
        return response

    # Register standardized error handlers
    register_exception_handlers(app)

    # Register API routes
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_application()
