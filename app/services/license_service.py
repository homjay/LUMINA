"""License verification and management service."""
from datetime import datetime
from typing import Optional

from loguru import logger

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
        logger.info(f"[LICENSE_VERIFY] Starting verification for key: {request.license_key[:10]}... from IP: {client_ip}")

        # Get license
        license_data = await storage.get_license(request.license_key)

        if not license_data:
            logger.warning(f"[LICENSE_VERIFY] License key not found: {request.license_key[:10]}...")
            return LicenseVerifyResponse(
                valid=False,
                message="Invalid license key"
            )

        # Check if license is active
        if license_data.status != "active":
            logger.warning(f"[LICENSE_VERIFY] License {request.license_key[:10]}... status is: {license_data.status}")
            return LicenseVerifyResponse(
                valid=False,
                message=f"License is {license_data.status}"
            )

        # Check expiry
        if is_license_expired(license_data.expiry_date):
            logger.warning(f"[LICENSE_VERIFY] License {request.license_key[:10]}... expired on: {license_data.expiry_date}")
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
            logger.info(f"[LICENSE_VERIFY] New activation request. Current: {current_count}/{license_data.max_activations}")
            if current_count >= license_data.max_activations:
                logger.warning(f"[LICENSE_VERIFY] License {request.license_key[:10]}... max activations reached: {current_count}")
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
            logger.info(f"[LICENSE_VERIFY] New activation added for {request.license_key[:10]}... IP: {client_ip}, Machine: {request.machine_code[:10] if request.machine_code else 'N/A'}...")
        else:
            # Update existing verification
            await storage.update_verification(
                request.license_key,
                request.machine_code,
                client_ip
            )
            logger.info(f"[LICENSE_VERIFY] Updated existing verification for {request.license_key[:10]}...")

        # Refresh license data
        license_data = await storage.get_license(request.license_key)
        remaining = license_data.max_activations - len(license_data.activations)

        logger.info(f"[LICENSE_VERIFY] SUCCESS - {request.license_key[:10]}... Product: {license_data.product}, Remaining: {remaining}")

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
        logger.info(f"[LICENSE_CREATE] Creating new license - Product: {license_data.product}, Customer: {license_data.customer}, Max activations: {license_data.max_activations}")

        # Validate IP whitelist
        if license_data.ip_whitelist:
            if not validate_ip_whitelist(license_data.ip_whitelist):
                logger.error(f"[LICENSE_CREATE] Invalid IP whitelist provided")
                raise ValueError("Invalid IP address in whitelist")

        result = await storage.create_license(license_data)
        logger.info(f"[LICENSE_CREATE] SUCCESS - License key: {result.key[:10]}... created for {license_data.product}")
        return result

    async def get_license(self, key: str) -> Optional[License]:
        """Get a license by key.

        Args:
            key: License key

        Returns:
            License data or None
        """
        logger.debug(f"[LICENSE_GET] Fetching license: {key[:10]}...")
        return await storage.get_license(key)

    async def get_all_licenses(self) -> list[License]:
        """Get all licenses.

        Returns:
            List of all licenses
        """
        licenses = await storage.get_all_licenses()
        logger.info(f"[LICENSE_LIST] Retrieved {len(licenses)} licenses")
        return licenses

    async def update_license(self, key: str, license_data: LicenseUpdate) -> Optional[License]:
        """Update a license.

        Args:
            key: License key
            license_data: Update data

        Returns:
            Updated license or None
        """
        logger.info(f"[LICENSE_UPDATE] Updating license: {key[:10]}...")

        # Validate IP whitelist if provided
        if license_data.ip_whitelist is not None:
            if not validate_ip_whitelist(license_data.ip_whitelist):
                logger.error(f"[LICENSE_UPDATE] Invalid IP whitelist provided")
                raise ValueError("Invalid IP address in whitelist")

        result = await storage.update_license(key, license_data)
        if result:
            logger.info(f"[LICENSE_UPDATE] SUCCESS - License {key[:10]}... updated")
        else:
            logger.warning(f"[LICENSE_UPDATE] License {key[:10]}... not found")
        return result

    async def delete_license(self, key: str) -> bool:
        """Delete a license.

        Args:
            key: License key

        Returns:
            True if deleted, False otherwise
        """
        logger.info(f"[LICENSE_DELETE] Deleting license: {key[:10]}...")
        result = await storage.delete_license(key)
        if result:
            logger.info(f"[LICENSE_DELETE] SUCCESS - License {key[:10]}... deleted")
        else:
            logger.warning(f"[LICENSE_DELETE] License {key[:10]}... not found")
        return result


# Global service instance
license_service = LicenseService()
