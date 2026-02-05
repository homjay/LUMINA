"""Base storage interface for license management."""
from abc import ABC, abstractmethod
from typing import List, Optional

from app.models.schemas import License, LicenseCreate, LicenseUpdate


class BaseStorage(ABC):
    """Abstract base class for storage implementations."""

    @abstractmethod
    async def get_license(self, key: str) -> Optional[License]:
        """Get a license by key."""
        pass

    @abstractmethod
    async def get_all_licenses(self) -> List[License]:
        """Get all licenses."""
        pass

    @abstractmethod
    async def create_license(self, license_data: LicenseCreate) -> License:
        """Create a new license."""
        pass

    @abstractmethod
    async def update_license(self, key: str, license_data: LicenseUpdate) -> Optional[License]:
        """Update an existing license."""
        pass

    @abstractmethod
    async def delete_license(self, key: str) -> bool:
        """Delete a license."""
        pass

    @abstractmethod
    async def license_exists(self, key: str) -> bool:
        """Check if a license exists."""
        pass

    @abstractmethod
    async def add_activation(
        self,
        key: str,
        machine_code: Optional[str],
        ip: Optional[str]
    ) -> bool:
        """Add an activation record to a license."""
        pass

    @abstractmethod
    async def update_verification(
        self,
        key: str,
        machine_code: Optional[str],
        ip: Optional[str]
    ) -> bool:
        """Update verification count and timestamp."""
        pass

    @abstractmethod
    async def get_activations_count(self, key: str) -> int:
        """Get the number of activations for a license."""
        pass
