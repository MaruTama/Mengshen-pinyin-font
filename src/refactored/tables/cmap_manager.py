# -*- coding: utf-8 -*-
"""Character mapping table management for font processing."""

from __future__ import annotations

from functools import lru_cache
from typing import Dict, Optional


class CmapTableManager:
    """Manages character mapping table operations."""

    def __init__(self, cmap_table: Optional[Dict[str, str]] = None):
        """Initialize with optional cmap table.

        Args:
            cmap_table: Character mapping table
        """
        self.cmap_table = cmap_table or {}

    def set_cmap_table(self, new_cmap_table: Dict[str, str]) -> None:
        """Set the cmap table.

        Args:
            new_cmap_table: Character mapping table
        """
        self.cmap_table = new_cmap_table

    def get_cmap_table(self) -> Dict[str, str]:
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

    def batch_convert_hanzi_to_cid(self, hanzi_list: list[str]) -> list[str]:
        """Convert multiple hanzi characters to CIDs.

        Args:
            hanzi_list: List of hanzi characters

        Returns:
            List of CID strings
        """
        return [self.convert_hanzi_to_cid(hanzi) for hanzi in hanzi_list]
