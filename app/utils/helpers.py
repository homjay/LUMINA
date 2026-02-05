"""Helper utility functions."""
from datetime import datetime
from typing import Optional


def is_license_expired(expiry_date: Optional[datetime]) -> bool:
    """Check if a license is expired.

    Args:
        expiry_date: License expiry date

    Returns:
        True if expired, False otherwise
    """
    if not expiry_date:
        return False

    now = datetime.utcnow().replace(tzinfo=expiry_date.tzinfo) if expiry_date.tzinfo else datetime.utcnow()
    return now > expiry_date


def calculate_expiry_date(days: int) -> datetime:
    """Calculate expiry date from current date.

    Args:
        days: Number of days from now

    Returns:
        Expiry datetime
    """
    from datetime import timedelta
    return datetime.utcnow() + timedelta(days=days)


def format_datetime(dt: Optional[datetime]) -> str:
    """Format datetime for display.

    Args:
        dt: DateTime to format

    Returns:
        Formatted string
    """
    if not dt:
        return "Never"

    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def get_client_ip(request) -> str:
    """Get client IP address from request headers.

    Args:
        request: FastAPI request object

    Returns:
        Client IP address
    """
    # Check for forwarded headers (proxy/load balancer)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fallback to client host
    if request.client:
        return request.client.host

    return "unknown"


def mask_license_key(key: str, show_first: int = 4, show_last: int = 4) -> str:
    """Mask a license key for display.

    Args:
        key: License key
        show_first: Number of characters to show at start
        show_last: Number of characters to show at end

    Returns:
        Masked license key
    """
    if not key:
        return ""

    if len(key) <= show_first + show_last:
        return key

    parts = key.split('-')
    if len(parts) == 3:
        # Format: PREFIX-YYYY-CODE
        prefix, year, code = parts
        masked_code = code[:show_last] + '*' * (len(code) - show_last)
        return f"{prefix}-{year}-{masked_code}"

    # Generic masking
    start = key[:show_first]
    end = key[-show_last:]
    middle = '*' * (len(key) - show_first - show_last)
    return f"{start}{middle}{end}"


def days_until_expiry(expiry_date: Optional[datetime]) -> Optional[int]:
    """Calculate days until license expires.

    Args:
        expiry_date: License expiry date

    Returns:
        Days until expiry, or None if no expiry
    """
    if not expiry_date:
        return None

    delta = expiry_date - datetime.utcnow()
    return delta.days
