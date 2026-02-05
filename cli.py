#!/usr/bin/env python3
"""LUMINA CLI - Secure command line tool for license management.

All operations go through the authenticated API.
"""
import argparse
import sys
import requests


class LUMINAClient:
    """LUMINA API client."""

    def __init__(self, base_url="http://localhost:18000/api/v1"):
        self.base_url = base_url
        self.token = None

    def login(self, username, password):
        """Login and get access token."""
        response = requests.post(
            f"{self.base_url}/admin/login",
            json={"username": username, "password": password}
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


def main():
    parser = argparse.ArgumentParser(description="LUMINA License Management CLI")
    parser.add_argument("--url", default="http://localhost:18000/api/v1", help="API base URL")
    parser.add_argument("--username", help="Admin username (default: from ADMIN_USERNAME env var or 'admin')")
    parser.add_argument("--password", help="Admin password (default: from ADMIN_PASSWORD env var)")

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

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Get credentials from environment
    import os
    username = args.username or os.environ.get("ADMIN_USERNAME", "admin")
    password = args.password or os.environ.get("ADMIN_PASSWORD")

    if not password:
        password = input("Enter admin password: ")

    # Create client and login
    client = LUMINAClient(args.url)
    if not client.login(username, password):
        print("✗ Login failed: Invalid username or password")
        sys.exit(1)

    print(f"✓ Logged in as {username}")

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

    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
