# -*- coding: utf-8 -*-
"""Glyph generation and management with clean architecture."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Union, cast

import orjson

from ..config import FontConstants, FontMetadata, FontType
from ..data import CharacterDataManager, MappingDataManager
from ..utils.logging_config import LOGGER_DEBUG, get_logger
from ..utils.pinyin_utils import simplification_pronunciation

# Font data types
GlyphData = Dict[str, Union[str, int, float, List[Dict[str, Union[str, int, float]]]]]
FontGlyphDict = Dict[str, GlyphData]
PinyinGlyphDict = Dict[str, GlyphData]


# レガシーコードコメント:
# > advanceHeight に対する advanceHeight の割合 (適当に決めてるから調整)
VERTICAL_ORIGIN_PER_HEIGHT = 0.88
# レガシーコードコメント:
# > ピンインの advanceHeight が無いときは決め打ちで advanceWidth の 1.4 倍にする
HEIGHT_RATE_OF_MONOSPACE = 1.4
# レガシーコードコメント:
# > otfccbuild の仕様なのか opentype の仕様なのか分からないが a と d が同じ値だと、グリフが消失する。
# > 少しでもサイズが違えば反映されるので、反映のためのマジックナンバー
DELTA_4_REFLECTION = 0.001


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

    def to_dict(self) -> Dict[str, Union[str, int, float]]:
        """Convert to dictionary for JSON serialization."""
        return {
            "glyph": self.glyph,
            "x": self.x,
            "y": self.y,
            "a": self.a,
            "b": self.b,
            "c": self.c,
            "d": self.d,
        }


class PinyinGlyphGenerator:
    """Generates pinyin-related glyphs."""

    def __init__(self, font_type: FontType, font_config: FontMetadata):
        """Initialize with font configuration."""
        self.font_type = font_type
        self.font_config = font_config
        self._pinyin_alphabets: Optional[FontGlyphDict] = None
        self.logger = get_logger(LOGGER_DEBUG)
        self._pronunciation_glyphs: Optional[PinyinGlyphDict] = None

    def load_alphabet_glyphs(self, alphabet_path: Path) -> None:
        """Load pinyin alphabet glyphs from template."""
        with open(alphabet_path, "rb") as f:
            alphabet_data = orjson.loads(f.read())

        # Convert alphabet glyphs to py_alphabet_ naming convention
        # Legacy code expects glyphs named like "py_alphabet_a", "py_alphabet_i1", etc.
        self._pinyin_alphabets = {}

        if "ǘ" in alphabet_data:
            self._pinyin_alphabets["py_alphabet_v3"] = alphabet_data["ǘ"]
        elif "ǚ" in alphabet_data:
            self._pinyin_alphabets["py_alphabet_v3"] = alphabet_data["ǚ"]
        elif "ǜ" in alphabet_data:
            self._pinyin_alphabets["py_alphabet_v3"] = alphabet_data["ǜ"]
        else:
            # Fallback to any character if special ones not found
            first_char = next(iter(alphabet_data.values()))
            self._pinyin_alphabets["py_alphabet_v3"] = first_char

        # Convert alphabet characters to simplified names with py_alphabet_ prefix
        # Use exact same logic as legacy code for tone mapping
        for char, glyph_data in alphabet_data.items():
            # Map tones to simplified forms exactly as legacy code does
            if char in ["ā", "á", "ǎ", "à"]:
                tone_map = {"ā": "a1", "á": "a2", "ǎ": "a3", "à": "a4"}
                alphabet_glyph_name = f"py_alphabet_{tone_map[char]}"
            elif char in ["ē", "é", "ě", "è"]:
                tone_map = {"ē": "e1", "é": "e2", "ě": "e3", "è": "e4"}
                alphabet_glyph_name = f"py_alphabet_{tone_map[char]}"
            elif char in ["ī", "í", "ǐ", "ì"]:
                tone_map = {"ī": "i1", "í": "i2", "ǐ": "i3", "ì": "i4"}
                alphabet_glyph_name = f"py_alphabet_{tone_map[char]}"
            elif char in ["ō", "ó", "ǒ", "ò"]:
                tone_map = {"ō": "o1", "ó": "o2", "ǒ": "o3", "ò": "o4"}
                alphabet_glyph_name = f"py_alphabet_{tone_map[char]}"
            elif char in ["ū", "ú", "ǔ", "ù"]:
                tone_map = {"ū": "u1", "ú": "u2", "ǔ": "u3", "ù": "u4"}
                alphabet_glyph_name = f"py_alphabet_{tone_map[char]}"
            elif char in ["ǖ", "ǘ", "ǚ", "ǜ"]:
                tone_map = {"ǖ": "v1", "ǘ": "v2", "ǚ": "v3", "ǜ": "v4"}
                alphabet_glyph_name = f"py_alphabet_{tone_map[char]}"
            elif char == "ü":
                alphabet_glyph_name = "py_alphabet_v"
            elif char in ["ń", "ň", "ǹ"]:
                tone_map = {"ń": "n2", "ň": "n3", "ǹ": "n4"}
                alphabet_glyph_name = f"py_alphabet_{tone_map[char]}"
            elif char == "ḿ":
                alphabet_glyph_name = "py_alphabet_m2"
            else:
                # For basic alphabet characters (a-z)
                alphabet_glyph_name = f"py_alphabet_{char}"

            self._pinyin_alphabets[alphabet_glyph_name] = glyph_data

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
        all_pronunciations: Set[str],
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
        target_pinyin_canvas_base_line = (
            pinyin_canvas_base_line * hanzi_canvas_height_scale
        )

        # Constants from legacy code
        target_advance_height = hanzi_advance_height + target_pinyin_canvas_height
        target_vertical_origin = target_advance_height * VERTICAL_ORIGIN_PER_HEIGHT

        # Get alphabet glyph height for scaling
        if self._pinyin_alphabets is None:
            raise ValueError("Alphabet glyphs not loaded")

        # レガシーコードコメント:
        # > ピンインがキャンバスに収まる scale を求める.
        # > 等幅フォントであれば大きさは同じなのでどんな文字でも同じだと思うが、一応最も背の高い文字を指定する (多分 ǘ ǚ ǜ)
        # Add the special v3 glyph used for height calculations (using highest character)
        py_alphabet_v3_glyf = self._pinyin_alphabets["py_alphabet_v3"]
        advance_width_raw = py_alphabet_v3_glyf.get("advanceWidth", 1000.0)
        advance_width = (
            float(advance_width_raw)
            if isinstance(advance_width_raw, (int, float))
            else 1000.0
        )
        advance_height_raw = py_alphabet_v3_glyf.get(
            "advanceHeight", advance_width * HEIGHT_RATE_OF_MONOSPACE
        )
        advance_height = (
            float(advance_height_raw)
            if isinstance(advance_height_raw, (int, float))
            else 1000.0
        )

        # Legacy pinyin scale calculation
        pinyin_scale = target_pinyin_canvas_height / advance_height

        # Generate pronunciation glyphs
        for pronunciation in all_pronunciations:
            simplified_pronunciation = self._simplify_pronunciation(pronunciation)

            # Calculate character positions and references
            references = []

            # Character spacing calculation
            char_count = len(pronunciation)
            if char_count > 0:
                # Get pinyin character width
                if self._pinyin_alphabets is None:
                    raise ValueError("Alphabet glyphs not loaded")
                width_raw = self._pinyin_alphabets["py_alphabet_v3"]["advanceWidth"]
                width_value = (
                    float(width_raw) if isinstance(width_raw, (int, float)) else 1000.0
                )
                pinyin_width = width_value * pinyin_scale

                # レガシーコードコメント:
                # > ピンイン表示部(target_pinyin_canvas_width)に収まるように等間隔に配置する
                width_positions = self._get_pinyin_position_on_canvas(
                    pronunciation,
                    pinyin_width,
                    target_pinyin_canvas_width,
                    self.font_config.pinyin_canvas.tracking * hanzi_canvas_width_scale,
                    hanzi_advance_width,
                )

                for i, char in enumerate(pronunciation):
                    # Map each character individually (legacy logic)
                    simplified_char = self._simplify_pronunciation(char)
                    alphabet_glyph_name = f"py_alphabet_{simplified_char}"

                    if alphabet_glyph_name in self._pinyin_alphabets:
                        # Calculate scaling with exact legacy logic
                        x_scale = round(pinyin_scale, 3)

                        # Apply overlapping avoidance if needed (legacy logic)
                        if (
                            hasattr(self.font_config, "is_avoid_overlapping_mode")
                            and self.font_config.is_avoid_overlapping_mode
                            and len(simplified_pronunciation) >= 5
                        ):
                            x_scale -= getattr(
                                self.font_config,
                                "x_scale_reduction_for_avoid_overlapping",
                                0.1,
                            )

                        y_scale = round(pinyin_scale + DELTA_4_REFLECTION, 3)

                        # レガシーコードコメント:
                        # > a-d ってなんだ？
                        # > > The transformation entries determine the values of an affine transformation applied to
                        # > the component prior to its being incorporated into the parent glyph.
                        # >
                        # > Given the component matrix [a b c d e f], the transformation applied to the component is:
                        # > [The 'glyf' table](https://developer.apple.com/fonts/TrueType-Reference-Manual/RM06/Chap6glyf.html)
                        # > [FontConfigの​matrix​フォント​プロパティを​利用して​字体を​変化させる​方法](http://ie.pcgw.pgw.jp/2015/10/17/fontconfig-matrix.html)

                        # Create reference
                        reference = {
                            "glyph": alphabet_glyph_name,
                            "x": width_positions[i],
                            "y": target_pinyin_canvas_base_line,
                            "a": x_scale,
                            "b": 0,
                            "c": 0,
                            "d": y_scale,
                        }
                        references.append(reference)

            # Create pronunciation glyph
            pronunciation_glyph: GlyphData = {
                "advanceWidth": hanzi_advance_width,
                "advanceHeight": target_advance_height,
                "verticalOrigin": target_vertical_origin,
                "references": cast(List[Dict[str, Union[str, int, float]]], references),
            }

            if self._pronunciation_glyphs is not None:
                self._pronunciation_glyphs[simplified_pronunciation] = (
                    pronunciation_glyph
                )

    def _simplify_pronunciation(self, pronunciation: str) -> str:
        """Simplify pinyin pronunciation for glyph lookup."""

        return simplification_pronunciation(pronunciation)

    def _get_pinyin_position_on_canvas(
        self,
        pronunciation: str,
        pinyin_width: float,
        canvas_width: float,
        canvas_tracking: float,
        target_advance_width_of_hanzi: float,
    ) -> list[float]:
        """Calculate pinyin character positions on canvas"""
        is_avoid_overlapping_mode = getattr(
            self.font_config, "is_avoid_overlapping_mode", False
        )

        # If 6+ characters, use full hanzi width to avoid overlapping
        if is_avoid_overlapping_mode and len(pronunciation) >= 6:
            canvas_width = target_advance_width_of_hanzi

        # Calculate blank spaces: 1 for single char, len(pronunciation)-1 for multiple
        blank_num = 1 if len(pronunciation) == 1 else len(pronunciation) - 1

        # Calculate blank width with tracking limit
        tmp = (canvas_width - pinyin_width * len(pronunciation)) / blank_num
        blank_width = tmp if tmp < canvas_tracking else canvas_tracking

        # Calculate total arranged pinyin width
        arranged_pinyin_width = (len(pronunciation) * pinyin_width) + (
            blank_num * blank_width
        )

        # Center alignment - calculate start position
        start_x = (target_advance_width_of_hanzi - arranged_pinyin_width) / 2

        # Calculate each character position
        positions = []
        for idx in range(len(pronunciation)):
            position = round(((start_x + pinyin_width * idx) + idx * blank_width), 2)
            positions.append(position)

        return positions

    def get_pinyin_alphabets(self) -> FontGlyphDict:
        """Get pinyin alphabet glyphs."""
        if self._pinyin_alphabets is None:
            raise RuntimeError(
                "Pinyin alphabets not loaded. Call load_alphabet_glyphs first."
            )
        return self._pinyin_alphabets

    def get_pronunciation_glyphs(self) -> PinyinGlyphDict:
        """Get pronunciation glyphs."""
        if self._pronunciation_glyphs is None:
            # Return empty dict if not loaded (legacy mode handles this differently)
            return {}
        return self._pronunciation_glyphs

    def get_glyph_names(self) -> Set[str]:
        """Get all pinyin glyph names."""
        names: set[str] = set()
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

        width_raw = sample_glyph.get("advanceWidth", 0)
        height_raw = sample_glyph.get("advanceHeight", 0)
        origin_raw = sample_glyph.get("verticalOrigin", 0)

        return PinyinMetrics(
            width=float(width_raw) if isinstance(width_raw, (int, float)) else 0.0,
            height=float(height_raw) if isinstance(height_raw, (int, float)) else 0.0,
            vertical_origin=(
                float(origin_raw) if isinstance(origin_raw, (int, float)) else 0.0
            ),
        )


class HanziGlyphGenerator:
    """Generates hanzi glyphs with pinyin annotations."""

    def __init__(
        self,
        font_config: FontMetadata,
        character_manager: CharacterDataManager,
        mapping_manager: MappingDataManager,
        pinyin_generator: PinyinGlyphGenerator,
    ):
        """Initialize with dependencies."""
        self.font_config = font_config
        self.character_manager = character_manager
        self.mapping_manager = mapping_manager
        self.pinyin_generator = pinyin_generator
        self.logger = get_logger(LOGGER_DEBUG)

        # Duplicate definition tracking
        self._duplicate_unicode_groups = [
            tuple(FontConstants.DUPLICATE_WU4_UNICODES),  # Index 0
            tuple(FontConstants.DUPLICATE_HU4_UNICODES),  # Index 1
        ]
        self._added_duplicate_flags = [False, False]

        # Legacy pronunciation glyphs (set externally)
        self._legacy_pronunciation_glyphs: Optional[PinyinGlyphDict] = None

    def set_legacy_pronunciation_glyphs(
        self, pronunciation_glyphs: PinyinGlyphDict
    ) -> None:
        """Set legacy pronunciation glyphs for compatibility."""
        self._legacy_pronunciation_glyphs = pronunciation_glyphs

    def _is_duplicate_definition_added(self, unicode_value: int) -> bool:
        """Check if duplicate definition glyph was already added."""
        for index, group in enumerate(self._duplicate_unicode_groups):
            if unicode_value in group:
                return self._added_duplicate_flags[index]
        return False

    def _mark_duplicate_definition_added(self, unicode_value: int) -> None:
        """Mark duplicate definition glyph as added."""
        for index, group in enumerate(self._duplicate_unicode_groups):
            if unicode_value in group:
                self._added_duplicate_flags[index] = True

    def _get_hanzi_metrics(
        self, sample_cid: str, glyf_data: FontGlyphDict
    ) -> tuple[float, float]:
        """Get hanzi glyph metrics from sample character."""
        if sample_cid not in glyf_data:
            # Use default metrics if sample not found
            return 1000.0, 1000.0

        glyph = glyf_data[sample_cid]
        advance_width_raw = glyph.get("advanceWidth", 1000)
        advance_width = (
            float(advance_width_raw)
            if isinstance(advance_width_raw, (int, float))
            else 1000.0
        )

        # Ensure advanceHeight exists
        if "advanceHeight" not in glyph:
            glyph["advanceHeight"] = advance_width

        advance_height_raw = glyph.get("advanceHeight", 1000)
        advance_height = (
            float(advance_height_raw)
            if isinstance(advance_height_raw, (int, float))
            else 1000.0
        )
        return advance_width, advance_height

    def _simplify_pronunciation(self, pronunciation: str) -> str:
        """Simplify pinyin pronunciation for glyph lookup."""

        return simplification_pronunciation(pronunciation)

    def _create_hanzi_with_pinyin_glyph(
        self,
        cid: str,
        pronunciation: str,
        advance_width: float,
        pinyin_metrics: PinyinMetrics,
    ) -> GlyphData:
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
            raise ValueError(
                f"Pronunciation glyph not found: {simplified_pronunciation}"
            )

        # Get pinyin glyph data and copy references (EXACT legacy behavior)
        pinyin_glyph_data = pronunciation_glyphs[simplified_pronunciation]
        refs_raw = pinyin_glyph_data.get("references", [])
        references: List[Dict[str, Union[str, int, float]]] = (
            copy.deepcopy(refs_raw) if isinstance(refs_raw, list) else []
        )

        # Add hanzi reference (ss00 = hanzi without pinyin) - EXACT legacy placement
        hanzi_ref: Dict[str, Union[str, int, float]] = {
            "glyph": f"{cid}.ss00",
            "x": 0,
            "y": 0,
            "a": 1,
            "b": 0,
            "c": 0,
            "d": 1,
        }
        references.append(hanzi_ref)

        return {
            "advanceWidth": advance_width,
            "advanceHeight": pinyin_metrics.height,
            "verticalOrigin": pinyin_metrics.vertical_origin,
            "references": references,
        }

    def _create_hanzi_with_normal_pinyin_glyph(
        self, cid: str, advance_width: float, pinyin_metrics: PinyinMetrics
    ) -> GlyphData:
        """Create hanzi glyph referencing normal pinyin variant."""
        hanzi_ref = GlyphReference(glyph=f"{cid}.ss01")

        return {
            "advanceWidth": advance_width,
            "advanceHeight": pinyin_metrics.height,
            "verticalOrigin": pinyin_metrics.vertical_origin,
            "references": [hanzi_ref.to_dict()],
        }

    def generate_single_pronunciation_glyphs(
        self, glyf_data: FontGlyphDict, pinyin_metrics: PinyinMetrics
    ) -> FontGlyphDict:
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

        self.logger.debug("Single pronunciation - processed: %d", processed_count)
        return generated_glyphs

    def generate_multiple_pronunciation_glyphs(
        self, glyf_data: FontGlyphDict, pinyin_metrics: PinyinMetrics
    ) -> FontGlyphDict:
        """Generate glyphs for characters with multiple pronunciations."""
        generated_glyphs = {}

        # Get sample hanzi metrics
        sample_char = "一"
        sample_cid = self.mapping_manager.convert_hanzi_to_cid(sample_char)
        if sample_cid:
            advance_width, _ = self._get_hanzi_metrics(sample_cid, glyf_data)
        else:
            advance_width = 1000.0

        # processed_count = 0  # Commented out as it's not used
        skipped_no_glyph = 0
        skipped_duplicate = 0
        skipped_no_cid = 0

        for (
            char_info
        ) in self.character_manager.iter_multiple_pronunciation_characters():
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
            normal_pronunciation = char_info.pronunciations[
                FontConstants.NORMAL_PRONUNCIATION
            ]
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
        mapping_manager: MappingDataManager,
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
        self.logger = get_logger(LOGGER_DEBUG)

        self._all_glyphs: FontGlyphDict = {}
        self._pronunciation_glyphs: PinyinGlyphDict = {}
        self._alphabet_glyphs: FontGlyphDict = {}
        self._legacy_mode = False
        self._font_data: Optional[FontGlyphDict] = None
        self._glyf_data: Optional[FontGlyphDict] = None

    def initialize(
        self,
        font_data: FontGlyphDict,
        glyf_data: FontGlyphDict,
        alphabet_pinyin_path: Path,
    ) -> None:
        """Initialize with font data and templates."""
        # Use refactored pinyin generator (no legacy mode for now)
        self.pinyin_generator.load_alphabet_glyphs(alphabet_pinyin_path)

        # Reset instance variables (already initialized in __init__)
        self._pronunciation_glyphs = {}
        self._alphabet_glyphs = {}
        self._legacy_mode = False

        self._font_data = font_data
        self._glyf_data = glyf_data

    def generate_pinyin_glyphs(self) -> None:
        """Generate all pinyin-related glyphs."""
        all_pronunciations = set()

        # Collect pronunciations from single-pronunciation characters (only existing in font)
        for char_info in self.character_manager.iter_single_pronunciation_characters():
            if self.mapping_manager.has_glyph_for_character(char_info.character):
                pronunciation = char_info.pronunciations[0]  # Single pronunciation
                all_pronunciations.add(pronunciation)

        # Collect pronunciations from multiple-pronunciation characters (only existing in font)
        for (
            char_info
        ) in self.character_manager.iter_multiple_pronunciation_characters():
            if self.mapping_manager.has_glyph_for_character(char_info.character):
                for pronunciation in char_info.pronunciations:
                    all_pronunciations.add(pronunciation)

        self.logger.debug("Found %d unique pronunciations", len(all_pronunciations))

        # Get hanzi metrics for pronunciation glyph generation
        sample_char = "一"  # Use "一" as reference
        sample_cid = self.mapping_manager.convert_hanzi_to_cid(sample_char)
        if sample_cid and self._glyf_data and sample_cid in self._glyf_data:
            glyph = self._glyf_data[sample_cid]
            width_raw = glyph.get("advanceWidth", 1000.0)
            hanzi_advance_width = (
                float(width_raw) if isinstance(width_raw, (int, float)) else 1000.0
            )
            height_raw = glyph.get("advanceHeight", hanzi_advance_width)
            hanzi_advance_height = (
                float(height_raw)
                if isinstance(height_raw, (int, float))
                else hanzi_advance_width
            )
        else:
            hanzi_advance_width = 1000.0
            hanzi_advance_height = 1000.0

        self.logger.debug(
            "Hanzi metrics - width: %f, height: %f",
            hanzi_advance_width,
            hanzi_advance_height,
        )

        # Generate pronunciation glyphs with proper parameters
        self.pinyin_generator.generate_pronunciation_glyphs(
            hanzi_advance_width=hanzi_advance_width,
            hanzi_advance_height=hanzi_advance_height,
            pinyin_canvas_width=self.font_config.pinyin_canvas.width,
            pinyin_canvas_height=self.font_config.pinyin_canvas.height,
            pinyin_canvas_base_line=self.font_config.pinyin_canvas.base_line,
            all_pronunciations=all_pronunciations,
        )

        # Add all generated glyphs to the collection
        pinyin_alphabets = self.pinyin_generator.get_pinyin_alphabets()
        pronunciation_glyphs = self.pinyin_generator.get_pronunciation_glyphs()

        self.logger.debug(
            "Generated %d alphabet glyphs and %d pronunciation glyphs",
            len(pinyin_alphabets),
            len(pronunciation_glyphs),
        )

        self._all_glyphs.update(pinyin_alphabets)
        # Store pronunciation glyphs separately for hanzi generator
        self._pronunciation_glyphs = pronunciation_glyphs

    def generate_hanzi_glyphs(self) -> None:
        """Generate all hanzi glyphs with pinyin."""
        if self._glyf_data is None:
            raise ValueError("Glyf data not loaded")
        if self._font_data is None:
            raise ValueError("Font data not loaded")

        # Set the pronunciation glyphs in the hanzi generator
        self.hanzi_generator.set_legacy_pronunciation_glyphs(self._pronunciation_glyphs)

        # Get correct pinyin metrics
        pinyin_metrics = self.get_pinyin_metrics()

        single_glyphs = self.hanzi_generator.generate_single_pronunciation_glyphs(
            self._glyf_data, pinyin_metrics
        )
        multiple_glyphs = self.hanzi_generator.generate_multiple_pronunciation_glyphs(
            self._glyf_data, pinyin_metrics
        )

        self._all_glyphs.update(single_glyphs)
        self._all_glyphs.update(multiple_glyphs)

        # Validate glyph count (temporarily disabled for debugging)
        total_glyphs = len(self._font_data[FontConstants.GLYF_TABLE]) + len(
            self._all_glyphs
        )
        self.logger.debug(
            "Base glyphs: %d", len(self._font_data[FontConstants.GLYF_TABLE])
        )
        self.logger.debug("Generated glyphs: %d", len(self._all_glyphs))
        self.logger.debug("Total glyphs: %d", total_glyphs)

        # Note: Glyph count validation is performed in FontBuilder._add_glyf() after final assembly

    def get_all_glyphs(self) -> FontGlyphDict:
        """Get all generated glyphs."""
        return self._all_glyphs.copy()

    def get_pinyin_glyph_names(self) -> Set[str]:
        """Get names of pinyin glyphs."""
        return self.pinyin_generator.get_glyph_names()

    def get_pinyin_metrics(self) -> PinyinMetrics:
        """Get pinyin glyph metrics."""
        # Try to get metrics from generated pronunciation glyphs first
        if hasattr(self, "_pronunciation_glyphs") and self._pronunciation_glyphs:
            try:
                # Use a sample pronunciation to get metrics
                sample_pronunciation = next(iter(self._pronunciation_glyphs.keys()))
                sample_glyph = self._pronunciation_glyphs[sample_pronunciation]
                width_raw = sample_glyph["advanceWidth"]
                height_raw = sample_glyph["advanceHeight"]
                origin_raw = sample_glyph["verticalOrigin"]

                advance_width = (
                    float(width_raw) if isinstance(width_raw, (int, float)) else 1000.0
                )
                advance_height = (
                    float(height_raw)
                    if isinstance(height_raw, (int, float))
                    else 1000.0
                )
                vertical_origin = (
                    float(origin_raw) if isinstance(origin_raw, (int, float)) else 880.0
                )

                self.logger.debug(
                    "Pinyin metrics from %s - width: %f, height: %f, vertical_origin: %f",
                    sample_pronunciation,
                    advance_width,
                    advance_height,
                    vertical_origin,
                )
                return PinyinMetrics(
                    width=advance_width,
                    height=advance_height,
                    vertical_origin=vertical_origin,
                )

            except (OSError, ValueError, RuntimeError, KeyError, TypeError) as e:
                self.logger.warning(
                    "Could not get pinyin metrics from pronunciation glyphs: %s", e
                )

        # Fallback to pinyin generator metrics
        fallback = self.pinyin_generator.get_metrics()
        self.logger.debug(
            "Fallback pinyin metrics - width: %f, height: %f, vertical_origin: %f",
            fallback.width,
            fallback.height,
            fallback.vertical_origin,
        )
        return fallback
