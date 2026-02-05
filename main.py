"""Main application entry point for LUMINA.
License Unified Management & Identity Network Authorization"""

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import uvicorn

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1 import licenses, admin, health
from app.storage.factory import storage

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info(f"Starting {settings.app.name} v{settings.app.version}")
    logger.info(f"Storage type: {settings.storage.type}")

    # Initialize storage if needed
    if hasattr(storage, "_ensure_initialized"):
        await storage._ensure_initialized()

    yield

    # Shutdown
    logger.info("Shutting down...")
    if hasattr(storage, "close"):
        await storage.close()


# Create FastAPI application
app = FastAPI(
    title=settings.app.name,
    version=settings.app.version,
    description="License authentication and management server",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500, content={"error": "Internal server error", "detail": str(exc)}
    )


# Include routers
api_prefix = "/api/v1"
app.include_router(licenses.router, prefix=api_prefix)
app.include_router(admin.router, prefix=api_prefix)
app.include_router(health.router, prefix=api_prefix)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app.name,
        "version": settings.app.version,
        "status": "running",
        "docs": "/docs",
        "health": f"{api_prefix}/health",
    }


def main():
    """Main entry point."""
    uvicorn.run(
        "main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
        log_level=settings.logging.level.lower(),
    )


if __name__ == "__main__":
    main()
