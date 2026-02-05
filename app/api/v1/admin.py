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


# API Key Management Endpoints

@router.post("/apikeys", dependencies=[Depends(verify_admin_token)])
async def create_api_key(name: str = None, expires: str = None):
    """Create a new API key for long-term access.

    Requires admin authentication.
    """
    try:
        import secrets
        import string
        from datetime import datetime, timedelta

        # Generate secure random API key
        api_key = 'lumina_' + ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

        # Parse expiration
        expires_at = None
        if expires:
            if expires.endswith('d'):
                days = int(expires[:-1])
                expires_at = (datetime.now() + timedelta(days=days)).isoformat()
            elif expires.endswith('y'):
                years = int(expires[:-1])
                expires_at = (datetime.now() + timedelta(days=years*365)).isoformat()
            else:
                # Try to parse as date
                try:
                    expires_at = datetime.strptime(expires, "%Y-%m-%d").isoformat()
                except:
                    raise HTTPException(status_code=400, detail="Invalid expiration format. Use: 30d, 1y, or YYYY-MM-DD")

        # Store in database
        if settings.storage.type == "sqlite":
            import sqlite3
            from pathlib import Path
            db_path = Path(settings.storage.sqlite_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO api_keys (key, name, expires_at)
                VALUES (?, ?, ?)
            """, (api_key, name, expires_at))

            conn.commit()
            conn.close()

        return {
            "key": api_key,
            "name": name or "N/A",
            "expires_at": expires_at,
            "created_at": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/apikeys", dependencies=[Depends(verify_admin_token)])
async def list_api_keys():
    """List all API keys.

    Requires admin authentication.
    """
    try:
        import sqlite3
        from pathlib import Path

        if settings.storage.type != "sqlite":
            raise HTTPException(status_code=400, detail="API keys only supported with SQLite storage")

        db_path = Path(settings.storage.sqlite_path)
        if not db_path.exists():
            return {"api_keys": []}

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, key, name, created_at, expires_at, is_active
            FROM api_keys
            ORDER BY created_at DESC
        """)

        keys = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return {"api_keys": keys}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/apikeys/{key}", dependencies=[Depends(verify_admin_token)])
async def delete_api_key(key: str):
    """Delete an API key.

    Requires admin authentication.
    """
    try:
        import sqlite3
        from pathlib import Path

        if settings.storage.type != "sqlite":
            raise HTTPException(status_code=400, detail="API keys only supported with SQLite storage")

        db_path = Path(settings.storage.sqlite_path)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM api_keys WHERE key = ?", (key,))
        conn.commit()

        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="API key not found")

        conn.close()
        return {"message": "API key deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
