# -*- coding: utf-8 -*-
"""Glyph generation and management with clean architecture."""

from __future__ import annotations

import copy
import orjson
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

from ..config import FontType, FontMetadata, FontConstants
from ..data import CharacterDataManager, MappingDataManager


@dataclass(frozen=True)
class PinyinMetrics:
    """Metrics for pinyin glyphs."""
    width: float
    height: float
    vertical_origin: float


@dataclass(frozen=True)
class GlyphReference:
    """Reference to another glyph in font composition."""
    glyph: str
    x: float = 0.0
    y: float = 0.0
    a: float = 1.0
    b: float = 0.0
    c: float = 0.0
    d: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'glyph': self.glyph,
            'x': self.x,
            'y': self.y,
            'a': self.a,
            'b': self.b,
            'c': self.c,
            'd': self.d
        }


class PinyinGlyphGenerator:
    """Generates pinyin-related glyphs."""
    
    def __init__(self, font_type: FontType, font_config: FontMetadata):
        """Initialize with font configuration."""
        self.font_type = font_type
        self.font_config = font_config
        self._pinyin_alphabets: Optional[Dict[str, Any]] = None
        self._pronunciation_glyphs: Optional[Dict[str, Any]] = None
    
    def load_alphabet_glyphs(self, alphabet_path: Path) -> None:
        """Load pinyin alphabet glyphs from template."""
        with open(alphabet_path, "rb") as f:
            alphabet_data = orjson.loads(f.read())
        
        # Process and convert pinyin alphabet glyphs
        # This would integrate with the existing pinyin_glyph module
        from pinyin_glyph import PinyinGlyph
        
        pinyin_glyph = PinyinGlyph(
            template_main_json=None,  # Will be set externally
            alphabet_pinyin_json=str(alphabet_path),
            font_type=int(self.font_type)
        )
        
        self._pinyin_alphabets = pinyin_glyph.get_py_alphablet_glyf_table()
        pinyin_glyph.add_references_of_pronunciation()
        self._pronunciation_glyphs = pinyin_glyph.get_pronunciation_glyf_table()
    
    def get_pinyin_alphabets(self) -> Dict[str, Any]:
        """Get pinyin alphabet glyphs."""
        if self._pinyin_alphabets is None:
            raise RuntimeError("Pinyin alphabets not loaded. Call load_alphabet_glyphs first.")
        return self._pinyin_alphabets
    
    def get_pronunciation_glyphs(self) -> Dict[str, Any]:
        """Get pronunciation glyphs.""" 
        if self._pronunciation_glyphs is None:
            raise RuntimeError("Pronunciation glyphs not loaded. Call load_alphabet_glyphs first.")
        return self._pronunciation_glyphs
    
    def get_glyph_names(self) -> Set[str]:
        """Get all pinyin glyph names."""
        names = set()
        if self._pinyin_alphabets:
            names.update(self._pinyin_alphabets.keys())
        if self._pronunciation_glyphs:
            names.update(self._pronunciation_glyphs.keys())
        return names
    
    def get_metrics(self) -> PinyinMetrics:
        """Get pinyin glyph metrics."""
        if self._pronunciation_glyphs is None:
            raise RuntimeError("Pronunciation glyphs not loaded")
        
        # Use a sample pronunciation to get metrics
        sample_glyph = next(iter(self._pronunciation_glyphs.values()))
        
        return PinyinMetrics(
            width=sample_glyph.get("advanceWidth", 0),
            height=sample_glyph.get("advanceHeight", 0),
            vertical_origin=sample_glyph.get("verticalOrigin", 0)
        )


