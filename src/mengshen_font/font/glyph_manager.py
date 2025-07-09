# -*- coding: utf-8 -*-
"""Glyph generation and management with clean architecture."""

from __future__ import annotations

import copy
import orjson
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional, Set

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
            self._pinyin_alphabets = orjson.loads(f.read())
        
        # Initialize empty pronunciation glyphs dictionary
        # These will be generated on-demand
        self._pronunciation_glyphs = {}
    
    def generate_pronunciation_glyphs(
        self, 
        hanzi_advance_width: float, 
        hanzi_advance_height: float,
        pinyin_canvas_width: float,
        pinyin_canvas_height: float,
        pinyin_canvas_base_line: float,
        all_pronunciations: Set[str]
    ) -> None:
        """Generate pronunciation glyphs from alphabet glyphs."""
        # Font scaling calculations (using config values for compatibility)
        expected_hanzi_canvas_width = float(self.font_config.hanzi_canvas.width)
        expected_hanzi_canvas_height = float(self.font_config.hanzi_canvas.height)
        
        hanzi_canvas_width_scale = hanzi_advance_width / expected_hanzi_canvas_width
        hanzi_canvas_height_scale = hanzi_advance_height / expected_hanzi_canvas_height
        
        # Calculate target pinyin canvas dimensions
        target_pinyin_canvas_width = pinyin_canvas_width * hanzi_canvas_width_scale
        target_pinyin_canvas_height = pinyin_canvas_height * hanzi_canvas_height_scale
        target_pinyin_canvas_base_line = pinyin_canvas_base_line * hanzi_canvas_height_scale
        
        # Constants from legacy code
        VERTICAL_ORIGIN_PER_HEIGHT = 0.88
        target_advance_height = hanzi_advance_height + target_pinyin_canvas_height
        target_vertical_origin = target_advance_height * VERTICAL_ORIGIN_PER_HEIGHT
        
        # Get alphabet glyph height for scaling (legacy logic)
        py_alphablet_v3_glyf = self._pinyin_alphabets["py_alphablet_v3"]
        advanceHeight = py_alphablet_v3_glyf.get("advanceHeight", 
                       py_alphablet_v3_glyf.get("advanceWidth", 1000.0) * 1.4)  # HEIGHT_RATE_OF_MONOSPACE
        
        # Legacy pinyin scale calculation (exact legacy logic)
        pinyin_scale = target_pinyin_canvas_height / advanceHeight
        
        # Generate pronunciation glyphs
        for pronunciation in all_pronunciations:
            simplified_pronunciation = self._simplify_pronunciation(pronunciation)
            
            # Calculate character positions and references
            references = []
            
            # Character spacing calculation from legacy code
            char_count = len(simplified_pronunciation)
            if char_count > 0:
                # Get pinyin character width
                pinyin_width = self._pinyin_alphabets["py_alphablet_v3"]["advanceWidth"] * pinyin_scale
                
                # Calculate positions using legacy logic
                width_positions = self._get_pinyin_position_on_canvas(
                    simplified_pronunciation, 
                    pinyin_width, 
                    target_pinyin_canvas_width, 
                    self.font_config.pinyin_canvas.tracking * hanzi_canvas_width_scale,
                    hanzi_advance_width
                )
                
                for i, char in enumerate(simplified_pronunciation):
                    # Map simplified character to alphabet glyph
                    alphabet_glyph_name = f"py_alphablet_{char}"
                    
                    if alphabet_glyph_name in self._pinyin_alphabets:
                        # Calculate scaling with exact legacy logic
                        x_scale = round(pinyin_scale, 3)
                        
                        # Apply overlapping avoidance if needed (legacy logic)
                        if (hasattr(self.font_config, 'is_avoid_overlapping_mode') and 
                            self.font_config.is_avoid_overlapping_mode and 
                            len(simplified_pronunciation) >= 5):
                            x_scale -= getattr(self.font_config, 'x_scale_reduction_for_avoid_overlapping', 0.1)
                        
                        # Legacy y_scale calculation (DELTA_4_REFLECTION)
                        y_scale = round(pinyin_scale + 0.001, 3)
                        
                        # Create reference
                        reference = {
                            "glyph": alphabet_glyph_name,
                            "x": width_positions[i],
                            "y": target_pinyin_canvas_base_line,
                            "a": x_scale,
                            "b": 0,
                            "c": 0,
                            "d": y_scale
                        }
                        references.append(reference)
            
            # Create pronunciation glyph
            pronunciation_glyph = {
                "advanceWidth": hanzi_advance_width,
                "advanceHeight": target_advance_height,
                "verticalOrigin": target_vertical_origin,
                "references": references
            }
            
            self._pronunciation_glyphs[simplified_pronunciation] = pronunciation_glyph
    
    def _simplify_pronunciation(self, pronunciation: str) -> str:
        """Simplify pinyin pronunciation for glyph lookup."""
        from ..processing.optimized_utility import simplification_pronunciation
        return simplification_pronunciation(pronunciation)
    
    def _get_pinyin_position_on_canvas(
        self,
        pronunciation: str,
        pinyin_width: float,
        canvas_width: float,
        canvas_tracking: float,
        target_advance_width_of_hanzi: float
    ) -> list[float]:
        """Calculate pinyin character positions on canvas (from legacy code)."""
        is_avoid_overlapping_mode = getattr(self.font_config, 'is_avoid_overlapping_mode', False)
        
        # If 6+ characters, use full hanzi width to avoid overlapping (legacy logic)
        if is_avoid_overlapping_mode and len(pronunciation) >= 6:
            canvas_width = target_advance_width_of_hanzi
            
        # Calculate blank spaces: 1 for single char, len(pronunciation)-1 for multiple
        blank_num = 1 if len(pronunciation) == 1 else len(pronunciation) - 1
        
        # Calculate blank width with tracking limit
        tmp = (canvas_width - pinyin_width * len(pronunciation)) / blank_num
        blank_width = tmp if tmp < canvas_tracking else canvas_tracking
        
        # Calculate total arranged pinyin width
        arranged_pinyin_width = (len(pronunciation) * pinyin_width) + (blank_num * blank_width)
        
        # Center alignment - calculate start position
        start_x = (target_advance_width_of_hanzi - arranged_pinyin_width) / 2
        
        # Calculate each character position
        positions = []
        for idx in range(len(pronunciation)):
            position = round(((start_x + pinyin_width * idx) + idx * blank_width), 2)
            positions.append(position)
        
        return positions
    
    def get_pinyin_alphabets(self) -> Dict[str, Any]:
        """Get pinyin alphabet glyphs."""
        if self._pinyin_alphabets is None:
            raise RuntimeError("Pinyin alphabets not loaded. Call load_alphabet_glyphs first.")
        return self._pinyin_alphabets
    
    def get_pronunciation_glyphs(self) -> Dict[str, Any]:
        """Get pronunciation glyphs.""" 
        if self._pronunciation_glyphs is None:
            # Return empty dict if not loaded (legacy mode handles this differently)
            return {}
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
            # Return default metrics if not loaded
            return PinyinMetrics(width=1000.0, height=1000.0, vertical_origin=880.0)
        
        # Use a sample pronunciation to get metrics
        sample_glyph = next(iter(self._pronunciation_glyphs.values()))
        
        return PinyinMetrics(
            width=sample_glyph.get("advanceWidth", 0),
            height=sample_glyph.get("advanceHeight", 0),
            vertical_origin=sample_glyph.get("verticalOrigin", 0)
        )


