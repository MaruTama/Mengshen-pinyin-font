# -*- coding: utf-8 -*-
"""Version utility functions for font metadata and project version management."""

from __future__ import annotations

import re
import sys
from importlib.metadata import version
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
                pkg_version = version("mengshen-pinyin-font")
                if pkg_version:
                    return pkg_version
            except (ImportError, ModuleNotFoundError, FileNotFoundError, OSError):
                # Package not installed or metadata not accessible
                pass

        # Fallback: parse pyproject.toml directly
        # Find pyproject.toml in the project root
        current_dir = Path(__file__).parent
        project_root = (
            current_dir.parent.parent.parent
        )  # utils -> refactored -> src -> project_root
        pyproject_path = project_root / "pyproject.toml"

        # Try to read and parse the file
        try:
            if pyproject_path.exists():
                content = pyproject_path.read_text(encoding="utf-8")
                # More robust regex to handle different quote styles and spacing
                match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    return match.group(1)
        except (OSError, UnicodeDecodeError):
            pass

    except (FileNotFoundError, OSError, UnicodeDecodeError, AttributeError):
        # File system errors, encoding issues, or path resolution failures
        pass

    # Final fallback
    return "2.0.0"


def parse_version_to_float(version_str: str | None) -> float:
    """Convert semantic version string to float for font metadata.

    Args:
        version_str: Semantic version string (e.g., "2.0.0", "1.04", "2.0.1") or None

    Returns:
        Float representation including patch version (e.g., "2.0.1" -> 2.01)

    Examples:
        >>> parse_version_to_float("2.0.0")
        2.0
        >>> parse_version_to_float("2.0.1")
        2.01
        >>> parse_version_to_float("1.04")
        1.04
        >>> parse_version_to_float("3")
        3.0
        >>> parse_version_to_float("invalid")
        1.0
        >>> parse_version_to_float(None)
        1.0
    """
    # Handle None input
    if version_str is None:
        return 1.0

    try:
        # Split version and include patch version
        parts = version_str.split(".")
        if len(parts) >= 3:
            # Include patch version: "2.0.1" -> 2.01
            major = int(parts[0])
            minor = int(parts[1])
            patch = int(parts[2])
            # Format as font-appropriate version: 2.01
            if patch == 0:
                return float(f"{major}.{minor}")
            return float(f"{major}.{minor:01d}{patch}")
        if len(parts) >= 2:
            return float(f"{parts[0]}.{parts[1]}")
        if len(parts) == 1:
            return float(parts[0])
        return 1.0  # fallback
    except (ValueError, IndexError, AttributeError):
        return 1.0  # fallback
