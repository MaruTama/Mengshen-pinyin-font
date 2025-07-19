# -*- coding: utf-8 -*-
"""Unicode and character mapping data management."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional, Protocol

import orjson

from ..config import FontConstants, ProjectPaths


class CmapDataSource(Protocol):
    """Protocol for character map data sources."""

    def get_cmap_table(self) -> Dict[str, str]:
        """Get character map table."""
        ...


class JsonCmapDataSource:
    """Character map data source from JSON template."""

    def __init__(self, template_path: Path):
        """Initialize with template JSON path."""
        self.template_path = template_path
        self._cmap_table: Optional[Dict[str, str]] = None

    def _load_cmap_table(self) -> None:
        """Load cmap table from JSON template."""
        if self._cmap_table is not None:
            return

        if not self.template_path.exists():
            raise FileNotFoundError(f"Template JSON not found: {self.template_path}")

        with open(self.template_path, "rb") as f:
            font_data = orjson.loads(f.read())

        self._cmap_table = font_data.get("cmap", {})

    def get_cmap_table(self) -> Dict[str, str]:
        """Get character map table."""
        self._load_cmap_table()
        return self._cmap_table.copy()


class MappingDataManager:
    """Manages unicode and character mappings."""

    def __init__(
        self,
        cmap_source: Optional[CmapDataSource] = None,
        paths: Optional[ProjectPaths] = None,
    ):
        """Initialize with optional cmap data source and paths."""
        self.paths = paths or ProjectPaths()
        self._cmap_source = cmap_source
        self._cmap_table: Optional[Dict[str, str]] = None

    def _get_cmap_source(self) -> CmapDataSource:
        """Get or create cmap data source."""
        if self._cmap_source is None:
            template_path = self.paths.get_temp_json_path("template_main.json")
            self._cmap_source = JsonCmapDataSource(template_path)
        return self._cmap_source

    def get_cmap_table(self) -> Dict[str, str]:
        """Get character map table."""
        if self._cmap_table is None:
            self._cmap_table = self._get_cmap_source().get_cmap_table()
        return self._cmap_table

    @lru_cache(maxsize=FontConstants.LRU_CACHE_SIZE_XLARGE)
    def convert_hanzi_to_cid(self, hanzi: str) -> Optional[str]:
        """Convert hanzi character to CID (Character ID)."""
        cmap_table = self.get_cmap_table()
        unicode_key = str(ord(hanzi))
        return cmap_table.get(unicode_key)

    def has_glyph_for_character(self, hanzi: str) -> bool:
        """Check if font has glyph for character."""
        return self.convert_hanzi_to_cid(hanzi) is not None

    def get_missing_characters(self, characters: list[str]) -> list[str]:
        """Get characters that don't have glyphs in the font."""
        return [char for char in characters if not self.has_glyph_for_character(char)]

    def get_available_characters(self, characters: list[str]) -> list[str]:
        """Get characters that have glyphs in the font."""
        return [char for char in characters if self.has_glyph_for_character(char)]

    def get_unicode_from_cid(self, cid: str) -> Optional[str]:
        """Reverse lookup: get unicode from CID."""
        cmap_table = self.get_cmap_table()
        for unicode_key, mapped_cid in cmap_table.items():
            if mapped_cid == cid:
                return unicode_key
        return None

    def get_character_from_cid(self, cid: str) -> Optional[str]:
        """Get character from CID."""
        unicode_key = self.get_unicode_from_cid(cid)
        if unicode_key is None:
            return None
        try:
            return chr(int(unicode_key))
        except (ValueError, OverflowError):
            return None

    def get_glyph_statistics(self) -> dict:
        """Get glyph mapping statistics."""
        cmap_table = self.get_cmap_table()
        return {
            "total_glyphs": len(cmap_table),
            "unicode_range_start": (
                min(int(k) for k in cmap_table.keys()) if cmap_table else 0
            ),
            "unicode_range_end": (
                max(int(k) for k in cmap_table.keys()) if cmap_table else 0
            ),
        }

    def get_unicode_mappings(self) -> Dict[str, str]:
        """Get Unicode to CID mappings (alias for compatibility)."""
        return self.get_cmap_table()

    def load_mappings(self) -> None:
        """Load mapping data (triggers lazy loading)."""
        self.get_cmap_table()


# Global instance for backward compatibility
_default_mapping_manager: Optional[MappingDataManager] = None


def get_default_mapping_manager() -> MappingDataManager:
    """Get the default mapping data manager."""
    global _default_mapping_manager
    if _default_mapping_manager is None:
        _default_mapping_manager = MappingDataManager()
    return _default_mapping_manager
