"""Input validation utilities."""
import re
from typing import List, Optional
from ipaddress import IPv4Address, IPv6Address, ip_address, AddressValueError


def validate_email(email: str) -> bool:
    """Validate email address format."""
    if not email:
        return True  # Email is optional

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_ip_address(ip: str) -> bool:
    """Validate IP address (IPv4 or IPv6)."""
    if not ip:
        return True  # IP is optional

    try:
        ip_address(ip)
        return True
    except (ValueError, AddressValueError):
        return False


def validate_ip_whitelist(ip_list: List[str]) -> bool:
    """Validate a list of IP addresses."""
    return all(validate_ip_address(ip) for ip in ip_list)


def validate_machine_code(code: Optional[str]) -> bool:
    """Validate machine code format.

    Machine code should be a non-empty alphanumeric string with optional hyphens.
    """
    if not code:
        return True  # Machine code is optional

    if len(code) < 10 or len(code) > 100:
        return False

    # Allow alphanumeric, hyphens, and underscores
    pattern = r'^[a-zA-Z0-9\-_]+$'
    return re.match(pattern, code) is not None


def sanitize_string(input_str: str, max_length: int = 255) -> str:
    """Sanitize string input."""
    if not input_str:
        return ""

    # Remove null bytes and trim
    sanitized = input_str.replace('\x00', '').strip()

    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized


def validate_product_name(name: str) -> bool:
    """Validate product name."""
    if not name or len(name) < 2 or len(name) > 100:
        return False

    # Allow alphanumeric, spaces, hyphens, and underscores
    pattern = r'^[a-zA-Z0-9\s\-_]+$'
    return re.match(pattern, name) is not None


def validate_customer_name(name: str) -> bool:
    """Validate customer name."""
    if not name or len(name) < 2 or len(name) > 100:
        return False

    # Allow letters, spaces, hyphens, and periods
    pattern = r'^[a-zA-Z\s\-\.]+$'
    return re.match(pattern, name) is not None
