# -*- coding: utf-8 -*-
"""Version utility functions for font metadata."""

from __future__ import annotations


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
        elif len(parts) == 1:
            return float(parts[0])
        else:
            return 1.0  # fallback
    except (ValueError, IndexError):
        return 1.0  # fallback
