# -*- coding: utf-8 -*-
"""Font assembly and metadata management."""

from __future__ import annotations

import orjson
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from ..config import FontType, FontConstants, ProjectPaths


class FontAssembler:
    """Handles font assembly, metadata, and output generation."""
    
    def __init__(self, font_config, paths: ProjectPaths):
        """Initialize font assembler."""
        self.font_config = font_config
        self.paths = paths
    
    def set_font_metadata(self, font_data: Dict[str, Any], font_type: FontType) -> None:
        """Set font metadata including version and creation date."""
        # Import migrated name table module
        from ..config.font_name_tables import VERSION
        
        # Set font revision
        font_data[FontConstants.HEAD_TABLE]["fontRevision"] = VERSION
        
        # Set creation date (base: 1904/01/01 00:00 GMT)
        base_date = datetime.strptime(FontConstants.FONT_EPOCH_BASE_DATE, FontConstants.DATE_FORMAT)
        base_time = base_date.timestamp()
        now_time = datetime.now().timestamp()
        font_data[FontConstants.HEAD_TABLE]["created"] = round(now_time - base_time)
        
        # Set font name table based on type
        if font_type == FontType.HAN_SERIF:
            font_data[FontConstants.NAME_TABLE] = name_table.HAN_SERIF
        elif font_type == FontType.HANDWRITTEN:
            font_data[FontConstants.NAME_TABLE] = name_table.HANDWRITTEN
        else:
            raise ValueError(f"Unsupported font type: {font_type}")
    
    def save_font_json(self, font_data: Dict[str, Any], output_path: Path) -> None:
        """Save font data as formatted JSON."""
        self.paths.ensure_directories()
        
        with open(output_path, "wb") as f:
            serialized_data = orjson.dumps(font_data, option=orjson.OPT_INDENT_2)
            f.write(serialized_data)
    
    def validate_font_structure(self, font_data: Dict[str, Any]) -> list[str]:
        """Validate font data structure and return list of issues."""
        issues = []
        
        required_tables = [
            FontConstants.CMAP_TABLE,
            FontConstants.GLYF_TABLE, 
            FontConstants.HEAD_TABLE,
            FontConstants.HHEA_TABLE,
            FontConstants.NAME_TABLE,
            FontConstants.GLYPH_ORDER
        ]
        
        for table in required_tables:
            if table not in font_data:
                issues.append(f"Missing required table: {table}")
        
        # Check glyph count
        if FontConstants.GLYF_TABLE in font_data:
            glyph_count = len(font_data[FontConstants.GLYF_TABLE])
            if glyph_count > FontConstants.MAX_GLYPHS:
                issues.append(f"Glyph count exceeds limit: {glyph_count} > {FontConstants.MAX_GLYPHS}")
        
        return issues
    
    def get_font_statistics(self, font_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get statistics about the assembled font."""
        stats = {}
        
        if FontConstants.GLYF_TABLE in font_data:
            stats['glyph_count'] = len(font_data[FontConstants.GLYF_TABLE])
        
        if FontConstants.CMAP_TABLE in font_data:
            cmap = font_data[FontConstants.CMAP_TABLE]
            if cmap:
                unicode_values = [int(k) for k in cmap.keys() if k.isdigit()]
                if unicode_values:
                    stats['unicode_range'] = {
                        'start': min(unicode_values),
                        'end': max(unicode_values),
                        'count': len(unicode_values)
                    }
        
        if FontConstants.CMAP_UVS_TABLE in font_data:
            stats['uvs_mappings'] = len(font_data[FontConstants.CMAP_UVS_TABLE])
        
        return stats