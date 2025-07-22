# -*- coding: utf-8 -*-
"""Font assembly and metadata management."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, cast

import orjson

from ..config import (
    FontConstants,
    FontMetadata,
    FontType,
    ProjectPaths,
    font_name_tables,
)
from ..config.font_name_tables import VERSION

# Import comprehensive type definitions
from ..types import FontData, HeadTable, StatsDict
from ..utils.logging_config import get_builder_logger


class FontAssembler:
    """Handles font assembly, metadata, and output generation."""

    def __init__(self, font_config: FontMetadata, paths: ProjectPaths):
        """Initialize font assembler.

        Args:
            font_config: Font metadata configuration (FontMetadata type)
            paths: Project paths configuration
        """
        self.font_config: FontMetadata = font_config
        self.paths = paths
        self.logger = get_builder_logger()

    def _get_current_font_timestamp(self) -> int:
        """Get current time as TrueType font timestamp.

        TrueType fonts use 1904/01/01 00:00 GMT as epoch (not Unix epoch 1970).

        Returns:
            Current time as seconds since 1904/01/01 00:00 GMT
        """
        # Font epoch: 1904/01/01 00:00 GMT (UTC)
        base_date = datetime.strptime(
            FontConstants.FONT_EPOCH_BASE_DATE, FontConstants.DATE_FORMAT
        ).replace(tzinfo=timezone.utc)
        base_time = base_date.timestamp()

        # Current time in UTC
        generation_time = datetime.now(timezone.utc).timestamp()
        return round(generation_time - base_time)

    def set_font_metadata(self, font_data: FontData, font_type: FontType) -> None:
        """Set font metadata including version and creation date."""

        # Set font revision
        head_table = cast(HeadTable, font_data[FontConstants.HEAD_TABLE])
        if isinstance(head_table, dict):
            head_table["fontRevision"] = VERSION

        # Set creation and modification dates to current generation time
        font_timestamp = self._get_current_font_timestamp()
        head_table["created"] = font_timestamp
        head_table["modified"] = font_timestamp

        # Optional: Add generation timestamp info for debugging
        generation_time = datetime.now()
        self.logger.info(
            "Font metadata set - Version: %s, Generated: %s",
            VERSION,
            generation_time.strftime("%Y-%m-%d %H:%M:%S"),
        )

        if font_type == FontType.HAN_SERIF:
            font_data[FontConstants.NAME_TABLE] = cast(Any, font_name_tables.HAN_SERIF)
        elif font_type == FontType.HANDWRITTEN:
            font_data[FontConstants.NAME_TABLE] = cast(
                Any, font_name_tables.HANDWRITTEN
            )
        else:
            raise ValueError(f"Unsupported font type: {font_type}")

    def save_font_json(self, font_data: FontData, output_path: Path) -> None:
        """Save font data as formatted JSON."""
        # Create output directories if they don't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "wb") as f:
            serialized_data = orjson.dumps(font_data, option=orjson.OPT_INDENT_2)
            f.write(serialized_data)

    def validate_font_structure(self, font_data: FontData) -> List[str]:
        """Validate font data structure and return list of issues."""
        issues = []

        required_tables = [
            FontConstants.CMAP_TABLE,
            FontConstants.GLYF_TABLE,
            FontConstants.HEAD_TABLE,
            FontConstants.HHEA_TABLE,
            FontConstants.NAME_TABLE,
            FontConstants.GLYPH_ORDER,
        ]

        for table in required_tables:
            if table not in font_data:
                issues.append(f"Missing required table: {table}")

        # Check glyph count
        if FontConstants.GLYF_TABLE in font_data:
            glyf_table = font_data[FontConstants.GLYF_TABLE]
            glyph_count = 0
            if isinstance(glyf_table, dict):
                glyph_count = len(glyf_table)
            elif isinstance(glyf_table, list):
                glyph_count = len(glyf_table)
            if glyph_count > FontConstants.MAX_GLYPHS:
                issues.append(
                    f"Glyph count exceeds limit: {glyph_count} > {FontConstants.MAX_GLYPHS}"
                )

        return issues

    def get_font_statistics(self, font_data: FontData) -> StatsDict:
        """Get statistics about the assembled font."""
        stats: StatsDict = {}

        if FontConstants.GLYF_TABLE in font_data:
            glyf_table = font_data[FontConstants.GLYF_TABLE]
            if isinstance(glyf_table, dict):
                stats["glyph_count"] = len(glyf_table)
            elif isinstance(glyf_table, list):
                stats["glyph_count"] = len(glyf_table)
            else:
                stats["glyph_count"] = 0

        if FontConstants.CMAP_TABLE in font_data:
            cmap = font_data[FontConstants.CMAP_TABLE]
            if cmap and hasattr(cmap, "keys"):
                cmap_dict = cast(Dict[str, Any], cmap)
                try:
                    unicode_values = [int(k) for k in cmap_dict.keys() if k.isdigit()]
                    if unicode_values:
                        unicode_range_dict: Dict[str, int] = {
                            "start": min(unicode_values),
                            "end": max(unicode_values),
                            "count": len(unicode_values),
                        }
                        stats["unicode_range"] = unicode_range_dict
                except (ValueError, AttributeError):
                    pass

        if FontConstants.CMAP_UVS_TABLE in font_data:
            uvs_table = font_data[FontConstants.CMAP_UVS_TABLE]
            if isinstance(uvs_table, dict):
                stats["uvs_mappings"] = len(uvs_table)
            elif isinstance(uvs_table, list):
                stats["uvs_mappings"] = len(uvs_table)
            else:
                stats["uvs_mappings"] = 0

        return stats
