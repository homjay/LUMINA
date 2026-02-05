"""JSON file storage implementation."""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from app.models.schemas import License, LicenseCreate, LicenseUpdate, ActivationRecord
from app.storage.base import BaseStorage
from app.utils.key_generator import generate_license_key
from app.core.config import settings


class JSONStorage(BaseStorage):
    """JSON file storage for licenses."""

    def __init__(self, file_path: str = None):
        """Initialize JSON storage."""
        self.file_path = Path(file_path or settings.storage.json_path)
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Ensure the JSON file exists."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            initial_data = {
                "licenses": [],
                "metadata": {
                    "version": "1.0",
                    "total_licenses": 0,
                    "last_updated": datetime.utcnow().isoformat()
                }
            }
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, indent=2, ensure_ascii=False)

    def _load_data(self) -> dict:
        """Load data from JSON file."""
        with open(self.file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_data(self, data: dict):
        """Save data to JSON file."""
        data["metadata"]["total_licenses"] = len(data["licenses"])
        data["metadata"]["last_updated"] = datetime.utcnow().isoformat()
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _dict_to_license(self, data: dict) -> License:
        """Convert dict to License object."""
        # Parse datetime strings
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        if "updated_at" in data and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
        if "expiry_date" in data and data["expiry_date"] and isinstance(data["expiry_date"], str):
            data["expiry_date"] = datetime.fromisoformat(data["expiry_date"].replace("Z", "+00:00"))

        # Parse activations
        activations = []
        for act in data.get("activations", []):
            if isinstance(act["activated_at"], str):
                act["activated_at"] = datetime.fromisoformat(act["activated_at"].replace("Z", "+00:00"))
            if act.get("last_verified") and isinstance(act["last_verified"], str):
                act["last_verified"] = datetime.fromisoformat(act["last_verified"].replace("Z", "+00:00"))
            activations.append(ActivationRecord(**act))
        data["activations"] = activations

        return License(**data)

    def _license_to_dict(self, license: License) -> dict:
        """Convert License object to dict."""
        data = license.model_dump(mode="json")
        # Ensure datetime is ISO format
        if isinstance(data.get("created_at"), datetime):
            data["created_at"] = data["created_at"].isoformat() + "Z"
        if isinstance(data.get("updated_at"), datetime):
            data["updated_at"] = data["updated_at"].isoformat() + "Z"
        if data.get("expiry_date") and isinstance(data["expiry_date"], datetime):
            data["expiry_date"] = data["expiry_date"].isoformat() + "Z"
        for act in data.get("activations", []):
            if isinstance(act.get("activated_at"), datetime):
                act["activated_at"] = act["activated_at"].isoformat() + "Z"
            if act.get("last_verified") and isinstance(act["last_verified"], datetime):
                act["last_verified"] = act["last_verified"].isoformat() + "Z"
        return data

    async def get_license(self, key: str) -> Optional[License]:
        """Get a license by key."""
        data = self._load_data()
        for lic in data["licenses"]:
            if lic["key"] == key:
                return self._dict_to_license(lic)
        return None

    async def get_all_licenses(self) -> List[License]:
        """Get all licenses."""
        data = self._load_data()
        return [self._dict_to_license(lic) for lic in data["licenses"]]

    async def create_license(self, license_data: LicenseCreate) -> License:
        """Create a new license."""
        data = self._load_data()

        # Generate key if not provided
        key = license_data.key or generate_license_key()

        # Check if key already exists
        for lic in data["licenses"]:
            if lic["key"] == key:
                raise ValueError(f"License with key {key} already exists")

        now = datetime.utcnow()
        license_dict = {
            "key": key,
            "product": license_data.product,
            "version": license_data.version or "1.0.0",
            "customer": license_data.customer,
            "email": license_data.email,
            "max_activations": license_data.max_activations,
            "machine_binding": license_data.machine_binding,
            "ip_whitelist": license_data.ip_whitelist,
            "expiry_date": license_data.expiry_date.isoformat() + "Z" if license_data.expiry_date else None,
            "status": license_data.status or "active",
            "created_at": now.isoformat() + "Z",
            "updated_at": now.isoformat() + "Z",
            "activations": []
        }

        data["licenses"].append(license_dict)
        self._save_data(data)

        return self._dict_to_license(license_dict)

    async def update_license(self, key: str, license_data: LicenseUpdate) -> Optional[License]:
        """Update an existing license."""
        data = self._load_data()

        for i, lic in enumerate(data["licenses"]):
            if lic["key"] == key:
                # Update fields
                update_dict = license_data.model_dump(exclude_unset=True)
                if "expiry_date" in update_dict and update_dict["expiry_date"]:
                    update_dict["expiry_date"] = update_dict["expiry_date"].isoformat() + "Z"

                for field, value in update_dict.items():
                    if value is not None:
                        data["licenses"][i][field] = value

                data["licenses"][i]["updated_at"] = datetime.utcnow().isoformat() + "Z"
                self._save_data(data)
                return self._dict_to_license(data["licenses"][i])

        return None

    async def delete_license(self, key: str) -> bool:
        """Delete a license."""
        data = self._load_data()
        original_count = len(data["licenses"])
        data["licenses"] = [lic for lic in data["licenses"] if lic["key"] != key]

        if len(data["licenses"]) < original_count:
            self._save_data(data)
            return True
        return False

    async def license_exists(self, key: str) -> bool:
        """Check if a license exists."""
        license_data = await self.get_license(key)
        return license_data is not None

    async def add_activation(
        self,
        key: str,
        machine_code: Optional[str],
        ip: Optional[str]
    ) -> bool:
        """Add an activation record to a license."""
        data = self._load_data()

        for lic in data["licenses"]:
            if lic["key"] == key:
                # Check if activation already exists
                for act in lic["activations"]:
                    if act.get("machine_code") == machine_code:
                        return False  # Already activated

                activation = {
                    "machine_code": machine_code,
                    "ip": ip,
                    "activated_at": datetime.utcnow().isoformat() + "Z",
                    "last_verified": None,
                    "verification_count": 0
                }
                lic["activations"].append(activation)
                lic["updated_at"] = datetime.utcnow().isoformat() + "Z"
                self._save_data(data)
                return True

        return False

    async def update_verification(
        self,
        key: str,
        machine_code: Optional[str],
        ip: Optional[str]
    ) -> bool:
        """Update verification count and timestamp."""
        data = self._load_data()

        for lic in data["licenses"]:
            if lic["key"] == key:
                for act in lic["activations"]:
                    # Find matching activation (by machine code if available, otherwise by IP)
                    if machine_code and act.get("machine_code") == machine_code:
                        act["verification_count"] = act.get("verification_count", 0) + 1
                        act["last_verified"] = datetime.utcnow().isoformat() + "Z"
                        if ip:
                            act["ip"] = ip
                        lic["updated_at"] = datetime.utcnow().isoformat() + "Z"
                        self._save_data(data)
                        return True
                    elif not machine_code and act.get("ip") == ip:
                        act["verification_count"] = act.get("verification_count", 0) + 1
                        act["last_verified"] = datetime.utcnow().isoformat() + "Z"
                        lic["updated_at"] = datetime.utcnow().isoformat() + "Z"
                        self._save_data(data)
                        return True

        return False

    async def get_activations_count(self, key: str) -> int:
        """Get the number of activations for a license."""
        license_data = await self.get_license(key)
        if license_data:
            return len(license_data.activations)
        return 0
