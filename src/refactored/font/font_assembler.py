# -*- coding: utf-8 -*-
"""Font assembly and metadata management."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Union

# Font data structure types
FontTableData = Dict[
    str, Union[str, int, float, List[Dict[str, Union[str, int, float]]]]
]
FontData = Dict[str, Union[str, int, float, FontTableData]]

import orjson

from ..config import FontConfig, FontConstants, FontType, ProjectPaths
from ..utils.logging_config import get_builder_logger


class FontAssembler:
    """Handles font assembly, metadata, and output generation."""

    def __init__(self, font_config: FontConfig, paths: ProjectPaths):
        """Initialize font assembler."""
        self.font_config = font_config
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
        # Import migrated name table module
        from ..config.font_name_tables import VERSION

        # Set font revision
        font_data[FontConstants.HEAD_TABLE]["fontRevision"] = VERSION

        # Set creation and modification dates to current generation time
        font_timestamp = self._get_current_font_timestamp()
        font_data[FontConstants.HEAD_TABLE]["created"] = font_timestamp
        font_data[FontConstants.HEAD_TABLE]["modified"] = font_timestamp

        # Optional: Add generation timestamp info for debugging
        generation_time = datetime.now()
        self.logger.info(
            f"Font metadata set - Version: {VERSION}, Generated: {generation_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )

        # Set font name table based on type
        from ..config import font_name_tables

        if font_type == FontType.HAN_SERIF:
            font_data[FontConstants.NAME_TABLE] = font_name_tables.HAN_SERIF
        elif font_type == FontType.HANDWRITTEN:
            font_data[FontConstants.NAME_TABLE] = font_name_tables.HANDWRITTEN
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
            glyph_count = len(font_data[FontConstants.GLYF_TABLE])
            if glyph_count > FontConstants.MAX_GLYPHS:
                issues.append(
                    f"Glyph count exceeds limit: {glyph_count} > {FontConstants.MAX_GLYPHS}"
                )

        return issues

    def get_font_statistics(
        self, font_data: FontData
    ) -> Dict[str, Union[str, int, float, Dict[str, int]]]:
        """Get statistics about the assembled font."""
        stats = {}

        if FontConstants.GLYF_TABLE in font_data:
            stats["glyph_count"] = len(font_data[FontConstants.GLYF_TABLE])

        if FontConstants.CMAP_TABLE in font_data:
            cmap = font_data[FontConstants.CMAP_TABLE]
            if cmap:
                unicode_values = [int(k) for k in cmap.keys() if k.isdigit()]
                if unicode_values:
                    unicode_range_dict = {
                        "start": min(unicode_values),
                        "end": max(unicode_values),
                        "count": len(unicode_values),
                    }
                    stats.update({"unicode_range": unicode_range_dict})

        if FontConstants.CMAP_UVS_TABLE in font_data:
            stats["uvs_mappings"] = len(font_data[FontConstants.CMAP_UVS_TABLE])

        return stats
