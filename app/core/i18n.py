"""Internationalization (i18n) support for LUMINA."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from app.core.config import settings


class I18nManager:
    """Internationalization manager for LUMINA."""

    def __init__(self):
        """Initialize i18n manager."""
        self.current_language = "en"  # Default to English
        self.fallback_language = "en"
        self.translations = {}
        self.load_translations()

    def load_translations(self):
        """Load translation files."""
        i18n_dir = Path(__file__).parent.parent / "i18n"

        # Create i18n directory if it doesn't exist
        i18n_dir.mkdir(exist_ok=True)

        # Load available languages
        for lang_file in i18n_dir.glob("*.json"):
            lang_code = lang_file.stem
            with open(lang_file, "r", encoding="utf-8") as f:
                self.translations[lang_code] = json.load(f)

    def set_language(self, language: str):
        """Set current language."""
        if language in self.translations:
            self.current_language = language
            return True
        return False

    def get_available_languages(self) -> Dict[str, str]:
        """Get available languages with their native names."""
        languages = {"en": "English", "zh": "中文"}

        # Add language names from translation files if available
        for lang_code, translations in self.translations.items():
            if "language_name" in translations:
                languages[lang_code] = translations["language_name"]

        return languages

    def translate(self, key: str, language: Optional[str] = None, **kwargs) -> str:
        """
        Translate a key to the specified language.

        Args:
            key: Translation key (dot-separated, e.g., "error.invalid_license")
            language: Target language code (uses current language if not specified)
            **kwargs: Format parameters for the translation

        Returns:
            Translated string or the key if translation not found
        """
        target_language = language or self.current_language

        # Try to get translation for the target language
        translation = self._get_nested_value(
            self.translations.get(target_language, {}), key
        )

        # Fallback to English if translation not found
        if translation is None and target_language != self.fallback_language:
            translation = self._get_nested_value(
                self.translations.get(self.fallback_language, {}), key
            )

        # Return the key if no translation found
        if translation is None:
            return key

        # Format the translation with provided parameters
        try:
            return translation.format(**kwargs) if kwargs else translation
        except (KeyError, ValueError):
            return translation

    def _get_nested_value(self, data: Dict[str, Any], key: str) -> Optional[str]:
        """Get nested value from dictionary using dot-separated key."""
        keys = key.split(".")
        current = data

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None

        return current if isinstance(current, str) else None


# Global i18n instance
i18n = I18nManager()


def _(key: str, **kwargs) -> str:
    """Shortcut function for translation."""
    return i18n.translate(key, **kwargs)


def set_language(language: str) -> bool:
    """Set current language."""
    return i18n.set_language(language)


def get_available_languages() -> Dict[str, str]:
    """Get available languages."""
    return i18n.get_available_languages()
