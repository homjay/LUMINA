#!/usr/bin/env python3
"""
Migration script for LUMINA
License Unified Management & Identity Network Authorization

This script migrates license data from JSON file to database (SQLite or MySQL).

Usage:
    python migrate_to_db.py [options]

Options:
    --source FILE        Source JSON file (default: data/json/licenses.json)
    --target TYPE       Target database type: sqlite or mysql (default: sqlite)
    --config FILE       Configuration file (default: config/config.yaml)
    --dry-run           Show what would be done without actually doing it
    --verbose           Show detailed information during migration
    --help              Show this help message
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

import yaml
from pydantic import BaseModel

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.storage.json_storage import JSONStorage
from app.storage.sqlite_storage import SQLiteStorage
from app.storage.mysql_storage import MySQLStorage
from app.core.config import Settings, get_settings


class MigrationStats(BaseModel):
    """Migration statistics."""

    total_licenses: int = 0
    migrated_licenses: int = 0
    skipped_licenses: int = 0
    failed_licenses: int = 0
    total_activations: int = 0
    migrated_activations: int = 0


class DataMigrator:
    """Data migration utility."""

    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize migrator with configuration."""
        self.config = self._load_config(config_path)
        self.stats = MigrationStats()

    def _load_config(self, config_path: str) -> Settings:
        """Load configuration from YAML file."""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_file, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}

        return Settings(**config_data)

    def _load_json_data(self, json_path: str) -> Dict[str, Any]:
        """Load data from JSON file."""
        json_file = Path(json_path)
        if not json_file.exists():
            raise FileNotFoundError(f"JSON file not found: {json_path}")

        with open(json_file, "r", encoding="utf-8") as f:
            return json.load(f)

    async def migrate_to_sqlite(
        self,
        json_data: Dict[str, Any],
        db_path: str,
        dry_run: bool = False,
        verbose: bool = False,
    ):
        """Migrate data from JSON to SQLite database."""
        if verbose:
            print(f"Target SQLite database: {db_path}")

        if not dry_run:
            # Initialize SQLite storage
            storage = SQLiteStorage(db_path)
            await storage._ensure_initialized()

        # Process licenses
        licenses = json_data.get("licenses", [])
        self.stats.total_licenses = len(licenses)

        if verbose:
            print(f"Found {self.stats.total_licenses} licenses to migrate")

        for license_data in licenses:
            try:
                # Convert JSON license to LicenseCreate schema
                from app.models.schemas import LicenseCreate

                # Parse dates
                expiry_date = None
                if license_data.get("expiry_date"):
                    expiry_date_str = license_data["expiry_date"]
                    if expiry_date_str.endswith("Z"):
                        expiry_date_str = expiry_date_str[:-1]
                    expiry_date = datetime.fromisoformat(expiry_date_str)

                # Create license data
                license_create = LicenseCreate(
                    key=license_data["key"],
                    product=license_data["product"],
                    version=license_data.get("version", "1.0.0"),
                    customer=license_data["customer"],
                    email=license_data.get("email"),
                    max_activations=license_data.get("max_activations", 1),
                    machine_binding=license_data.get("machine_binding", True),
                    ip_whitelist=license_data.get("ip_whitelist", []),
                    expiry_date=expiry_date,
                )

                # Count activations
                activations = license_data.get("activations", [])
                self.stats.total_activations += len(activations)

                if not dry_run:
                    # Create license in database
                    created_license = await storage.create_license(license_create)

                    # Add activations
                    for activation in activations:
                        try:
                            # Parse activation datetime
                            activated_at_str = activation["activated_at"]
                            if activated_at_str.endswith("Z"):
                                activated_at_str = activated_at_str[:-1]
                            activated_at = datetime.fromisoformat(activated_at_str)

                            # Temporarily set the created_at to match activation time
                            original_created_at = created_license.created_at
                            created_license.created_at = activated_at

                            # Add activation
                            await storage.add_activation(
                                created_license.key,
                                activation.get("machine_code"),
                                activation.get("ip"),
                            )

                            # Restore original created_at
                            created_license.created_at = original_created_at

                            self.stats.migrated_activations += 1

                        except Exception as e:
                            if verbose:
                                print(f"  Warning: Failed to migrate activation: {e}")

                self.stats.migrated_licenses += 1

                if verbose:
                    print(f"  ✓ Migrated license: {license_data['key']}")

            except Exception as e:
                self.stats.failed_licenses += 1
                if verbose:
                    print(
                        f"  ✗ Failed to migrate license {license_data.get('key', 'unknown')}: {e}"
                    )

    async def migrate_to_mysql(
        self, json_data: Dict[str, Any], dry_run: bool = False, verbose: bool = False
    ):
        """Migrate data from JSON to MySQL database."""
        mysql_config = self.config.storage.mysql

        if verbose:
            print(
                f"Target MySQL database: {mysql_config.host}:{mysql_config.port}/{mysql_config.database}"
            )

        if not dry_run:
            # Initialize MySQL storage
            storage = MySQLStorage()
            await storage._ensure_initialized()

        # Process licenses (same logic as SQLite)
        licenses = json_data.get("licenses", [])
        self.stats.total_licenses = len(licenses)

        if verbose:
            print(f"Found {self.stats.total_licenses} licenses to migrate")

        for license_data in licenses:
            try:
                # Convert JSON license to LicenseCreate schema
                from app.models.schemas import LicenseCreate

                # Parse dates
                expiry_date = None
                if license_data.get("expiry_date"):
                    expiry_date_str = license_data["expiry_date"]
                    if expiry_date_str.endswith("Z"):
                        expiry_date_str = expiry_date_str[:-1]
                    expiry_date = datetime.fromisoformat(expiry_date_str)

                # Create license data
                license_create = LicenseCreate(
                    key=license_data["key"],
                    product=license_data["product"],
                    version=license_data.get("version", "1.0.0"),
                    customer=license_data["customer"],
                    email=license_data.get("email"),
                    max_activations=license_data.get("max_activations", 1),
                    machine_binding=license_data.get("machine_binding", True),
                    ip_whitelist=license_data.get("ip_whitelist", []),
                    expiry_date=expiry_date,
                )

                # Count activations
                activations = license_data.get("activations", [])
                self.stats.total_activations += len(activations)

                if not dry_run:
                    # Create license in database
                    created_license = await storage.create_license(license_create)

                    # Add activations
                    for activation in activations:
                        try:
                            # Parse activation datetime
                            activated_at_str = activation["activated_at"]
                            if activated_at_str.endswith("Z"):
                                activated_at_str = activated_at_str[:-1]
                            activated_at = datetime.fromisoformat(activated_at_str)

                            # Temporarily set the created_at to match activation time
                            original_created_at = created_license.created_at
                            created_license.created_at = activated_at

                            # Add activation
                            await storage.add_activation(
                                created_license.key,
                                activation.get("machine_code"),
                                activation.get("ip"),
                            )

                            # Restore original created_at
                            created_license.created_at = original_created_at

                            self.stats.migrated_activations += 1

                        except Exception as e:
                            if verbose:
                                print(f"  Warning: Failed to migrate activation: {e}")

                self.stats.migrated_licenses += 1

                if verbose:
                    print(f"  ✓ Migrated license: {license_data['key']}")

            except Exception as e:
                self.stats.failed_licenses += 1
                if verbose:
                    print(
                        f"  ✗ Failed to migrate license {license_data.get('key', 'unknown')}: {e}"
                    )

    def print_stats(self):
        """Print migration statistics."""
        print("\n=== Migration Statistics ===")
        print(f"Total licenses found: {self.stats.total_licenses}")
        print(f"Successfully migrated: {self.stats.migrated_licenses}")
        print(f"Failed to migrate: {self.stats.failed_licenses}")
        print(f"Total activations found: {self.stats.total_activations}")
        print(f"Successfully migrated activations: {self.stats.migrated_activations}")

        if self.stats.total_licenses > 0:
            success_rate = (
                self.stats.migrated_licenses / self.stats.total_licenses
            ) * 100
            print(f"Success rate: {success_rate:.1f}%")


