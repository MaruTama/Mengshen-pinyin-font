# -*- coding: utf-8 -*-
"""Character mapping table management for font processing.

Contains centralized character mapping table operations with clean OOP design.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

import orjson

from ..config.paths import DIR_TEMP
from ..font_types import CmapTable


class CmapTableManager:
    """Manages character mapping table operations with centralized design."""

    def __init__(self, cmap_table: Optional[CmapTable] = None):
        """Initialize with optional cmap table.

        Args:
            cmap_table: Character mapping table
        """
        self.cmap_table = cmap_table or {}

    def set_cmap_table(self, new_cmap_table: CmapTable) -> None:
        """Set the cmap table.

        Args:
            new_cmap_table: Character mapping table
        """
        self.cmap_table = new_cmap_table
        # Clear LRU cache when table changes
        self.convert_hanzi_to_cid.cache_clear()

    def get_cmap_table(self) -> CmapTable:
        """Get the current cmap table.

        Returns:
            Current character mapping table
        """
        return self.cmap_table

    @lru_cache(maxsize=1024)
    def convert_hanzi_to_cid(self, hanzi: str) -> str:
        """Convert hanzi character to CID using cmap table.

        Args:
            hanzi: Single hanzi character

        Returns:
            CID string or empty string if not found
        """
        if not hanzi or len(hanzi) != 1:
            return ""

        unicode_val = str(ord(hanzi))
        return self.cmap_table.get(unicode_val, "")

    def convert_hanzi_to_cid_safe(self, hanzi: str) -> Optional[str]:
        """Safely convert hanzi character to CID with error handling.

        Args:
            hanzi: Single Chinese character

        Returns:
            CID string if found, None if not found
        """
        if not isinstance(hanzi, str) or not hanzi or len(hanzi) != 1:
            return None

        unicode_value = str(ord(hanzi))
        return self.cmap_table.get(unicode_value)

    def batch_convert_hanzi_to_cid(self, hanzi_list: list[str]) -> list[str]:
        """Convert multiple hanzi characters to CIDs.

        Args:
            hanzi_list: List of hanzi characters

        Returns:
            List of CID strings
        """
        return [self.convert_hanzi_to_cid(hanzi) for hanzi in hanzi_list]

    @classmethod
    def from_template_main(cls) -> "CmapTableManager":
        """Load cmap table from template_main.json and create manager.

        Returns:
            CmapTableManager instance with loaded cmap table

        Raises:
            FileNotFoundError: If template_main.json doesn't exist
            KeyError: If 'cmap' section not found
            RuntimeError: If loading fails
        """
        template_main_json = os.path.join(DIR_TEMP, "template_main.json")

        if not os.path.exists(template_main_json):
            raise FileNotFoundError(f"Template file not found: {template_main_json}")

        try:
            with open(template_main_json, "rb") as read_file:
                merged_font = orjson.loads(read_file.read())

            if "cmap" not in merged_font:
                raise KeyError("No 'cmap' section found in template_main.json")

            cmap_data = merged_font["cmap"]
            if not isinstance(cmap_data, dict):
                raise TypeError(f"cmap data is not a dictionary: {type(cmap_data)}")

            return cls(cmap_data)

        except (OSError, KeyError, TypeError, ValueError) as e:
            raise RuntimeError(
                f"Failed to load cmap table from {template_main_json}: {e}"
            ) from e

    @classmethod
    def from_path(cls, template_path: str) -> "CmapTableManager":
        """Load cmap table from specific template JSON file and create manager.

        Args:
            template_path: Path to template JSON file

        Returns:
            CmapTableManager instance with loaded cmap table

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

            return cls(cmap_data)

        except (OSError, KeyError, TypeError, ValueError) as e:
            raise RuntimeError(
                f"Failed to load cmap table from {template_file}: {e}"
            ) from e
