"""Configuration management for License Server."""

import os
from pathlib import Path
from typing import Any, Dict

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class AppConfig(BaseModel):
    """Application configuration."""

    name: str = "LUMINA"
    version: str = "1.0.0"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000


class MySQLConfig(BaseModel):
    """MySQL database configuration."""

    host: str = "localhost"
    port: int = 3306
    database: str = "license_server"
    user: str = "root"
    password: str = ""
    pool_size: int = 5
    max_overflow: int = 10


class StorageConfig(BaseModel):
    """Storage configuration."""

    type: str = "json"  # json, sqlite, mysql
    json_path: str = "data/licenses.json"
    sqlite_path: str = "data/licenses.db"
    mysql: MySQLConfig = Field(default_factory=MySQLConfig)


class SecurityConfig(BaseModel):
    """Security configuration."""

    admin_username: str = "admin"
    admin_password: str = "admin123"
    secret_key: str = "your-secret-key-change-this"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""

    enabled: bool = True
    requests_per_minute: int = 60


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str = "logs/license_server.log"
    max_bytes: int = 10485760  # 10MB
    backup_count: int = 5


class LicenseConfig(BaseModel):
    """License settings configuration."""

    default_max_activations: int = 1
    default_expiry_days: int = 365
    key_length: int = 16
    key_prefix: str = "LS"


class Settings(BaseSettings):
    """Application settings."""

    app: AppConfig = Field(default_factory=AppConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    license: LicenseConfig = Field(default_factory=LicenseConfig)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    config_file = Path(config_path)
    if not config_file.exists():
        return {}

    with open(config_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_settings() -> Settings:
    """Get application settings."""
    config_data = load_config()
    return Settings(**config_data)


# Global settings instance
settings = get_settings()

# Create necessary directories
Path("data").mkdir(exist_ok=True)
Path("logs").mkdir(exist_ok=True)
Path("config").mkdir(exist_ok=True)
