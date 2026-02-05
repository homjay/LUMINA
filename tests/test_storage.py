"""Storage tests for License Server."""
import pytest
import asyncio
from pathlib import Path

from app.storage.json_storage import JSONStorage
from app.storage.sqlite_storage import SQLiteStorage
from app.models.schemas import LicenseCreate
from datetime import datetime, timedelta


@pytest.mark.asyncio
async def test_json_storage_create_and_get():
    """Test JSON storage create and get operations."""
    # Use test file
    storage = JSONStorage("data/test_licenses.json")

    # Create license
    license_data = LicenseCreate(
        product="TestApp",
        customer="Test Customer",
        max_activations=1,
        machine_binding=True
    )

    license_obj = await storage.create_license(license_data)

    assert license_obj.key is not None
    assert license_obj.product == "TestApp"
    assert license_obj.customer == "Test Customer"

    # Get license
    retrieved = await storage.get_license(license_obj.key)
    assert retrieved is not None
    assert retrieved.key == license_obj.key

    # Cleanup
    Path("data/test_licenses.json").unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_json_storage_update_and_delete():
    """Test JSON storage update and delete operations."""
    storage = JSONStorage("data/test_licenses.json")

    # Create license
    license_data = LicenseCreate(
        product="TestApp",
        customer="Test Customer"
    )
    license_obj = await storage.create_license(license_data)

    # Update license
    updated = await storage.update_license(
        license_obj.key,
        LicenseUpdate(customer="Updated Customer")
    )

    assert updated is not None
    assert updated.customer == "Updated Customer"

    # Delete license
    deleted = await storage.delete_license(license_obj.key)
    assert deleted is True

    # Verify deletion
    retrieved = await storage.get_license(license_obj.key)
    assert retrieved is None

    # Cleanup
    Path("data/test_licenses.json").unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_json_storage_activation():
    """Test JSON storage activation operations."""
    storage = JSONStorage("data/test_licenses.json")

    # Create license
    license_data = LicenseCreate(
        product="TestApp",
        customer="Test Customer",
        machine_binding=True
    )
    license_obj = await storage.create_license(license_data)

    # Add activation
    result = await storage.add_activation(
        license_obj.key,
        "MACHINE-CODE-123",
        "192.168.1.1"
    )

    assert result is True

    # Get activation count
    count = await storage.get_activations_count(license_obj.key)
    assert count == 1

    # Update verification
    update_result = await storage.update_verification(
        license_obj.key,
        "MACHINE-CODE-123",
        "192.168.1.1"
    )

    assert update_result is True

    # Verify
    license_updated = await storage.get_license(license_obj.key)
    assert len(license_updated.activations) == 1
    assert license_updated.activations[0].verification_count == 1

    # Cleanup
    Path("data/test_licenses.json").unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_sqlite_storage():
    """Test SQLite storage operations."""
    storage = SQLiteStorage("data/test_licenses.db")

    # Create license
    license_data = LicenseCreate(
        product="TestApp",
        customer="Test Customer"
    )
    license_obj = await storage.create_license(license_data)

    assert license_obj.key is not None
    assert license_obj.product == "TestApp"

    # Get license
    retrieved = await storage.get_license(license_obj.key)
    assert retrieved is not None

    # Cleanup
    Path("data/test_licenses.db").unlink(missing_ok=True)


# Import after definition to avoid circular import
from app.models.schemas import LicenseUpdate
