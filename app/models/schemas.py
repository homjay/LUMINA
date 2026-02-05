"""Data models and schemas for License Server."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator


class ActivationRecord(BaseModel):
    """License activation record."""
    machine_code: Optional[str] = None
    ip: Optional[str] = None
    activated_at: datetime = Field(default_factory=datetime.utcnow)
    last_verified: Optional[datetime] = None
    verification_count: int = 0


class LicenseBase(BaseModel):
    """Base license schema."""
    product: str
    version: Optional[str] = "1.0.0"
    customer: str
    email: Optional[str] = None
    max_activations: int = 1
    machine_binding: bool = True
    ip_whitelist: List[str] = Field(default_factory=list)
    expiry_date: Optional[datetime] = None
    status: str = "active"


class LicenseCreate(LicenseBase):
    """Schema for creating a license."""
    key: Optional[str] = None


class LicenseUpdate(BaseModel):
    """Schema for updating a license."""
    product: Optional[str] = None
    version: Optional[str] = None
    customer: Optional[str] = None
    email: Optional[str] = None
    max_activations: Optional[int] = None
    machine_binding: Optional[bool] = None
    ip_whitelist: Optional[List[str]] = None
    expiry_date: Optional[datetime] = None
    status: Optional[str] = None


class License(LicenseBase):
    """Full license schema."""
    key: str
    created_at: datetime
    updated_at: datetime
    activations: List[ActivationRecord] = Field(default_factory=list)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class LicenseVerifyRequest(BaseModel):
    """Schema for license verification request."""
    license_key: str
    machine_code: Optional[str] = None
    ip: Optional[str] = None


class LicenseVerifyResponse(BaseModel):
    """Schema for license verification response."""
    valid: bool
    message: str
    license: Optional[License] = None
    remaining_activations: Optional[int] = None
    expiry_date: Optional[datetime] = None


class AdminLogin(BaseModel):
    """Schema for admin login."""
    username: str
    password: str


class AdminToken(BaseModel):
    """Schema for admin token response."""
    access_token: str
    token_type: str = "bearer"


class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str
    version: str
    storage_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Schema for error response."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