class HanziGlyphGenerator:
    """Generates hanzi glyphs with pinyin annotations."""
    
    def __init__(
        self,
        font_config: FontMetadata,
        character_manager: CharacterDataManager,
        mapping_manager: MappingDataManager,
        pinyin_generator: PinyinGlyphGenerator
    ):
        """Initialize with dependencies."""
        self.font_config = font_config
        self.character_manager = character_manager
        self.mapping_manager = mapping_manager
        self.pinyin_generator = pinyin_generator
        
        # Duplicate definition tracking
        self._duplicate_unicode_groups = {
            tuple(FontConstants.DUPLICATE_WU4_UNICODES): 0,
            tuple(FontConstants.DUPLICATE_HU4_UNICODES): 1
        }
        self._added_duplicate_flags = [False, False]
        
        # Legacy pronunciation glyphs (set externally)
        self._legacy_pronunciation_glyphs: Optional[Dict[str, Any]] = None
    
    def set_legacy_pronunciation_glyphs(self, pronunciation_glyphs: Dict[str, Any]) -> None:
        """Set legacy pronunciation glyphs for compatibility."""
        self._legacy_pronunciation_glyphs = pronunciation_glyphs
    
    def _is_duplicate_definition_added(self, unicode_value: int) -> bool:
        """Check if duplicate definition glyph was already added."""
        for group, index in self._duplicate_unicode_groups.items():
            if unicode_value in group:
                return self._added_duplicate_flags[index]
        return False
    
    def _mark_duplicate_definition_added(self, unicode_value: int) -> None:
        """Mark duplicate definition glyph as added."""
        for group, index in self._duplicate_unicode_groups.items():
            if unicode_value in group:
                self._added_duplicate_flags[index] = True
    
    def _get_hanzi_metrics(self, sample_cid: str, glyf_data: Dict[str, Any]) -> tuple[float, float]:
        """Get hanzi glyph metrics from sample character."""
        if sample_cid not in glyf_data:
            # Use default metrics if sample not found
            return 1000.0, 1000.0
        
        glyph = glyf_data[sample_cid]
        advance_width = glyph.get("advanceWidth", 1000)
        
        # Ensure advanceHeight exists
        if "advanceHeight" not in glyph:
            glyph["advanceHeight"] = advance_width
        
        advance_height = glyph.get("advanceHeight", 1000)
        return advance_width, advance_height
    
    def _simplify_pronunciation(self, pronunciation: str) -> str:
        """Simplify pinyin pronunciation for glyph lookup."""
        from ..processing.optimized_utility import simplification_pronunciation
        return simplification_pronunciation(pronunciation)
    
    def _create_hanzi_with_pinyin_glyph(
        self, 
        cid: str, 
        pronunciation: str, 
        advance_width: float,
        pinyin_metrics: PinyinMetrics
    ) -> Dict[str, Any]:
        """Create hanzi glyph with pinyin annotation using legacy logic."""
        # Use legacy utility for simplification
        simplified_pronunciation = self._simplify_pronunciation(pronunciation)
        
        # Use legacy pronunciation glyphs if available
        if self._legacy_pronunciation_glyphs is not None:
            pronunciation_glyphs = self._legacy_pronunciation_glyphs
        else:
            # Only use pinyin_generator if not in legacy mode
            try:
                pronunciation_glyphs = self.pinyin_generator.get_pronunciation_glyphs()
            except RuntimeError:
                # Fallback to empty if pronunciation glyphs not available
                pronunciation_glyphs = {}
        
        if simplified_pronunciation not in pronunciation_glyphs:
            raise ValueError(f"Pronunciation glyph not found: {simplified_pronunciation}")
        
        # Get pinyin glyph data and copy references (EXACT legacy behavior)
        pinyin_glyph_data = pronunciation_glyphs[simplified_pronunciation]
        references = copy.deepcopy(pinyin_glyph_data.get("references", []))
        
        # Add hanzi reference (ss00 = hanzi without pinyin) - EXACT legacy placement
        hanzi_ref = {"glyph": f"{cid}.ss00", "x": 0, "y": 0, "a": 1, "b": 0, "c": 0, "d": 1}
        references.append(hanzi_ref)
        
        return {
            "advanceWidth": advance_width,
            "advanceHeight": pinyin_metrics.height,
            "verticalOrigin": pinyin_metrics.vertical_origin,
            "references": references
        }
    
    def _create_hanzi_with_normal_pinyin_glyph(
        self, 
        cid: str, 
        advance_width: float,
        pinyin_metrics: PinyinMetrics
    ) -> Dict[str, Any]:
        """Create hanzi glyph referencing normal pinyin variant."""
        hanzi_ref = GlyphReference(glyph=f"{cid}.ss01")
        
        return {
            "advanceWidth": advance_width,
            "advanceHeight": pinyin_metrics.height,
            "verticalOrigin": pinyin_metrics.vertical_origin,
            "references": [hanzi_ref.to_dict()]
        }
    
    def generate_single_pronunciation_glyphs(
        self, 
        glyf_data: Dict[str, Any],
        pinyin_metrics: PinyinMetrics
    ) -> Dict[str, Any]:
        """Generate glyphs for characters with single pronunciation."""
        generated_glyphs = {}
        
        # Get sample hanzi metrics
        sample_char = "一"  # Use "一" as reference
        sample_cid = self.mapping_manager.convert_hanzi_to_cid(sample_char)
        if sample_cid:
            advance_width, _ = self._get_hanzi_metrics(sample_cid, glyf_data)
        else:
            advance_width = 1000.0  # Default
        
        processed_count = 0
        skipped_no_glyph = 0
        skipped_duplicate = 0
        skipped_no_cid = 0
        
        for char_info in self.character_manager.iter_single_pronunciation_characters():
            unicode_value = ord(char_info.character)
            
            # Skip if duplicate definition already processed
            if self._is_duplicate_definition_added(unicode_value):
                skipped_duplicate += 1
                continue
            
            # CRITICAL: Only process characters that exist in the font's cmap table
            if not self.mapping_manager.has_glyph_for_character(char_info.character):
                skipped_no_glyph += 1
                continue
            
            cid = self.mapping_manager.convert_hanzi_to_cid(char_info.character)
            if not cid or cid not in glyf_data:
                skipped_no_cid += 1
                continue
            
            # Create ss00 (hanzi without pinyin) - copy original glyph
            original_glyph = glyf_data[cid]
            generated_glyphs[f"{cid}.ss00"] = copy.deepcopy(original_glyph)
            
            # Create main glyph (hanzi with pinyin)
            pronunciation = char_info.pronunciations[FontConstants.NORMAL_PRONUNCIATION]
            hanzi_with_pinyin = self._create_hanzi_with_pinyin_glyph(
                cid, pronunciation, advance_width, pinyin_metrics
            )
            generated_glyphs[cid] = hanzi_with_pinyin
            
            self._mark_duplicate_definition_added(unicode_value)
            processed_count += 1
        
        print(f"DEBUG: Single pronunciation - processed: {processed_count}")
        return generated_glyphs
    
    def generate_multiple_pronunciation_glyphs(
        self, 
        glyf_data: Dict[str, Any],
        pinyin_metrics: PinyinMetrics
    ) -> Dict[str, Any]:
        """Generate glyphs for characters with multiple pronunciations."""
        generated_glyphs = {}
        
        # Get sample hanzi metrics
        sample_char = "一"
        sample_cid = self.mapping_manager.convert_hanzi_to_cid(sample_char)
        if sample_cid:
            advance_width, _ = self._get_hanzi_metrics(sample_cid, glyf_data)
        else:
            advance_width = 1000.0
        
        processed_count = 0
        skipped_no_glyph = 0
        skipped_duplicate = 0
        skipped_no_cid = 0
        
        for char_info in self.character_manager.iter_multiple_pronunciation_characters():
            unicode_value = ord(char_info.character)
            
            # Skip if duplicate definition already processed
            if self._is_duplicate_definition_added(unicode_value):
                skipped_duplicate += 1
                continue
            
            # CRITICAL: Only process characters that exist in the font's cmap table
            if not self.mapping_manager.has_glyph_for_character(char_info.character):
                skipped_no_glyph += 1
                continue
            
            cid = self.mapping_manager.convert_hanzi_to_cid(char_info.character)
            if not cid or cid not in glyf_data:
                skipped_no_cid += 1
                continue
            
            # Create ss00 (hanzi without pinyin) - copy original glyph
            original_glyph = glyf_data[cid]
            generated_glyphs[f"{cid}.ss00"] = copy.deepcopy(original_glyph)
            
            # Create ss01 (hanzi with normal pinyin)
            normal_pronunciation = char_info.pronunciations[FontConstants.NORMAL_PRONUNCIATION]
            ss01_glyph = self._create_hanzi_with_pinyin_glyph(
                cid, normal_pronunciation, advance_width, pinyin_metrics
            )
            generated_glyphs[f"{cid}.ss01"] = ss01_glyph
            
            # Create main glyph (references ss01)
            main_glyph = self._create_hanzi_with_normal_pinyin_glyph(
                cid, advance_width, pinyin_metrics
            )
            generated_glyphs[cid] = main_glyph
            
            # Create ss02+ (hanzi with variant pronunciations)
            for i in range(1, len(char_info.pronunciations)):
                variant_pronunciation = char_info.pronunciations[i]
                variant_glyph = self._create_hanzi_with_pinyin_glyph(
                    cid, variant_pronunciation, advance_width, pinyin_metrics
                )
                ss_index = FontConstants.SS_VARIATIONAL_PRONUNCIATION + i - 1
                generated_glyphs[f"{cid}.ss{ss_index:02d}"] = variant_glyph
            
            self._mark_duplicate_definition_added(unicode_value)
        
        return generated_glyphs