class HanziGlyphGenerator:
    """Generates hanzi glyphs with pinyin annotations."""
    
    def __init__(\n        self,\n        font_config: FontMetadata,\n        character_manager: CharacterDataManager,\n        mapping_manager: MappingDataManager,\n        pinyin_generator: PinyinGlyphGenerator\n    ):\n        \"\"\"Initialize with dependencies.\"\"\"\n        self.font_config = font_config\n        self.character_manager = character_manager\n        self.mapping_manager = mapping_manager\n        self.pinyin_generator = pinyin_generator\n        \n        # Duplicate definition tracking\n        self._duplicate_unicode_groups = {\n            tuple(FontConstants.DUPLICATE_WU4_UNICODES): 0,\n            tuple(FontConstants.DUPLICATE_HU4_UNICODES): 1\n        }\n        self._added_duplicate_flags = [False, False]\n    \n    def _is_duplicate_definition_added(self, unicode_value: int) -> bool:\n        \"\"\"Check if duplicate definition glyph was already added.\"\"\"\n        for group, index in self._duplicate_unicode_groups.items():\n            if unicode_value in group:\n                return self._added_duplicate_flags[index]\n        return False\n    \n    def _mark_duplicate_definition_added(self, unicode_value: int) -> None:\n        \"\"\"Mark duplicate definition glyph as added.\"\"\"\n        for group, index in self._duplicate_unicode_groups.items():\n            if unicode_value in group:\n                self._added_duplicate_flags[index] = True\n    \n    def _get_hanzi_metrics(self, sample_cid: str, glyf_data: Dict[str, Any]) -> tuple[float, float]:\n        \"\"\"Get hanzi glyph metrics from sample character.\"\"\"\n        if sample_cid not in glyf_data:\n            # Use default metrics if sample not found\n            return 1000.0, 1000.0\n        \n        glyph = glyf_data[sample_cid]\n        advance_width = glyph.get(\"advanceWidth\", 1000)\n        \n        # Ensure advanceHeight exists\n        if \"advanceHeight\" not in glyph:\n            glyph[\"advanceHeight\"] = advance_width\n        \n        advance_height = glyph.get(\"advanceHeight\", 1000)\n        return advance_width, advance_height\n    \n    def _simplify_pronunciation(self, pronunciation: str) -> str:\n        \"\"\"Simplify pinyin pronunciation for glyph lookup.\"\"\"\n        # This would integrate with the existing utility module\n        from utility import simplification_pronunciation\n        return simplification_pronunciation(pronunciation)\n    \n    def _create_hanzi_with_pinyin_glyph(\n        self, \n        cid: str, \n        pronunciation: str, \n        advance_width: float,\n        pinyin_metrics: PinyinMetrics\n    ) -> Dict[str, Any]:\n        \"\"\"Create hanzi glyph with pinyin annotation.\"\"\"\n        simplified_pronunciation = self._simplify_pronunciation(pronunciation)\n        pronunciation_glyphs = self.pinyin_generator.get_pronunciation_glyphs()\n        \n        if simplified_pronunciation not in pronunciation_glyphs:\n            raise ValueError(f\"Pronunciation glyph not found: {simplified_pronunciation}\")\n        \n        # Get pinyin glyph data and copy references\n        pinyin_glyph_data = pronunciation_glyphs[simplified_pronunciation]\n        references = copy.deepcopy(pinyin_glyph_data.get(\"references\", []))\n        \n        # Add hanzi reference (ss00 = hanzi without pinyin)\n        hanzi_ref = GlyphReference(glyph=f\"{cid}.ss00\")\n        references.append(hanzi_ref.to_dict())\n        \n        return {\n            \"advanceWidth\": advance_width,\n            \"advanceHeight\": pinyin_metrics.height,\n            \"verticalOrigin\": pinyin_metrics.vertical_origin,\n            \"references\": references\n        }\n    \n    def _create_hanzi_with_normal_pinyin_glyph(\n        self, \n        cid: str, \n        advance_width: float,\n        pinyin_metrics: PinyinMetrics\n    ) -> Dict[str, Any]:\n        \"\"\"Create hanzi glyph referencing normal pinyin variant.\"\"\"\n        hanzi_ref = GlyphReference(glyph=f\"{cid}.ss01\")\n        \n        return {\n            \"advanceWidth\": advance_width,\n            \"advanceHeight\": pinyin_metrics.height,\n            \"verticalOrigin\": pinyin_metrics.vertical_origin,\n            \"references\": [hanzi_ref.to_dict()]\n        }\n    \n    def generate_single_pronunciation_glyphs(\n        self, \n        glyf_data: Dict[str, Any]\n    ) -> Dict[str, Any]:\n        \"\"\"Generate glyphs for characters with single pronunciation.\"\"\"\n        generated_glyphs = {}\n        pinyin_metrics = self.pinyin_generator.get_metrics()\n        \n        # Get sample hanzi metrics\n        sample_char = \"一\"  # Use \"一\" as reference\n        sample_cid = self.mapping_manager.convert_hanzi_to_cid(sample_char)\n        if sample_cid:\n            advance_width, _ = self._get_hanzi_metrics(sample_cid, glyf_data)\n        else:\n            advance_width = 1000.0  # Default\n        \n        for char_info in self.character_manager.iter_single_pronunciation_characters():\n            unicode_value = ord(char_info.character)\n            \n            # Skip if duplicate definition already processed\n            if self._is_duplicate_definition_added(unicode_value):\n                continue\n            \n            cid = self.mapping_manager.convert_hanzi_to_cid(char_info.character)\n            if not cid or cid not in glyf_data:\n                continue\n            \n            # Create ss00 (hanzi without pinyin) - copy original glyph\n            original_glyph = glyf_data[cid]\n            generated_glyphs[f\"{cid}.ss00\"] = copy.deepcopy(original_glyph)\n            \n            # Create main glyph (hanzi with pinyin)\n            pronunciation = char_info.pronunciations[FontConstants.NORMAL_PRONUNCIATION]\n            hanzi_with_pinyin = self._create_hanzi_with_pinyin_glyph(\n                cid, pronunciation, advance_width, pinyin_metrics\n            )\n            generated_glyphs[cid] = hanzi_with_pinyin\n            \n            self._mark_duplicate_definition_added(unicode_value)\n        \n        return generated_glyphs\n    \n    def generate_multiple_pronunciation_glyphs(\n        self, \n        glyf_data: Dict[str, Any]\n    ) -> Dict[str, Any]:\n        \"\"\"Generate glyphs for characters with multiple pronunciations.\"\"\"\n        generated_glyphs = {}\n        pinyin_metrics = self.pinyin_generator.get_metrics()\n        \n        # Get sample hanzi metrics\n        sample_char = \"一\"\n        sample_cid = self.mapping_manager.convert_hanzi_to_cid(sample_char)\n        if sample_cid:\n            advance_width, _ = self._get_hanzi_metrics(sample_cid, glyf_data)\n        else:\n            advance_width = 1000.0\n        \n        for char_info in self.character_manager.iter_multiple_pronunciation_characters():\n            unicode_value = ord(char_info.character)\n            \n            # Skip if duplicate definition already processed\n            if self._is_duplicate_definition_added(unicode_value):\n                continue\n            \n            cid = self.mapping_manager.convert_hanzi_to_cid(char_info.character)\n            if not cid or cid not in glyf_data:\n                continue\n            \n            # Create ss00 (hanzi without pinyin) - copy original glyph\n            original_glyph = glyf_data[cid]\n            generated_glyphs[f\"{cid}.ss00\"] = copy.deepcopy(original_glyph)\n            \n            # Create ss01 (hanzi with normal pinyin)\n            normal_pronunciation = char_info.pronunciations[FontConstants.NORMAL_PRONUNCIATION]\n            ss01_glyph = self._create_hanzi_with_pinyin_glyph(\n                cid, normal_pronunciation, advance_width, pinyin_metrics\n            )\n            generated_glyphs[f\"{cid}.ss01\"] = ss01_glyph\n            \n            # Create main glyph (references ss01)\n            main_glyph = self._create_hanzi_with_normal_pinyin_glyph(\n                cid, advance_width, pinyin_metrics\n            )\n            generated_glyphs[cid] = main_glyph\n            \n            # Create ss02+ (hanzi with variant pronunciations)\n            for i in range(1, len(char_info.pronunciations)):\n                variant_pronunciation = char_info.pronunciations[i]\n                variant_glyph = self._create_hanzi_with_pinyin_glyph(\n                    cid, variant_pronunciation, advance_width, pinyin_metrics\n                )\n                ss_index = FontConstants.SS_VARIATIONAL_PRONUNCIATION + i - 1\n                generated_glyphs[f\"{cid}.ss{ss_index:02d}\"] = variant_glyph\n            \n            self._mark_duplicate_definition_added(unicode_value)\n        \n        return generated_glyphs


