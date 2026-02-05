"""Health check API endpoints."""
from fastapi import APIRouter

from app.models.schemas import HealthResponse
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse)
async def health_check():
    """Health check endpoint.

    Returns the current status of the service.
    """
    return HealthResponse(
        status="healthy",
        version=settings.app.version,
        storage_type=settings.storage.type
    )


@router.get("/ping")
async def ping():
    """Simple ping endpoint for checking service availability."""
    return {"ping": "pong"}
