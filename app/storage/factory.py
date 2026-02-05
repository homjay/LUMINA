"""Storage factory for creating storage instances."""
from app.storage.base import BaseStorage
from app.storage.json_storage import JSONStorage
from app.storage.sqlite_storage import SQLiteStorage
from app.storage.mysql_storage import MySQLStorage
from app.core.config import settings


def get_storage() -> BaseStorage:
    """Get storage instance based on configuration."""
    storage_type = settings.storage.type.lower()

    if storage_type == "json":
        return JSONStorage()
    elif storage_type == "sqlite":
        return SQLiteStorage()
    elif storage_type == "mysql":
        return MySQLStorage()
    else:
        raise ValueError(f"Unsupported storage type: {storage_type}")


# Global storage instance
storage = get_storage()
