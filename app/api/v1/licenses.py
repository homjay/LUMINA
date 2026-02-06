"""License verification API endpoints."""
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse

from loguru import logger

from app.models.schemas import LicenseVerifyRequest, LicenseVerifyResponse, ErrorResponse
from app.services.license_service import license_service

router = APIRouter(prefix="/license", tags=["License"])


@router.post("/verify", response_model=LicenseVerifyResponse)
async def verify_license(
    request_data: LicenseVerifyRequest,
    request: Request
):
    """Verify a license key.

    This endpoint validates a license key and optionally records activation data.
    """
    try:
        # Get client IP
        client_ip = request_data.ip or request.client.host if request.client else None

        # Verify license
        result = await license_service.verify_license(request_data, client_ip)

        # Log result summary
        if result.valid:
            logger.info(f"[API] License verification SUCCESS: {request_data.license_key[:10]}... -> {result.message}")
        else:
            logger.warning(f"[API] License verification FAILED: {request_data.license_key[:10]}... -> {result.message}")

        return result

    except ValueError as e:
        logger.error(f"[API] License verification ValueError: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[API] License verification error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/check/{key}")
async def check_license(key: str):
    """Check if a license key exists and is active.

    Returns minimal information about the license status.
    """
    try:
        license_data = await license_service.get_license(key)

        if not license_data:
            return JSONResponse(
                status_code=404,
                content={
                    "exists": False,
                    "message": "License not found"
                }
            )

        return {
            "exists": True,
            "active": license_data.status == "active",
            "product": license_data.product,
            "customer": license_data.customer
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
