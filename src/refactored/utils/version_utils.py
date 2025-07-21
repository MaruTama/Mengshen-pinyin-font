# -*- coding: utf-8 -*-
"""Version utility functions for font metadata and project version management."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def get_project_version() -> str:
    """Get version from pyproject.toml with fallback mechanisms.

    Returns:
        Version string from pyproject.toml or fallback value

    Examples:
        >>> get_project_version()  # doctest: +SKIP
        "2.0.0"
    """
    try:
        # Try using importlib.metadata first (preferred for installed packages)
        if sys.version_info >= (3, 8):
            try:
                from importlib.metadata import (
                    version,  # pylint: disable=import-outside-toplevel
                )

                return version("mengshen-pinyin-font")
            except (ImportError, ModuleNotFoundError, FileNotFoundError, OSError):
                pass

        # Fallback: parse pyproject.toml directly

        # Find pyproject.toml in the project root
        current_dir = Path(__file__).parent
        project_root = (
            current_dir.parent.parent.parent
        )  # utils -> refactored -> src -> project_root
        pyproject_path = project_root / "pyproject.toml"

        if pyproject_path.exists():
            content = pyproject_path.read_text(encoding="utf-8")
            match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                return match.group(1)

        # Final fallback
        return "2.0.0"

    except (FileNotFoundError, OSError, ValueError, AttributeError):
        # Ultimate fallback if all else fails
        return "2.0.0"


def parse_version_to_float(version_str: str) -> float:
    """Convert semantic version string to float for font metadata.

    Args:
        version_str: Semantic version string (e.g., "2.0.0", "1.04")

    Returns:
        Float representation of the version (e.g., "2.0.0" -> 2.0)

    Examples:
        >>> parse_version_to_float("2.0.0")
        2.0
        >>> parse_version_to_float("1.04")
        1.04
        >>> parse_version_to_float("3")
        3.0
        >>> parse_version_to_float("invalid")
        1.0
    """
    try:
        # Split version and take major.minor parts
        parts = version_str.split(".")
        if len(parts) >= 2:
            return float(f"{parts[0]}.{parts[1]}")
        if len(parts) == 1:
            return float(parts[0])
        return 1.0  # fallback
    except (ValueError, IndexError):
        return 1.0  # fallback