class GlyphManager:\n    \"\"\"Manages glyph generation and integration.\"\"\"\n    \n    def __init__(\n        self,\n        font_type: FontType,\n        font_config: FontMetadata,\n        character_manager: CharacterDataManager,\n        mapping_manager: MappingDataManager\n    ):\n        \"\"\"Initialize glyph manager.\"\"\"\n        self.font_type = font_type\n        self.font_config = font_config\n        self.character_manager = character_manager\n        self.mapping_manager = mapping_manager\n        \n        self.pinyin_generator = PinyinGlyphGenerator(font_type, font_config)\n        self.hanzi_generator = HanziGlyphGenerator(\n            font_config, character_manager, mapping_manager, self.pinyin_generator\n        )\n        \n        self._all_glyphs: Dict[str, Any] = {}\n    \n    def initialize(self, font_data: Dict[str, Any], glyf_data: Dict[str, Any], alphabet_pinyin_path: Path) -> None:\n        \"\"\"Initialize with font data and templates.\"\"\"\n        self.pinyin_generator.load_alphabet_glyphs(alphabet_pinyin_path)\n        self._font_data = font_data\n        self._glyf_data = glyf_data\n    \n    def generate_pinyin_glyphs(self) -> None:\n        \"\"\"Generate all pinyin-related glyphs.\"\"\"\n        pinyin_alphabets = self.pinyin_generator.get_pinyin_alphabets()\n        pronunciation_glyphs = self.pinyin_generator.get_pronunciation_glyphs()\n        \n        self._all_glyphs.update(pinyin_alphabets)\n        self._all_glyphs.update(pronunciation_glyphs)\n    \n    def generate_hanzi_glyphs(self) -> None:\n        \"\"\"Generate all hanzi glyphs with pinyin.\"\"\"\n        single_glyphs = self.hanzi_generator.generate_single_pronunciation_glyphs(self._glyf_data)\n        multiple_glyphs = self.hanzi_generator.generate_multiple_pronunciation_glyphs(self._glyf_data)\n        \n        self._all_glyphs.update(single_glyphs)\n        self._all_glyphs.update(multiple_glyphs)\n        \n        # Validate glyph count\n        total_glyphs = len(self._font_data[FontConstants.GLYF_TABLE]) + len(self._all_glyphs)\n        if total_glyphs > FontConstants.MAX_GLYPHS:\n            raise RuntimeError(f\"Glyph count exceeds limit: {total_glyphs} > {FontConstants.MAX_GLYPHS}\")\n    \n    def get_all_glyphs(self) -> Dict[str, Any]:\n        \"\"\"Get all generated glyphs.\"\"\"\n        return self._all_glyphs.copy()\n    \n    def get_pinyin_glyph_names(self) -> Set[str]:\n        \"\"\"Get names of pinyin glyphs.\"\"\"\n        return self.pinyin_generator.get_glyph_names()\n    \n    def get_pinyin_metrics(self) -> PinyinMetrics:\n        \"\"\"Get pinyin glyph metrics.\"\"\"\n        return self.pinyin_generator.get_metrics()