"""License verification and management service."""
from datetime import datetime
from typing import Optional

from app.models.schemas import (
    License,
    LicenseVerifyRequest,
    LicenseVerifyResponse,
    LicenseCreate,
    LicenseUpdate
)
from app.storage.factory import storage
from app.utils.validators import (
    validate_ip_address,
    validate_ip_whitelist,
    validate_machine_code
)
from app.utils.helpers import is_license_expired, get_client_ip


class LicenseService:
    """Service for license operations."""

    async def verify_license(
        self,
        request: LicenseVerifyRequest,
        client_ip: Optional[str] = None
    ) -> LicenseVerifyResponse:
        """Verify a license key.

        Args:
            request: License verification request
            client_ip: Client IP address

        Returns:
            Verification response
        """
        # Get license
        license_data = await storage.get_license(request.license_key)

        if not license_data:
            return LicenseVerifyResponse(
                valid=False,
                message="Invalid license key"
            )

        # Check if license is active
        if license_data.status != "active":
            return LicenseVerifyResponse(
                valid=False,
                message=f"License is {license_data.status}"
            )

        # Check expiry
        if is_license_expired(license_data.expiry_date):
            return LicenseVerifyResponse(
                valid=False,
                message="License has expired"
            )

        # Validate machine code if required
        if license_data.machine_binding and request.machine_code:
            if not validate_machine_code(request.machine_code):
                return LicenseVerifyResponse(
                    valid=False,
                    message="Invalid machine code format"
                )

        # Check IP whitelist
        if license_data.ip_whitelist and client_ip:
            if client_ip not in license_data.ip_whitelist:
                return LicenseVerifyResponse(
                    valid=False,
                    message="IP address not authorized"
                )

        # Check for existing activation
        activation_exists = False
        for activation in license_data.activations:
            if license_data.machine_binding and request.machine_code:
                if activation.machine_code == request.machine_code:
                    activation_exists = True
                    break
            elif not license_data.machine_binding and activation.ip == client_ip:
                activation_exists = True
                break

        # Check if max activations reached
        if not activation_exists:
            current_count = await storage.get_activations_count(request.license_key)
            if current_count >= license_data.max_activations:
                return LicenseVerifyResponse(
                    valid=False,
                    message="Maximum activations reached"
                )

            # Add new activation
            await storage.add_activation(
                request.license_key,
                request.machine_code,
                client_ip
            )
        else:
            # Update existing verification
            await storage.update_verification(
                request.license_key,
                request.machine_code,
                client_ip
            )

        # Refresh license data
        license_data = await storage.get_license(request.license_key)
        remaining = license_data.max_activations - len(license_data.activations)

        return LicenseVerifyResponse(
            valid=True,
            message="License verified successfully",
            license=license_data,
            remaining_activations=remaining,
            expiry_date=license_data.expiry_date
        )

    async def create_license(self, license_data: LicenseCreate) -> License:
        """Create a new license.

        Args:
            license_data: License creation data

        Returns:
            Created license
        """
        # Validate IP whitelist
        if license_data.ip_whitelist:
            if not validate_ip_whitelist(license_data.ip_whitelist):
                raise ValueError("Invalid IP address in whitelist")

        return await storage.create_license(license_data)

    async def get_license(self, key: str) -> Optional[License]:
        """Get a license by key.

        Args:
            key: License key

        Returns:
            License data or None
        """
        return await storage.get_license(key)

    async def get_all_licenses(self) -> list[License]:
        """Get all licenses.

        Returns:
            List of all licenses
        """
        return await storage.get_all_licenses()

    async def update_license(self, key: str, license_data: LicenseUpdate) -> Optional[License]:
        """Update a license.

        Args:
            key: License key
            license_data: Update data

        Returns:
            Updated license or None
        """
        # Validate IP whitelist if provided
        if license_data.ip_whitelist is not None:
            if not validate_ip_whitelist(license_data.ip_whitelist):
                raise ValueError("Invalid IP address in whitelist")

        return await storage.update_license(key, license_data)

    async def delete_license(self, key: str) -> bool:
        """Delete a license.

        Args:
            key: License key

        Returns:
            True if deleted, False otherwise
        """
        return await storage.delete_license(key)


# Global service instance
license_service = LicenseService()
