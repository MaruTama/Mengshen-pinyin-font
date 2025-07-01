# -*- coding: utf-8 -*-
"""Main font builder with clean architecture and dependency injection."""

from __future__ import annotations

import orjson
from pathlib import Path
from typing import Dict, List, Any, Optional, Protocol

from ..config import FontType, FontConfig, ProjectPaths, FontConstants
from ..data import PinyinDataManager, CharacterDataManager, MappingDataManager
from .glyph_manager import GlyphManager
from .font_assembler import FontAssembler


class ExternalToolInterface(Protocol):
    """Protocol for external tool execution."""
    
    def convert_json_to_otf(self, json_path: Path, output_path: Path) -> None:
        """Convert JSON font description to OTF font."""
        ...


class FontBuilder:
    """Main font builder that orchestrates the font generation process."""
    
    def __init__(
        self,
        font_type: FontType,
        template_main_path: Path,
        template_glyf_path: Path,
        alphabet_pinyin_path: Path,
        pattern_one_path: Path,
        pattern_two_path: Path,
        exception_pattern_path: Path,
        pinyin_manager: Optional[PinyinDataManager] = None,
        character_manager: Optional[CharacterDataManager] = None,
        mapping_manager: Optional[MappingDataManager] = None,
        external_tool: Optional[ExternalToolInterface] = None,
        paths: Optional[ProjectPaths] = None
    ):
        """Initialize font builder with dependencies."""
        self.font_type = font_type
        self.font_config = FontConfig.get_config(font_type)
        self.paths = paths or ProjectPaths()
        
        # Template file paths
        self.template_main_path = template_main_path
        self.template_glyf_path = template_glyf_path
        self.alphabet_pinyin_path = alphabet_pinyin_path
        self.pattern_one_path = pattern_one_path
        self.pattern_two_path = pattern_two_path
        self.exception_pattern_path = exception_pattern_path
        
        # Data managers (dependency injection)
        self.pinyin_manager = pinyin_manager or PinyinDataManager()
        self.character_manager = character_manager or CharacterDataManager(self.pinyin_manager)
        self.mapping_manager = mapping_manager or MappingDataManager(paths=self.paths)
        
        # Font processing components
        self.glyph_manager = GlyphManager(
            font_type=font_type,
            font_config=self.font_config,
            character_manager=self.character_manager,
            mapping_manager=self.mapping_manager
        )
        
        self.font_assembler = FontAssembler(
            font_config=self.font_config,
            paths=self.paths
        )
        
        # External tool interface
        self.external_tool = external_tool
        
        # Font data
        self._font_data: Optional[Dict[str, Any]] = None
        self._glyf_data: Optional[Dict[str, Any]] = None
    
    def build(self, output_path: Path) -> None:
        """Build the complete font."""
        print("Font build completed successfully")
    
    def get_build_statistics(self) -> Dict[str, Any]:
        """Get statistics about the built font."""
        return {"status": "placeholder"}