#!/usr/bin/env python3
"""
LUMINA Command Line Interface
License Unified Management & Identity Network Authorization

A unified CLI tool for managing LUMINA license server operations.

Usage:
    python lumina_cli.py <command> [options]

Commands:
    license     Manage licenses (add, list, etc.)
    migrate     Migrate data between storage formats
    server      Start the license server
    config      Manage configuration

Use --help with any command for more information.
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))


def create_parser():
    """Create the main argument parser."""
    parser = argparse.ArgumentParser(
        prog="lumina_cli",
        description="LUMINA Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # License command
    license_parser = subparsers.add_parser("license", help="Manage licenses")
    license_subparsers = license_parser.add_subparsers(
        dest="license_action", help="License actions"
    )

    # Add license
    add_parser = license_subparsers.add_parser("add", help="Add a new license")
    add_parser.add_argument("product", help="Product name")
    add_parser.add_argument("customer", help="Customer name")
    add_parser.add_argument("--email", help="Customer email")
    add_parser.add_argument(
        "--max-activations",
        type=int,
        default=1,
        help="Maximum activations (default: 1)",
    )
    add_parser.add_argument(
        "--version", default="1.0.0", help="Product version (default: 1.0.0)"
    )

    # List licenses
    list_parser = license_subparsers.add_parser("list", help="List all licenses")
    list_parser.add_argument(
        "--format", choices=["table", "json"], default="table", help="Output format"
    )

    # Migrate command
    migrate_parser = subparsers.add_parser(
        "migrate", help="Migrate data between storage formats"
    )
    migrate_parser.add_argument(
        "--source",
        default="data/licenses.json",
        help="Source JSON file (default: data/licenses.json)",
    )
    migrate_parser.add_argument(
        "--target",
        choices=["sqlite", "mysql"],
        default="sqlite",
        help="Target database type (default: sqlite)",
    )
    migrate_parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="Configuration file (default: config/config.yaml)",
    )
    migrate_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually doing it",
    )
    migrate_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed information during migration",
    )

    # Server command
    server_parser = subparsers.add_parser("server", help="Start the license server")
    server_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    server_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    server_parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    server_parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload for development"
    )

    # Config command
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_subparsers = config_parser.add_subparsers(
        dest="config_action", help="Configuration actions"
    )

    # Show config
    show_config_parser = config_subparsers.add_parser(
        "show", help="Show current configuration"
    )

    # Init config
    init_config_parser = config_subparsers.add_parser(
        "init", help="Initialize configuration file"
    )
    init_config_parser.add_argument(
        "--force", action="store_true", help="Overwrite existing config file"
    )

    return parser


async def handle_license_add(args):
    """Handle license add command."""
    from add_license import add_license as add_license_func

    print(f"Adding license for product: {args.product}")
    print(f"Customer: {args.customer}")
    if args.email:
        print(f"Email: {args.email}")
    print(f"Max activations: {args.max_activations}")
    print(f"Version: {args.version}")
    print()

    success = add_license_func(
        args.product, args.customer, args.email, args.max_activations, args.version
    )

    if success:
        print("✓ License added successfully!")
    else:
        print("✗ Failed to add license")
        sys.exit(1)


async def handle_license_list(args):
    """Handle license list command."""
    from app.storage.factory import get_storage

    # Get storage instance
    storage = await get_storage()

    # Get all licenses
    licenses = await storage.get_all_licenses()

    if args.format == "json":
        import json
        from app.models.schemas import License

        # Convert to JSON-serializable format
        licenses_data = []
        for license in licenses:
            license_dict = license.model_dump(mode="json")
            licenses_data.append(license_dict)

        print(json.dumps(licenses_data, indent=2, ensure_ascii=False))
    else:
        # Table format
        if not licenses:
            print("No licenses found.")
            return

        # Print table header
        print(
            f"{'Key':<25} {'Product':<15} {'Customer':<20} {'Activations':<10} {'Status':<10}"
        )
        print("-" * 85)

        # Print licenses
        for license in licenses:
            activation_count = len(license.activations)
            print(
                f"{license.key:<25} {license.product:<15} {license.customer:<20} {activation_count:<10} {license.status:<10}"
            )


async def handle_migrate(args):
    """Handle migrate command."""
    from tools.migrate_to_db import DataMigrator

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


async def handle_server(args):
    """Handle server command."""
    import uvicorn

    print(f"Starting LUMINA server on {args.host}:{args.port}")
    if args.debug:
        print("Debug mode enabled")
    if args.reload:
        print("Auto-reload enabled")

    uvicorn.run(
        "main:app", host=args.host, port=args.port, debug=args.debug, reload=args.reload
    )


def handle_config_show(args):
    """Handle config show command."""
    from app.core.config import get_settings

    settings = get_settings()

    print("Current Configuration:")
    print("=" * 50)
    print(f"App Name: {settings.app.name}")
    print(f"Version: {settings.app.version}")
    print(f"Debug: {settings.app.debug}")
    print(f"Host: {settings.app.host}")
    print(f"Port: {settings.app.port}")
    print()
    print(f"Storage Type: {settings.storage.type}")
    if settings.storage.type == "json":
        print(f"JSON Path: {settings.storage.json_path}")
    elif settings.storage.type == "sqlite":
        print(f"SQLite Path: {settings.storage.sqlite_path}")
    elif settings.storage.type == "mysql":
        print(f"MySQL Host: {settings.storage.mysql.host}")
        print(f"MySQL Database: {settings.storage.mysql.database}")
    print()
    print(f"Admin Username: {settings.security.admin_username}")
    print(f"Token Algorithm: {settings.security.algorithm}")
    print(f"Token Expires: {settings.security.access_token_expire_minutes} minutes")


def handle_config_init(args):
    """Handle config init command."""
    import shutil
    from pathlib import Path

    config_file = Path("config/config.yaml")
    example_file = Path("config/config.yaml.example")

    if config_file.exists() and not args.force:
        print("Configuration file already exists. Use --force to overwrite.")
        return

    if not example_file.exists():
        print("Example configuration file not found.")
        return

    # Create config directory if it doesn't exist
    config_file.parent.mkdir(parents=True, exist_ok=True)

    # Copy example file to config file
    shutil.copy2(example_file, config_file)

    print(f"Configuration file initialized at: {config_file}")
    print("Please edit the file to set your configuration.")


async def main():
    """Main CLI function."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "license":
            if args.license_action == "add":
                await handle_license_add(args)
            elif args.license_action == "list":
                await handle_license_list(args)
            else:
                parser.print_help()
                sys.exit(1)

        elif args.command == "migrate":
            await handle_migrate(args)

        elif args.command == "server":
            await handle_server(args)

        elif args.command == "config":
            if args.config_action == "show":
                handle_config_show(args)
            elif args.config_action == "init":
                handle_config_init(args)
            else:
                parser.print_help()
                sys.exit(1)

        else:
            parser.print_help()
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
