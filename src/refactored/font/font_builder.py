# -*- coding: utf-8 -*-
"""Main font builder with clean architecture and dependency injection."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, Protocol, cast

import orjson

from ..config import (
    HAN_SERIF,
    HANDWRITTEN,
    FontConstants,
    FontMetadata,
    FontType,
    ProjectPaths,
)
from ..config.font_config import FontConfig
from ..config.font_name_tables import VERSION
from ..data import CharacterDataManager, MappingDataManager, PinyinDataManager
from ..data.mapping_data import JsonCmapDataSource
from ..processing.gsub_table_generator import GSUBTableGenerator
from ..processing.optimized_utility import set_cmap_table

# Import comprehensive type definitions
from ..types import HeadTable, HheaTable, OS2Table, StatsDict
from ..utils.cmap_utils import load_cmap_table_from_path
from ..utils.logging_config import get_builder_logger
from .font_assembler import FontAssembler
from .glyph_manager import GlyphManager


class ExternalToolInterface(Protocol):
    """Protocol for external tool execution."""

    def convert_json_to_otf(self, json_path: Path, output_path: Path) -> None:
        """Convert JSON font description to OTF font."""


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
        paths: Optional[ProjectPaths] = None,
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

        # Logging
        self.logger = get_builder_logger()
        self.character_manager = character_manager or CharacterDataManager(
            self.pinyin_manager
        )
        # Create mapping manager with correct template path
        if mapping_manager is None:

            cmap_source = JsonCmapDataSource(self.template_main_path)
            mapping_manager = MappingDataManager(
                cmap_source=cmap_source, paths=self.paths
            )
        self.mapping_manager = mapping_manager

        # Load cmap table for character conversion
        self._cmap_table = load_cmap_table_from_path(str(self.template_main_path))

        # Font processing components
        self.glyph_manager = GlyphManager(
            font_type=font_type,
            font_config=self.font_config,
            character_manager=self.character_manager,
            mapping_manager=self.mapping_manager,
        )

        font_config_obj: FontMetadata = FontConfig.get_config(font_type)
        self.font_assembler = FontAssembler(
            font_config=font_config_obj, paths=self.paths
        )

        # External tool interface
        self.external_tool = external_tool

        # Font data with proper typing
        self._font_data: Optional[Dict[str, Any]] = None
        self._glyf_data: Optional[Dict[str, Any]] = None

    def build(self, output_path: Path) -> None:
        """Build the complete font."""
        try:
            self.logger.info("Starting font build for %s...", self.font_type.name)

            # Load font templates
            self.logger.info("Loading font templates...")
            self._load_templates()

            # Initialize managers
            self.logger.info("Initializing managers...")
            self._initialize_managers()

            # Build font components
            self.logger.info("Adding cmap_uvs table...")
            self._add_cmap_uvs()

            self.logger.info("Adding glyph_order table...")
            self._add_glyph_order()

            self.logger.info("Adding glyf table...")
            self._add_glyf()

            self.logger.info("Adding GSUB table...")
            self._add_gsub()

            self.logger.info("Setting font metadata...")
            self._set_about_size()
            self._set_copyright()

            # Save and convert
            self.logger.info("Saving and converting font...")
            temp_json_path = self.paths.get_temp_json_path("template_output.json")
            self._save_as_json(temp_json_path)
            self._convert_json_to_otf(temp_json_path, output_path)

            self.logger.info("Font build completed successfully: %s", output_path)

        except (OSError, ValueError, RuntimeError, KeyError, TypeError) as e:
            self.logger.error("Font build failed: %s", e)
            raise
        except Exception as e:
            self.logger.error("Unexpected font build error: %s", e)
            raise

    def get_build_statistics(self) -> StatsDict:
        """Get statistics about the built font."""
        if not self._font_data:
            return {"status": "not_built"}

        stats: StatsDict = {
            "status": "built",
            "font_type": int(self.font_type),
        }

        # Add glyph counts if available
        if "glyf" in self._font_data:
            glyf_table = self._font_data["glyf"]
            if hasattr(glyf_table, "__len__"):
                stats["total_glyphs"] = len(glyf_table)

        # Add generated glyph counts if glyph_manager is available
        if hasattr(self, "glyph_manager") and self.glyph_manager:
            generated_glyphs = self.glyph_manager.get_all_glyphs()
            pinyin_glyph_names = self.glyph_manager.get_pinyin_glyph_names()

            stats["generated_glyphs"] = len(generated_glyphs)
            stats["pinyin_glyphs"] = len(pinyin_glyph_names)

        # Add font metrics if available
        if "head" in self._font_data:
            head_table = cast(HeadTable, self._font_data["head"])
            if isinstance(head_table, dict):
                if "yMax" in head_table:
                    ymax_val = head_table["yMax"]
                    if isinstance(ymax_val, (int, float)):
                        stats["ymax"] = ymax_val
                if "fontRevision" in head_table:
                    revision_val = head_table["fontRevision"]
                    if isinstance(revision_val, (int, float)):
                        stats["font_revision"] = revision_val

        if "hhea" in self._font_data:
            hhea_table = cast(HheaTable, self._font_data["hhea"])
            if isinstance(hhea_table, dict) and "ascender" in hhea_table:
                ascender_val = hhea_table["ascender"]
                if isinstance(ascender_val, (int, float)):
                    stats["ascender"] = ascender_val

        return stats

    def _load_templates(self) -> None:
        """Load font template files."""
        with open(self.template_main_path, "rb") as f:
            self._font_data = orjson.loads(f.read())

        with open(self.template_glyf_path, "rb") as f:
            self._glyf_data = orjson.loads(f.read())

    def _initialize_managers(self) -> None:
        """Initialize component managers."""
        if self._font_data is None or self._glyf_data is None:
            raise ValueError("Font data not loaded")

        # Cast to proper types for the glyph manager
        font_data_dict = cast(Dict[str, Dict[str, Any]], self._font_data)
        glyf_data_dict = cast(Dict[str, Dict[str, Any]], self._glyf_data)

        self.glyph_manager.initialize(
            font_data_dict,
            glyf_data_dict,
            self.alphabet_pinyin_path,
            self.template_main_path,
        )

        cmap_data = self._font_data.get("cmap")
        if isinstance(cmap_data, dict):
            cmap_table = cast(Dict[str, str], cmap_data)
            set_cmap_table(cmap_table)

    def _add_cmap_uvs(self) -> None:
        """Add Unicode IVS (Ideographic Variant Selector) support.

        e.g.:
        hanzi_glyf　　　　標準の読みの拼音
        hanzi_glyf.ss00　ピンインの無い漢字グリフ。設定を変更するだけで拼音を変更できる
        hanzi_glyf.ss01　（異読のピンインがあるとき）標準の読みの拼音（uni4E0D と重複しているが GSUB の置換（多音字のパターン）を無効にして強制的に置き換えるため）
        hanzi_glyf.ss02　（異読のピンインがあるとき）以降、異読
        ...
        """
        if self._font_data is None:
            raise ValueError("Font data not loaded")

        # Initialize cmap_uvs table if not exists
        if "cmap_uvs" not in self._font_data:
            self._font_data["cmap_uvs"] = {}

        cmap_uvs = cast(Dict[str, str], self._font_data["cmap_uvs"])
        ivs_base = FontConstants.IVS_BASE  # 0xE01E0 (917984)

        # Add IVS entries for single-pronunciation characters
        for char_info in self.character_manager.iter_single_pronunciation_characters():
            if not self.mapping_manager.has_glyph_for_character(char_info.character):
                continue

            unicode_value = ord(char_info.character)
            cid = self.mapping_manager.convert_hanzi_to_cid(char_info.character)

            if cid:
                # IVS selector for ss00 (no pinyin variant)
                ivs_key = f"{unicode_value} {ivs_base}"
                cmap_uvs[ivs_key] = f"{cid}.ss00"

        # Add IVS entries for multiple-pronunciation characters
        for (
            char_info
        ) in self.character_manager.iter_multiple_pronunciation_characters():
            if not self.mapping_manager.has_glyph_for_character(char_info.character):
                continue

            unicode_value = ord(char_info.character)
            cid = self.mapping_manager.convert_hanzi_to_cid(char_info.character)

            if cid:
                # IVS selectors for all variants (ss00 through ssNN)
                num_variants = len(char_info.pronunciations) + 1  # +1 for ss00
                for i in range(num_variants):
                    ivs_key = f"{unicode_value} {ivs_base + i}"
                    cmap_uvs[ivs_key] = f"{cid}.ss{i:02d}"

        self.logger.debug("cmap_uvs entries: %d", len(cmap_uvs))

    def _add_glyph_order(self) -> None:
        """Add glyph order definition."""
        if self._font_data is None:
            raise ValueError("Font data not loaded")

        # Start with existing glyph order
        glyph_order_raw = self._font_data.get("glyph_order", [])
        if isinstance(glyph_order_raw, list):
            existing_order = set(glyph_order_raw)
        else:
            existing_order = set()

        # Add hanzi glyphs for single-pronunciation characters
        for char_info in self.character_manager.iter_single_pronunciation_characters():
            if not self.mapping_manager.has_glyph_for_character(char_info.character):
                continue

            cid = self.mapping_manager.convert_hanzi_to_cid(char_info.character)
            if cid:
                existing_order.add(f"{cid}.ss00")

        # Add hanzi glyphs for multiple-pronunciation characters
        for (
            char_info
        ) in self.character_manager.iter_multiple_pronunciation_characters():
            if not self.mapping_manager.has_glyph_for_character(char_info.character):
                continue

            cid = self.mapping_manager.convert_hanzi_to_cid(char_info.character)
            if cid:
                # Add all stylistic set variants (ss00 through ssNN)
                num_variants = len(char_info.pronunciations) + 1  # +1 for ss00
                for i in range(num_variants):
                    existing_order.add(f"{cid}.ss{i:02d}")

        # Add pinyin alphabet glyphs
        pinyin_glyph_names = self.glyph_manager.get_pinyin_glyph_names()
        existing_order.update(pinyin_glyph_names)

        # Sort and set new glyph order
        new_glyph_order = list(existing_order)
        new_glyph_order.sort()
        if self._font_data is not None:
            self._font_data["glyph_order"] = new_glyph_order

        self.logger.debug("glyph order entries: %d", len(new_glyph_order))

    def _add_glyf(self) -> None:
        """Add pinyin-annotated glyphs using exact legacy logic."""
        # Use glyf template data (substance_glyf_table) instead of main template glyf
        # This matches legacy font.py where substance_glyf_table contains actual glyph contour data

        if self._font_data is None or self._glyf_data is None:
            raise ValueError("Font data not loaded")

        # Get the base glyf table from MAIN template (for metadata structure)
        base_glyf_raw = self._font_data.get("glyf", {})
        base_glyf = (
            cast(Dict[str, Any], base_glyf_raw)
            if isinstance(base_glyf_raw, dict)
            else {}
        )

        # Use glyph_manager to generate all pinyin-annotated glyphs
        self.glyph_manager.generate_pinyin_glyphs()  # Generate pinyin alphabet glyphs
        self.glyph_manager.generate_hanzi_glyphs()  # Generate hanzi+pinyin composite glyphs

        # Get all generated glyphs from glyph_manager
        generated_glyphs = self.glyph_manager.get_all_glyphs()

        # Start with template glyf data that contains actual contours
        # base_glyf from main template has empty contours, _glyf_data has the actual contours
        new_glyf = dict(
            self._glyf_data
        )  # Use template glyf with contours as starting point

        # DEBUG: Verify hiragana contours are preserved
        if "cid01460" in new_glyf:
            glyph_data = new_glyf["cid01460"]
            if isinstance(glyph_data, dict):
                contours = glyph_data.get("contours", [])
                contour_count = len(contours) if isinstance(contours, list) else 0
                self.logger.debug(
                    "new_glyf starts with cid01460 having %d contours", contour_count
                )

        # Merge any metadata from base_glyf that might be needed
        for glyph_name, glyph_data in base_glyf.items():
            if glyph_name not in new_glyf:
                new_glyf[glyph_name] = glyph_data

        # 2. Add pinyin alphabet glyphs (from legacy py_alphabet)
        pinyin_alphabet_glyphs = {
            k: v for k, v in generated_glyphs.items() if k.startswith("py_alphabet")
        }
        self.logger.debug(
            " Found %d pinyin alphabet glyphs in generated_glyphs",
            len(pinyin_alphabet_glyphs),
        )
        self.logger.debug(
            " First few pinyin alphabet glyph names: %s",
            list(pinyin_alphabet_glyphs.keys())[:5],
        )
        self.logger.debug(" Total generated_glyphs keys: %d", len(generated_glyphs))
        pinyin_alphabet_count = len(
            [k for k in generated_glyphs if k.startswith("py_alphabet")]
        )
        self.logger.debug(
            " Generated pinyin alphabet glyphs: %d", pinyin_alphabet_count
        )
        new_glyf.update(pinyin_alphabet_glyphs)
        self.logger.debug(
            " new_glyf now has %d glyphs after adding pinyin alphabets", len(new_glyf)
        )

        # 3. Add substance glyphs (CRITICAL: use glyf template for contour data)
        # This is the missing piece - we need to use _glyf_data for actual glyph contours
        substance_glyphs = {
            k: v for k, v in generated_glyphs.items() if not k.startswith("py_alphabet")
        }

        self.logger.debug(" Processing %d substance glyphs", len(substance_glyphs))

        # For substance glyphs, merge with template glyf data to preserve contours
        for glyph_name, glyph_data in substance_glyphs.items():
            # Check if this is a base glyph that should have contour data from template
            base_glyph_name = glyph_name.split(".")[0]  # Remove .ss## suffix

            if base_glyph_name in self._glyf_data:
                template_glyph = cast(Dict[str, Any], self._glyf_data[base_glyph_name])

                # If generated glyph has no useful content (no references/contours), use template
                references_raw = glyph_data.get("references", [])
                has_references = (
                    "references" in glyph_data
                    and isinstance(references_raw, list)
                    and len(references_raw) > 0
                )
                contours_raw = glyph_data.get("contours", [])
                has_contours = (
                    "contours" in glyph_data
                    and isinstance(contours_raw, list)
                    and len(contours_raw) > 0
                )
                template_contours_raw = template_glyph.get("contours", [])
                template_has_contours = (
                    "contours" in template_glyph
                    and isinstance(template_contours_raw, list)
                    and len(template_contours_raw) > 0
                )

                if not has_references and not has_contours and template_has_contours:
                    # Generated glyph is empty but template has contours - use template completely
                    new_glyf[glyph_name] = template_glyph.copy()
                    self.logger.debug(
                        "Used template completely for empty generated glyph: %s",
                        glyph_name,
                    )
                elif glyph_name.endswith(".ss00"):
                    # For .ss00 glyphs (hanzi without pinyin), use template contour data
                    merged_glyph = template_glyph.copy()
                    # Update metrics from generated data while keeping contours
                    for key, value in glyph_data.items():
                        if key not in ["contours"]:  # Preserve template contours
                            merged_glyph[key] = value
                    new_glyf[glyph_name] = merged_glyph
                    self.logger.debug(
                        " Preserved contours for .ss00 glyph: %s", glyph_name
                    )
                else:
                    # For all other glyphs (with pinyin), use generated references completely
                    # This preserves the pinyin positioning and display
                    new_glyf[glyph_name] = glyph_data
                    self.logger.debug(
                        " Used generated data for pinyin glyph: %s", glyph_name
                    )
            else:
                # Use generated glyph as-is (likely a composite glyph)
                new_glyf[glyph_name] = glyph_data
                self.logger.debug(
                    " Used generated data for composite glyph: %s", glyph_name
                )

        # Ensure all template glyphs are included, especially basic characters
        # This preserves hiragana, katakana, alphabet characters that are not processed by character manager
        template_glyphs_added = 0
        for glyph_name, glyph_data in self._glyf_data.items():
            if glyph_name not in new_glyf:
                # Use template data completely - this preserves contours for basic characters
                if isinstance(glyph_data, dict) and hasattr(glyph_data, "copy"):
                    new_glyf[glyph_name] = glyph_data.copy()
                else:
                    new_glyf[glyph_name] = glyph_data
                template_glyphs_added += 1

                # Debug specific basic characters
                if glyph_name in [
                    "cid01460",
                    "cid00034",
                    "cid01461",
                    "cid01462",
                ] and isinstance(glyph_data, dict):
                    contours = glyph_data.get("contours", [])
                    contour_count = len(contours) if isinstance(contours, list) else 0
                    self.logger.debug(
                        "Added template glyph %s with %d contours",
                        glyph_name,
                        contour_count,
                    )

        self.logger.debug(
            " Added %d template glyphs to preserve basic characters",
            template_glyphs_added,
        )

        # Update the font data
        if self._font_data is not None:
            self._font_data["glyf"] = new_glyf

        # Validate glyph count limits (legacy compatibility)
        # OpenType fonts have a hard limit of 65536 glyphs due to 16-bit indexing
        if len(new_glyf) > 65536:
            raise Exception("glyf table cannot contain more than 65536 glyphs.")

        self.logger.debug("glyf num : %d", len(new_glyf))

    def _add_gsub(self) -> None:
        """Add GSUB table for contextual substitution."""

        # Create GSUB table generator with pattern files
        gsub_generator = GSUBTableGenerator(
            pattern_one_path=self.pattern_one_path,
            pattern_two_path=self.pattern_two_path,
            exception_pattern_path=self.exception_pattern_path,
            character_manager=self.character_manager,
            mapping_manager=self.mapping_manager,
            cmap_table=self._cmap_table,
        )

        # Generate and add GSUB table
        gsub_table = gsub_generator.generate_gsub_table()
        if self._font_data is not None:
            self._font_data["GSUB"] = gsub_table

        self.logger.info("GSUB table generation completed")

    def _set_about_size(self) -> None:
        """Set font size metadata."""

        if self._font_data is None:
            raise ValueError("Font data not loaded")

        self.font_assembler.set_font_metadata(self._font_data, self.font_type)

        # Set font metrics to accommodate pinyin height (legacy compatibility)
        # This matches the legacy set_about_size() method behavior
        pinyin_metrics = self.glyph_manager.get_pinyin_metrics()

        if pinyin_metrics:
            advanceAddedPinyinHeight = pinyin_metrics.height

            # Update yMax if pinyin height exceeds current yMax
            # すべてのグリフの輪郭を含む範囲
            if "head" in self._font_data:
                head_table = cast(HeadTable, self._font_data["head"])
                if isinstance(head_table, dict) and "yMax" in head_table:
                    ymax_val = head_table["yMax"]
                    if isinstance(
                        ymax_val, (int, float)
                    ) and advanceAddedPinyinHeight > float(ymax_val):
                        head_table["yMax"] = advanceAddedPinyinHeight

            # Update ascender and usWinAscent if pinyin height exceeds current ascender
            # 原点からグリフの上端までの距離
            if "hhea" in self._font_data:
                hhea_table = cast(HheaTable, self._font_data["hhea"])
                if isinstance(hhea_table, dict) and "ascender" in hhea_table:
                    ascender_val = hhea_table["ascender"]
                    if (
                        isinstance(ascender_val, (int, float))
                        and advanceAddedPinyinHeight > ascender_val
                    ):
                        # Update ascender first
                        hhea_table["ascender"] = advanceAddedPinyinHeight

                        # Then update OS/2 usWinAscent (Windows-specific ascent metric)
                        if "OS_2" in self._font_data:
                            os2_table = cast(OS2Table, self._font_data["OS_2"])
                            if (
                                isinstance(os2_table, dict)
                                and "usWinAscent" in os2_table
                            ):
                                os2_table["usWinAscent"] = advanceAddedPinyinHeight

            # Debug logging with safe access
            head_table = cast(HeadTable, self._font_data.get("head", {}))
            hhea_table = cast(HheaTable, self._font_data.get("hhea", {}))
            os2_table = cast(OS2Table, self._font_data.get("OS_2", {}))

            ymax_val = (
                head_table.get("yMax", "unknown")
                if isinstance(head_table, dict)
                else "unknown"
            )
            hhea_ascent_debug = (
                hhea_table.get("ascender", "unknown")
                if isinstance(hhea_table, dict)
                else "unknown"
            )
            us_win_ascent_val = (
                os2_table.get("usWinAscent", "unknown")
                if isinstance(os2_table, dict)
                else "unknown"
            )

            self.logger.debug(
                "Font metrics updated - yMax: %s, ascender: %s, usWinAscent: %s",
                ymax_val,
                hhea_ascent_debug,
                us_win_ascent_val,
            )

        self.logger.debug("font revision set to: %s", VERSION)

    def _set_copyright(self) -> None:
        """Set font copyright and naming information."""

        if self._font_data is None:
            raise ValueError("Font data not loaded")

        # Set name table based on font type
        if self.font_type == FontType.HAN_SERIF:
            self._font_data["name"] = cast(Any, HAN_SERIF)
            self.logger.debug("name table set: HAN_SERIF")
        elif self.font_type == FontType.HANDWRITTEN:
            self._font_data["name"] = cast(Any, HANDWRITTEN)
            self.logger.debug("name table set: HANDWRITTEN")
        else:
            raise ValueError(f"Unsupported font type: {self.font_type}")

        name_table = self._font_data.get("name")
        if name_table and hasattr(name_table, "__len__"):
            try:
                self.logger.debug("name table entries: %d", len(name_table))
            except TypeError:
                self.logger.debug("name table entries: unknown (not sized)")
        else:
            self.logger.debug("name table entries: unknown")

    def _save_as_json(self, output_path: Path) -> None:
        """Save font data as JSON."""
        with open(output_path, "wb") as f:
            f.write(orjson.dumps(self._font_data, option=orjson.OPT_INDENT_2))

    def _convert_json_to_otf(self, json_path: Path, output_path: Path) -> None:
        """Convert JSON font to OTF using external tools."""
        if self.external_tool:
            self.external_tool.convert_json_to_otf(json_path, output_path)
        else:
            try:
                subprocess.run(
                    ["otfccbuild", str(json_path), "-o", str(output_path)],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
            except subprocess.CalledProcessError as e:
                self.logger.error("Error during otfccbuild: %s", e.stderr)
                raise
            except subprocess.TimeoutExpired as e:
                self.logger.error("otfccbuild timed out: %s", e)
                raise
            except FileNotFoundError:
                self.logger.error(
                    "Error: otfccbuild command not found. Please ensure it's installed and in your PATH."
                )
                raise
