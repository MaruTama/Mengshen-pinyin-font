# -*- coding: utf-8 -*-
# !/usr/bin/env python

"""
CMap (Character Map) utilities for font processing.

Contains functions for loading and working with font character mapping tables.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional

import orjson

from refactored.config.paths import DIR_TEMP

# Global cmap table cache
cmap_table: Dict[str, str] = {}


def get_cmap_table() -> None:
    """Load cmap table from template_main.json."""
    global cmap_table
    TEMPLATE_MAIN_JSON = os.path.join(DIR_TEMP, "template_main.json")
    with open(TEMPLATE_MAIN_JSON, "rb") as read_file:
        merged_font = orjson.loads(read_file.read())
    cmap_table = merged_font["cmap"]


def load_cmap_table_from_path(template_path: str) -> Dict[str, str]:
    """
    Load cmap table from specific template JSON file.

    Args:
        template_path: Path to template JSON file

    Returns:
        Character mapping table

    Raises:
        FileNotFoundError: If template file doesn't exist
        KeyError: If 'cmap' section not found in template
        RuntimeError: If loading fails
    """
    template_file = Path(template_path)

    if not template_file.exists():
        raise FileNotFoundError(f"Template file not found: {template_file}")

    try:
        with open(template_file, "rb") as f:
            template_data = orjson.loads(f.read())

        if "cmap" not in template_data:
            raise KeyError("No 'cmap' section found in template file")

        cmap_data = template_data["cmap"]
        if not isinstance(cmap_data, dict):
            raise TypeError(f"cmap data is not a dictionary: {type(cmap_data)}")
        return cmap_data

    except Exception as e:
        raise RuntimeError(f"Failed to load cmap table from {template_file}: {e}")


def set_cmap_table(new_cmap_table: Dict[str, str]) -> None:
    """
    Set the global cmap table.

    Args:
        new_cmap_table: New character mapping table
    """
    global cmap_table
    cmap_table = new_cmap_table


def clear_cmap_table() -> None:
    """Clear the global cmap table cache."""
    global cmap_table
    cmap_table = {}


# 漢字から cid を取得する
@lru_cache(maxsize=2048)
def convert_str_hanzi_2_cid(str_hanzi: str) -> str:
    """Convert hanzi character to CID with caching for performance."""
    if len(cmap_table) == 0:
        get_cmap_table()
    return cmap_table[str(ord(str_hanzi))]


def convert_hanzi_to_cid_safe(
    hanzi: str, cmap: Optional[Dict[str, str]] = None
) -> Optional[str]:
    """
    Safely convert hanzi character to CID with error handling.

    Args:
        hanzi: Single Chinese character
        cmap: Optional custom cmap table to use

    Returns:
        CID string if found, None if not found
    """
    if not hanzi or len(hanzi) != 1:
        return None

    # Use provided cmap or global cmap
    mapping_table = cmap if cmap else cmap_table

    # Load global cmap if empty and no custom cmap provided
    if not mapping_table and not cmap:
        get_cmap_table()
        mapping_table = cmap_table

    unicode_value = str(ord(hanzi))
    return mapping_table.get(unicode_value)


def get_unicode_from_cid(
    cid: str, cmap: Optional[Dict[str, str]] = None
) -> Optional[str]:
    """
    Get Unicode value from CID by reverse lookup.

    Args:
        cid: Character ID to look up
        cmap: Optional custom cmap table to use

    Returns:
        Unicode string if found, None if not found
    """
    # Use provided cmap or global cmap
    mapping_table = cmap if cmap else cmap_table

    # Load global cmap if empty and no custom cmap provided
    if not mapping_table and not cmap:
        get_cmap_table()
        mapping_table = cmap_table

    # Reverse lookup
    for unicode_str, mapped_cid in mapping_table.items():
        if mapped_cid == cid:
            return unicode_str

    return None


def get_hanzi_from_cid(
    cid: str, cmap: Optional[Dict[str, str]] = None
) -> Optional[str]:
    """
    Get hanzi character from CID.

    Args:
        cid: Character ID to look up
        cmap: Optional custom cmap table to use

    Returns:
        Hanzi character if found, None if not found
    """
    unicode_str = get_unicode_from_cid(cid, cmap)

    if unicode_str:
        try:
            return chr(int(unicode_str))
        except (ValueError, OverflowError):
            return None

    return None


def validate_cmap_table(cmap: Dict[str, str]) -> bool:
    """
    Validate cmap table structure.

    Args:
        cmap: Character mapping table to validate

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(cmap, dict):
        return False

    for unicode_str, cid in cmap.items():
        # Check that keys are valid Unicode values
        try:
            unicode_value = int(unicode_str)
            if unicode_value < 0:
                return False
        except ValueError:
            return False

        # Check that values are valid CID strings
        if not isinstance(cid, str) or not cid:
            return False

    return True
