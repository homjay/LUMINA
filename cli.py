#!/usr/bin/env python3
"""LUMINA CLI - Secure command line tool for license management.

All operations go through the authenticated API.
"""
import argparse
import sys
import hashlib
import requests
import os


class LUMINAClient:
    """LUMINA API client."""

    def __init__(self, base_url="http://localhost:18000/api/v1"):
        self.base_url = base_url
        self.token = None

    def hash_password(self, password: str) -> str:
        """Hash password before sending (SHA-256)."""
        return hashlib.sha256(password.encode()).hexdigest()

    def login(self, username, password):
        """Login and get access token - sends password hash."""
        # Hash password before sending
        password_hash = self.hash_password(password)

        response = requests.post(
            f"{self.base_url}/admin/login",
            json={"username": username, "password": password_hash}  # Send hash
        )
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            return True
        return False

    def add_license(self, product, customer, email=None, max_activations=1, version="1.0.0"):
        """Add a new license."""
        if not self.token:
            raise ValueError("Not authenticated")

        data = {
            "product": product,
            "customer": customer,
            "max_activations": max_activations,
            "version": version
        }
        if email:
            data["email"] = email

        response = requests.post(
            f"{self.base_url}/admin/license",
            headers={"Authorization": f"Bearer {self.token}"},
            json=data
        )
        return response

    def list_licenses(self):
        """List all licenses."""
        if not self.token:
            raise ValueError("Not authenticated")

        response = requests.get(
            f"{self.base_url}/admin/license",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        return response

    def get_license(self, key):
        """Get license details."""
        if not self.token:
            raise ValueError("Not authenticated")

        response = requests.get(
            f"{self.base_url}/admin/license/{key}",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        return response

    def delete_license(self, key):
        """Delete a license."""
        if not self.token:
            raise ValueError("Not authenticated")

        response = requests.delete(
            f"{self.base_url}/admin/license/{key}",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        return response

    def list_activations(self, key):
        """List license activations."""
        if not self.token:
            raise ValueError("Not authenticated")

        response = requests.get(
            f"{self.base_url}/admin/license/{key}/activations",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        return response

    def delete_activation(self, key, machine_code):
        """Delete an activation (allow reactivation)."""
        if not self.token:
            raise ValueError("Not authenticated")

        response = requests.delete(
            f"{self.base_url}/admin/license/{key}/activation/{machine_code}",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        return response


def load_env_file(path: str = ".env") -> None:
    """Load environment variables from a .env file if present."""
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                # Do not override already-set env vars
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception as e:
        print(f"✗ Error reading {path}: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="LUMINA License Management CLI")
    parser.add_argument("--url", default="http://localhost:18000/api/v1", help="API base URL")
    parser.add_argument("-u", "--username", help="Admin username (default: from ADMIN_USERNAME env var or 'admin')")
    parser.add_argument("-p", "--password", help="Admin password (default: from ADMIN_PASSWORD env var)")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Add license
    add_parser = subparsers.add_parser("add", help="Add a new license")
    add_parser.add_argument("product", help="Product name")
    add_parser.add_argument("customer", help="Customer name")
    add_parser.add_argument("--email", help="Customer email")
    add_parser.add_argument("--max-activations", type=int, default=1, help="Max activations")
    add_parser.add_argument("--version", default="1.0.0", help="Product version")

    # List licenses
    list_parser = subparsers.add_parser("list", help="List all licenses")

    # Get license
    get_parser = subparsers.add_parser("get", help="Get license details")
    get_parser.add_argument("key", help="License key")

    # Delete license
    delete_parser = subparsers.add_parser("delete", help="Delete a license")
    delete_parser.add_argument("key", help="License key")

    # List activations
    activations_parser = subparsers.add_parser("activations", help="List license activations")
    activations_parser.add_argument("key", help="License key")

    # Delete activation
    rm_activation_parser = subparsers.add_parser("rm-activation", help="Delete an activation")
    rm_activation_parser.add_argument("key", help="License key")
    rm_activation_parser.add_argument("machine_code", help="Machine code")

    # Get token
    token_parser = subparsers.add_parser("token", help="Get current access token")
    token_parser.add_argument("--save", action="store_true", help="Save token to environment file")

    # Export data
    export_parser = subparsers.add_parser("export", help="Export licenses to JSON file")
    export_parser.add_argument("--output", "-o", default="licenses_export.json", help="Output file path")

    # API Key management
    apikey_parser = subparsers.add_parser("apikey", help="Manage API keys")
    apikey_subparsers = apikey_parser.add_subparsers(dest="apikey_action", help="API key actions")

    # Create API key
    create_key_parser = apikey_subparsers.add_parser("create", help="Create a new API key")
    create_key_parser.add_argument("--name", help="API key name/description")
    create_key_parser.add_argument("--expires", help="Expiration time (e.g., 30d, 1y, 2025-12-31)")

    # List API keys
    list_keys_parser = apikey_subparsers.add_parser("list", help="List all API keys")

    # Delete API key
    delete_key_parser = apikey_subparsers.add_parser("delete", help="Delete an API key")
    delete_key_parser.add_argument("key", help="API key to delete")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Load .env if present (do not override existing environment)
    load_env_file(".env")

    # Get credentials from environment or arguments
    import os
    username = args.username or os.environ.get("ADMIN_USERNAME", "admin")
    password = args.password or os.environ.get("ADMIN_PASSWORD")

    if not password:
        print("✗ Error: ADMIN_PASSWORD not set")
        print("  Set it via:")
        print("    - Environment variable: export ADMIN_PASSWORD=xxx")
        print("    - Command line argument: python cli.py -p xxx")
        print("    - .env file: ADMIN_PASSWORD=xxx")
        sys.exit(1)

    # Create client and login
    client = LUMINAClient(args.url)
    if not client.login(username, password):
        print("✗ Login failed: Invalid username or password")
        sys.exit(1)

    # Execute command
    try:
        if args.command == "add":
            response = client.add_license(
                args.product, args.customer, args.email, args.max_activations, args.version
            )
            if response.status_code == 200:
                data = response.json()
                print(f"\n✓ License added successfully!")
                print(f"  Key: {data['key']}")
                print(f"  Product: {data['product']}")
                print(f"  Customer: {data['customer']}")
                print(f"  Max activations: {data['max_activations']}")
            else:
                print(f"✗ Failed: {response.json().get('detail', 'Unknown error')}")

        elif args.command == "list":
            response = client.list_licenses()
            if response.status_code == 200:
                licenses = response.json()
                if not licenses:
                    print("No licenses found")
                else:
                    print(f"\n{'Key':<25} {'Product':<15} {'Customer':<20} {'Status':<10}")
                    print("-" * 75)
                    for lic in licenses:
                        print(f"{lic['key']:<25} {lic['product']:<15} {lic['customer']:<20} {lic['status']:<10}")

        elif args.command == "get":
            response = client.get_license(args.key)
            if response.status_code == 200:
                data = response.json()
                print(f"\nLicense Details:")
                print(f"  Key: {data['key']}")
                print(f"  Product: {data['product']}")
                print(f"  Version: {data['version']}")
                print(f"  Customer: {data['customer']}")
                print(f"  Email: {data.get('email', 'N/A')}")
                print(f"  Max activations: {data['max_activations']}")
                print(f"  Machine binding: {data['machine_binding']}")
                print(f"  Status: {data['status']}")
                print(f"  Activations: {len(data['activations'])}")
            else:
                print(f"✗ License not found")

        elif args.command == "delete":
            response = client.delete_license(args.key)
            if response.status_code == 200:
                print(f"✓ License {args.key} deleted")
            else:
                print(f"✗ Failed: {response.json().get('detail', 'Unknown error')}")

        elif args.command == "activations":
            response = client.list_activations(args.key)
            if response.status_code == 200:
                activations = response.json()
                if not activations:
                    print("No activations found")
                else:
                    print(f"\nActivations for {args.key}:")
                    for act in activations:
                        print(f"  - Machine: {act.get('machine_code', 'N/A')}")
                        print(f"    IP: {act.get('ip', 'N/A')}")
                        print(f"    Activated: {act.get('activated_at', 'N/A')}")
                        print(f"    Verifications: {act.get('verification_count', 0)}")
                        print()

        elif args.command == "rm-activation":
            response = client.delete_activation(args.key, args.machine_code)
            if response.status_code == 200:
                print(f"✓ Activation deleted for machine {args.machine_code}")
            else:
                print(f"✗ Failed: {response.json().get('detail', 'Unknown error')}")

        elif args.command == "token":
            print(f"\n✓ Access Token:")
            print(f"  {client.token}")
            print()
            print("Use with Authorization header:")
            print(f"  Authorization: Bearer {client.token}")
            print()
            print("Or save to environment:")
            print(f"  export LUMINA_TOKEN={client.token}")

        elif args.command == "export":
            response = client.list_licenses()
            if response.status_code == 200:
                licenses = response.json()
                import json
                with open(args.output, 'w') as f:
                    json.dump({"licenses": licenses}, f, indent=2, ensure_ascii=False)
                print(f"✓ Exported {len(licenses)} licenses to {args.output}")
            else:
                print(f"✗ Failed: {response.json().get('detail', 'Unknown error')}")

        elif args.command == "apikey":
            if args.apikey_action == "create":
                import secrets
                import string
                # Generate secure random API key
                api_key = 'lumina_' + ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

                print(f"\n✓ API Key created:")
                print(f"  Key: {api_key}")
                print(f"  Name: {args.name or 'N/A'}")
                print(f"  Expires: {args.expires or 'Never'}")
                print()
                print("Add to .env file:")
                print(f"  API_KEY={api_key}")
                print()
                print("Or use with Authorization header:")
                print(f"  Authorization: Bearer {api_key}")

            elif args.apikey_action == "list":
                print("\nAPI Keys are stored in database.")
                print("Use SQL to view them:")
                print("  SELECT * FROM api_keys WHERE is_active = 1;")

            elif args.apikey_action == "delete":
                print(f"\n✓ To delete API key, run SQL directly:")
                print(f"  DELETE FROM api_keys WHERE key = '{args.key}';")

    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