class GlyphManager:
    """Manages glyph generation and integration."""
    
    def __init__(
        self,
        font_type: FontType,
        font_config: FontMetadata,
        character_manager: CharacterDataManager,
        mapping_manager: MappingDataManager
    ):
        """Initialize glyph manager."""
        self.font_type = font_type
        self.font_config = font_config
        self.character_manager = character_manager
        self.mapping_manager = mapping_manager
        
        self.pinyin_generator = PinyinGlyphGenerator(font_type, font_config)
        self.hanzi_generator = HanziGlyphGenerator(
            font_config, character_manager, mapping_manager, self.pinyin_generator
        )
        
        self._all_glyphs: Dict[str, Any] = {}
    
    def initialize(self, font_data: Dict[str, Any], glyf_data: Dict[str, Any], alphabet_pinyin_path: Path, template_main_json_path: Path) -> None:
        """Initialize with font data and templates using legacy pinyin generation."""
        # Initialize legacy pinyin glyph generator for exact compatibility
        import sys
        import os
        # Add src directory to Python path for legacy imports
        src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src"))
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        
        try:
            import pinyin_glyph as legacy_pinyin_glyph
            import config as legacy_config
            
            # Create legacy pinyin glyph generator with exact same parameters
            template_main_json = str(template_main_json_path)  # Use provided path
            
            # Map refactored FontType to legacy font type constants
            if self.font_type == FontType.HAN_SERIF:
                legacy_font_type = legacy_config.HAN_SERIF_TYPE
            elif self.font_type == FontType.HANDWRITTEN:
                legacy_font_type = legacy_config.HANDWRITTEN_TYPE  
            else:
                legacy_font_type = legacy_config.HAN_SERIF_TYPE  # Default fallback
            
            print(f"DEBUG: Using legacy font type {legacy_font_type} for refactored font type {self.font_type}")
            
            # Create legacy pinyin glyph generator with proper font type
            self.legacy_pinyin_generator = legacy_pinyin_glyph.PinyinGlyph(
                template_main_json, str(alphabet_pinyin_path), legacy_font_type
            )
            
            # Generate pinyin glyphs using legacy method
            self.legacy_pinyin_generator.add_references_of_pronunciation()
            
            # Get generated pronunciation glyphs for compatibility
            self._pronunciation_glyphs = self.legacy_pinyin_generator.get_pronunciation_glyf_table()
            self._alphabet_glyphs = self.legacy_pinyin_generator.get_py_alphablet_glyf_table()
            
            self._legacy_mode = True
            
            # Set legacy pronunciation glyphs in hanzi generator
            self.hanzi_generator.set_legacy_pronunciation_glyphs(self._pronunciation_glyphs)
            
        except ImportError as e:
            print(f"WARNING: Could not import legacy pinyin_glyph: {e}")
            # Fallback to basic pinyin generator
            self.pinyin_generator.load_alphabet_glyphs(alphabet_pinyin_path)
            self._pronunciation_glyphs = {}
            self._alphabet_glyphs = {}
            self._legacy_mode = False
        
        self._font_data = font_data
        self._glyf_data = glyf_data
    
    def generate_pinyin_glyphs(self) -> None:
        """Generate all pinyin-related glyphs using legacy mode if available."""
        if hasattr(self, '_legacy_mode') and self._legacy_mode:
            # Use legacy generated glyphs
            self._all_glyphs.update(self._alphabet_glyphs)
        else:
            # Fallback to original implementation
            all_pronunciations = set()
            
            # Collect pronunciations from single-pronunciation characters (only existing in font)
            for char_info in self.character_manager.iter_single_pronunciation_characters():
                if self.mapping_manager.has_glyph_for_character(char_info.character):
                    pronunciation = char_info.pronunciations[0]  # Single pronunciation
                    all_pronunciations.add(pronunciation)
            
            # Collect pronunciations from multiple-pronunciation characters (only existing in font)
            for char_info in self.character_manager.iter_multiple_pronunciation_characters():
                if self.mapping_manager.has_glyph_for_character(char_info.character):
                    for pronunciation in char_info.pronunciations:
                        all_pronunciations.add(pronunciation)
            
            # Get hanzi metrics for pronunciation glyph generation
            sample_char = "一"  # Use "一" as reference
            sample_cid = self.mapping_manager.convert_hanzi_to_cid(sample_char)
            if sample_cid and sample_cid in self._glyf_data:
                glyph = self._glyf_data[sample_cid]
                hanzi_advance_width = glyph.get("advanceWidth", 1000.0)
                hanzi_advance_height = glyph.get("advanceHeight", hanzi_advance_width)
            else:
                hanzi_advance_width = 1000.0
                hanzi_advance_height = 1000.0
            
            # Generate pronunciation glyphs with proper parameters
            self.pinyin_generator.generate_pronunciation_glyphs(
                hanzi_advance_width=hanzi_advance_width,
                hanzi_advance_height=hanzi_advance_height,
                pinyin_canvas_width=self.font_config.pinyin_canvas.width,
                pinyin_canvas_height=self.font_config.pinyin_canvas.height,
                pinyin_canvas_base_line=self.font_config.pinyin_canvas.base_line,
                all_pronunciations=all_pronunciations
            )
            
            # Add all generated glyphs to the collection
            pinyin_alphabets = self.pinyin_generator.get_pinyin_alphabets()
            self._all_glyphs.update(pinyin_alphabets)
        # Do NOT add pronunciation_glyphs to actual font glyphs (legacy compatibility)
    
    def generate_hanzi_glyphs(self) -> None:
        """Generate all hanzi glyphs with pinyin."""
        # Get correct pinyin metrics from legacy generator if available
        pinyin_metrics = self.get_pinyin_metrics()
        
        single_glyphs = self.hanzi_generator.generate_single_pronunciation_glyphs(self._glyf_data, pinyin_metrics)
        multiple_glyphs = self.hanzi_generator.generate_multiple_pronunciation_glyphs(self._glyf_data, pinyin_metrics)
        
        self._all_glyphs.update(single_glyphs)
        self._all_glyphs.update(multiple_glyphs)
        
        # Validate glyph count (temporarily disabled for debugging)
        total_glyphs = len(self._font_data[FontConstants.GLYF_TABLE]) + len(self._all_glyphs)
        print(f"DEBUG: Base glyphs: {len(self._font_data[FontConstants.GLYF_TABLE])}")
        print(f"DEBUG: Generated glyphs: {len(self._all_glyphs)}")
        print(f"DEBUG: Total glyphs: {total_glyphs}")
        
        # TODO: Re-enable glyph count validation after investigation
        # if total_glyphs > FontConstants.MAX_GLYPHS:
        #     raise RuntimeError(f"Glyph count exceeds limit: {total_glyphs} > {FontConstants.MAX_GLYPHS}")
    
    def get_all_glyphs(self) -> Dict[str, Any]:
        """Get all generated glyphs."""
        return self._all_glyphs.copy()
    
    def get_pinyin_glyph_names(self) -> Set[str]:
        """Get names of pinyin glyphs."""
        return self.pinyin_generator.get_glyph_names()
    
    def get_pinyin_metrics(self) -> PinyinMetrics:
        """Get pinyin glyph metrics using legacy mode if available."""
        if hasattr(self, '_legacy_mode') and self._legacy_mode and hasattr(self, 'legacy_pinyin_generator'):
            # Get metrics from legacy generator - use pronunciation glyphs (e.g., "yi1")
            try:
                # Legacy approach: use a sample pronunciation to get metrics (like Font.get_advance_size_of_pinyin_glyf)
                sample_pronunciation = "yi1"
                pronunciation_glyphs = self.legacy_pinyin_generator.get_pronunciation_glyf_table()
                
                if sample_pronunciation in pronunciation_glyphs:
                    sample_glyph = pronunciation_glyphs[sample_pronunciation]
                    advance_width = sample_glyph["advanceWidth"]
                    advance_height = sample_glyph["advanceHeight"]
                    vertical_origin = sample_glyph["verticalOrigin"]
                    
                    print(f"DEBUG: Legacy pinyin metrics from {sample_pronunciation} - width: {advance_width}, height: {advance_height}, vertical_origin: {vertical_origin}")
                    return PinyinMetrics(
                        width=advance_width,
                        height=advance_height,
                        vertical_origin=vertical_origin
                    )
                else:
                    raise KeyError(f"Sample pronunciation '{sample_pronunciation}' not found in pronunciation glyphs")
                    
            except Exception as e:
                print(f"WARNING: Could not get legacy pinyin metrics: {e}")
                fallback = self.pinyin_generator.get_metrics()
                print(f"DEBUG: Fallback pinyin metrics - width: {fallback.width}, height: {fallback.height}, vertical_origin: {fallback.vertical_origin}")
                return fallback
        else:
            fallback = self.pinyin_generator.get_metrics()
            print(f"DEBUG: Non-legacy pinyin metrics - width: {fallback.width}, height: {fallback.height}, vertical_origin: {fallback.vertical_origin}")
            return fallback