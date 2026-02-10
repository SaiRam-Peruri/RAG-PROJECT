"""
Input validation and sanitization.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional


class ValidationError(ValueError):
    """Raised when input validation fails."""
    pass


def sanitize_opportunity_name(name: str) -> str:
    """
    Sanitize opportunity name to prevent path traversal and injection.
    Allows: alphanumeric, hyphens, underscores, dots, spaces.
    """
    if not name or not name.strip():
        raise ValidationError("Opportunity name cannot be empty")

    name = name.strip()

    # Block path traversal
    if ".." in name or "/" in name or "\\" in name:
        raise ValidationError(f"Invalid characters in opportunity name: {name}")

    # Allow only safe characters
    if not re.match(r'^[\w\-. ]+$', name):
        raise ValidationError(
            f"Opportunity name contains invalid characters: {name}. "
            "Allowed: alphanumeric, hyphens, underscores, dots, spaces."
        )

    if len(name) > 200:
        raise ValidationError(f"Opportunity name too long ({len(name)} chars, max 200)")

    return name


def validate_file_path(path: str | Path, must_exist: bool = True) -> Path:
    """Validate a file path is safe and optionally exists."""
    p = Path(path).resolve()

    # Block path traversal
    if ".." in str(path):
        raise ValidationError(f"Path traversal not allowed: {path}")

    if must_exist and not p.exists():
        raise ValidationError(f"File not found: {p}")

    return p


def validate_mode(mode: str) -> str:
    """Validate query mode."""
    mode = mode.strip().lower()
    if mode not in ("auth", "draft"):
        raise ValidationError(f"Mode must be 'auth' or 'draft', got: {mode}")
    return mode


def validate_section_type(section_type: str) -> str:
    """Validate proposal section type."""
    valid = {
        "technical", "management", "past_performance", "executive_summary",
        "staffing", "quality_assurance", "security", "transition", "cost",
    }
    section_type = section_type.strip().lower()
    if section_type not in valid:
        raise ValidationError(
            f"Invalid section type: {section_type}. Valid: {', '.join(sorted(valid))}"
        )
    return section_type


def validate_positive_int(value: int, name: str, max_val: int = 10000) -> int:
    """Validate a positive integer within bounds."""
    if not isinstance(value, int) or value < 1 or value > max_val:
        raise ValidationError(f"{name} must be between 1 and {max_val}, got: {value}")
    return value
