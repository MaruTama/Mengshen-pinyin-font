# -*- coding: utf-8 -*-
"""Font assembly and metadata management."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import cast

from ..config import (
    VERSION,
    FontConstants,
    FontMetadata,
    FontType,
    ProjectPaths,
    font_name_tables,
)

# Import comprehensive type definitions
from ..font_types import FontData, HeadTable, NameTable
from ..utils.logging_config import get_logger


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
        self.logger = get_logger("mengshen.font_assembler")

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
            font_data[FontConstants.NAME_TABLE] = cast(
                NameTable, font_name_tables.HAN_SERIF
            )
        elif font_type == FontType.HANDWRITTEN:
            font_data[FontConstants.NAME_TABLE] = cast(
                NameTable, font_name_tables.HANDWRITTEN
            )
        else:
            raise ValueError(f"Unsupported font type: {font_type}")
