"""Configuration management for License Server."""

import os
import shutil
import logging
from pathlib import Path
from typing import Any, Dict

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class AppConfig(BaseModel):
    """Application configuration."""

    name: str = "LUMINA"
    version: str = "1.0.0"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000


class MySQLConfig(BaseSettings):
    """MySQL database configuration."""

    host: str = Field(default="localhost", env="MYSQL_HOST")
    port: int = Field(default=3306, env="MYSQL_PORT")
    database: str = Field(default="license_server", env="MYSQL_DATABASE")
    user: str = Field(default="root", env="MYSQL_USER")
    password: str = Field(default="", env="MYSQL_PASSWORD")
    pool_size: int = 5
    max_overflow: int = 10


class StorageConfig(BaseModel):
    """Storage configuration."""

    type: str = "json"  # json, sqlite, mysql
    json_path: str = "data/licenses.json"
    sqlite_path: str = "data/licenses.db"
    mysql: MySQLConfig = Field(default_factory=MySQLConfig)


class SecurityConfig(BaseSettings):
    """Security configuration."""

    admin_username: str = Field(default="admin", env="ADMIN_USERNAME")
    admin_password: str = Field(default="admin123", env="ADMIN_PASSWORD")
    secret_key: str = Field(default="your-secret-key-change-this", env="SECRET_KEY")
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


def ensure_config_exists() -> None:
    """Ensure configuration file exists.

    Strategy:
    1. If data/config.yaml exists → do nothing (keep user config)
    2. If data/config.yaml missing → copy from config/config.yaml.example
    3. If example also missing → create from default values

    This ensures first-time deployment gets a config file,
    but existing configs are never overwritten.
    """
    user_config_path = Path("data/config.yaml")
    example_config_path = Path("config/config.yaml.example")

    # Case 1: User config already exists - DO NOT TOUCH!
    if user_config_path.exists():
        logger.info(f"Using existing config: {user_config_path}")
        return

    # Case 2: Config missing, try to copy from example
    logger.warning(f"Config file not found: {user_config_path}")

    if example_config_path.exists():
        try:
            # Ensure data directory exists
            user_config_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy example config
            shutil.copy2(example_config_path, user_config_path)
            logger.info(f"✓ Created config from example: {user_config_path}")
            logger.warning("⚠️  Please review and update data/config.yaml for production!")
        except Exception as e:
            logger.error(f"Failed to copy example config: {e}")
    else:
        # Case 3: Example also missing - create minimal config
        logger.warning("Example config not found, creating minimal config")
        try:
            user_config_path.parent.mkdir(parents=True, exist_ok=True)

            default_config = """# LUMINA Configuration
# Auto-generated - please customize for production!

app:
  name: "LUMINA"
  version: "1.0.0"
  debug: false
  host: "0.0.0.0"
  port: 18000

storage:
  type: json
  json:
    path: "data/licenses.json"

security:
  admin_username: "admin"
  admin_password: "admin123"  # ⚠️ CHANGE THIS!
  secret_key: "your-secret-key-change-this"  # ⚠️ CHANGE THIS!

logging:
  level: "INFO"

license:
  default_max_activations: 1
  default_expiry_days: 365
  key_length: 16
  key_prefix: "LS"
"""
            with open(user_config_path, "w", encoding="utf-8") as f:
                f.write(default_config)
            logger.info(f"✓ Created default config: {user_config_path}")
            logger.warning("⚠️  Please review and update data/config.yaml!")
        except Exception as e:
            logger.error(f"Failed to create default config: {e}")


def load_config(config_path: str = "data/config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file.

    Searches in multiple locations:
    1. data/config.yaml (user config, not in git)
    2. config/config.yaml (fallback, for compatibility)
    """
    # Try user config first
    config_file = Path(config_path)
    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    # Fallback to old location
    fallback_path = Path("config/config.yaml")
    if fallback_path.exists():
        with open(fallback_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    return {}


def get_settings() -> Settings:
    """Get application settings."""
    # Ensure config file exists before loading
    ensure_config_exists()

    # Load configuration
    config_data = load_config()
    return Settings(**config_data)


# Global settings instance
settings = get_settings()

# Create necessary directories
Path("data").mkdir(exist_ok=True)
Path("logs").mkdir(exist_ok=True)
