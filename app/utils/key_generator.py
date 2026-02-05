"""License key generation utilities."""
import random
import string
from datetime import datetime
from typing import Optional

from app.core.config import settings


def generate_license_key(prefix: Optional[str] = None, length: Optional[int] = None) -> str:
    """Generate a unique license key.

    Args:
        prefix: Custom prefix (default from config)
        length: Key length without prefix (default from config)

    Returns:
        A unique license key in format: PREFIX-YYYY-XXXXXXXX
    """
    prefix = prefix or settings.license.key_prefix
    length = length or settings.license.key_length
    year = datetime.now().year

    # Generate random alphanumeric string
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(random.choice(chars) for _ in range(length))

    # Remove ambiguous characters
    for ambiguous in ['O', '0', 'I', '1']:
        random_part = random_part.replace(ambiguous, random.choice(string.ascii_uppercase))

    return f"{prefix}-{year}-{random_part}"


def validate_license_key(key: str) -> bool:
    """Validate license key format.

    Args:
        key: License key to validate

    Returns:
        True if format is valid, False otherwise
    """
    if not key:
        return False

    parts = key.split('-')
    if len(parts) != 3:
        return False

    prefix, year, code = parts

    # Check if year is valid
    try:
        year_int = int(year)
        if year_int < 2020 or year_int > 2100:
            return False
    except ValueError:
        return False

    # Check if code is alphanumeric
    if not code.isalnum():
        return False

    return True
