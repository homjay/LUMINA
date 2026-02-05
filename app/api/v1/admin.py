"""Admin API endpoints for license management."""
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional

from app.models.schemas import (
    License,
    LicenseCreate,
    LicenseUpdate,
    AdminLogin,
    AdminToken,
    ErrorResponse
)
from app.services.license_service import license_service
from app.services.auth_service import auth_service

router = APIRouter(prefix="/admin", tags=["Admin"])


async def verify_admin_token(authorization: Optional[str] = Header(None)) -> bool:
    """Verify admin authorization token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")

    token = authorization[7:]  # Remove "Bearer " prefix
    is_valid = await auth_service.verify_token(token)

    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return True


@router.post("/login", response_model=AdminToken)
async def login(login_data: AdminLogin):
    """Authenticate as admin and get access token.

    Returns a JWT token that must be used in subsequent admin requests.
    """
    try:
        token = await auth_service.authenticate(login_data.username, login_data.password)

        if not token:
            raise HTTPException(status_code=401, detail="Invalid username or password")

        return AdminToken(access_token=token)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/license", response_model=License, dependencies=[Depends(verify_admin_token)])
async def create_license(license_data: LicenseCreate):
    """Create a new license.

    Requires admin authentication.
    """
    try:
        return await license_service.create_license(license_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/license/{key}", response_model=License, dependencies=[Depends(verify_admin_token)])
async def get_license(key: str):
    """Get a license by key.

    Requires admin authentication.
    """
    try:
        license_data = await license_service.get_license(key)

        if not license_data:
            raise HTTPException(status_code=404, detail="License not found")

        return license_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/licenses", response_model=list[License], dependencies=[Depends(verify_admin_token)])
async def get_all_licenses():
    """Get all licenses.

    Requires admin authentication.
    """
    try:
        return await license_service.get_all_licenses()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/license/{key}", response_model=License, dependencies=[Depends(verify_admin_token)])
async def update_license(key: str, license_data: LicenseUpdate):
    """Update a license.

    Requires admin authentication.
    """
    try:
        result = await license_service.update_license(key, license_data)

        if not result:
            raise HTTPException(status_code=404, detail="License not found")

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/license/{key}", dependencies=[Depends(verify_admin_token)])
async def delete_license(key: str):
    """Delete a license.

    Requires admin authentication.
    """
    try:
        success = await license_service.delete_license(key)

        if not success:
            raise HTTPException(status_code=404, detail="License not found")

        return {"message": "License deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