async def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(
        description="Migrate LUMINA license data from JSON to database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--source",
        default="data/json/licenses.json",
        help="Source JSON file (default: data/json/licenses.json)",
    )

    parser.add_argument(
        "--target",
        choices=["sqlite", "mysql"],
        default="sqlite",
        help="Target database type (default: sqlite)",
    )

    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="Configuration file (default: config/config.yaml)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually doing it",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed information during migration",
    )

    args = parser.parse_args()

    try:
        # Initialize migrator
        migrator = DataMigrator(args.config)

        # Load JSON data
        if args.verbose:
            print(f"Loading data from {args.source}...")

        json_data = migrator._load_json_data(args.source)

        if args.verbose:
            print(f"Loaded {len(json_data.get('licenses', []))} licenses from JSON")

        # Perform migration
        if args.target == "sqlite":
            db_path = migrator.config.storage.sqlite_path
            if args.verbose:
                print(f"Migrating to SQLite database: {db_path}")

            if args.dry_run:
                print("DRY RUN: No actual changes will be made")

            await migrator.migrate_to_sqlite(
                json_data, db_path, args.dry_run, args.verbose
            )

        elif args.target == "mysql":
            if args.verbose:
                print("Migrating to MySQL database...")

            if args.dry_run:
                print("DRY RUN: No actual changes will be made")

            await migrator.migrate_to_mysql(json_data, args.dry_run, args.verbose)

        # Print statistics
        migrator.print_stats()

        if args.dry_run:
            print("\nDRY RUN completed. Use --verbose for more details.")
        else:
            if migrator.stats.failed_licenses == 0:
                print("\n✓ Migration completed successfully!")
            else:
                print(
                    f"\n⚠ Migration completed with {migrator.stats.failed_licenses} errors."
                )
                print("  Check the verbose output for details.")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
