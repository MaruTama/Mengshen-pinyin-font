# -*- coding: utf-8 -*-
"""Main font builder with clean architecture and dependency injection."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Protocol, Union

# Font data types
FontTableData = Dict[
    str, Union[str, int, float, List[Dict[str, Union[str, int, float]]]]
]
FontData = Dict[str, Union[str, int, float, FontTableData]]

import orjson

from ..config import FontConfig, FontConstants, FontType, ProjectPaths
from ..data import CharacterDataManager, MappingDataManager, PinyinDataManager
from ..utils.cmap_utils import load_cmap_table_from_path
from ..utils.logging_config import get_builder_logger
from .font_assembler import FontAssembler
from .glyph_manager import GlyphManager


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
            from ..data.mapping_data import JsonCmapDataSource

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

        self.font_assembler = FontAssembler(
            font_config=self.font_config, paths=self.paths
        )

        # External tool interface
        self.external_tool = external_tool

        # Font data
        self._font_data: Optional[FontData] = None
        self._glyf_data: Optional[FontTableData] = None

    def build(self, output_path: Path) -> None:
        """Build the complete font."""
        try:
            self.logger.info(f"Starting font build for {self.font_type.name}...")

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

            self.logger.info(f"Font build completed successfully: {output_path}")

        except Exception as e:
            self.logger.error(f"Font build failed: {e}")
            raise

    def get_build_statistics(self) -> Dict[str, Union[str, int, float]]:
        """Get statistics about the built font."""
        return {"status": "placeholder"}

    def _load_templates(self) -> None:
        """Load font template files."""
        with open(self.template_main_path, "rb") as f:
            self._font_data = orjson.loads(f.read())

        with open(self.template_glyf_path, "rb") as f:
            self._glyf_data = orjson.loads(f.read())

    def _initialize_managers(self) -> None:
        """Initialize component managers."""
        self.glyph_manager.initialize(
            self._font_data,
            self._glyf_data,
            self.alphabet_pinyin_path,
            self.template_main_path,
        )
        # Set up utility cmap table for compatibility
        from ..processing.optimized_utility import set_cmap_table

        set_cmap_table(self._font_data["cmap"])

    def _add_cmap_uvs(self) -> None:
        """Add Unicode IVS (Ideographic Variant Selector) support.

        e.g.:
        hanzi_glyf　　　　標準の読みの拼音
        hanzi_glyf.ss00　ピンインの無い漢字グリフ。設定を変更するだけで拼音を変更できる
        hanzi_glyf.ss01　（異読のピンインがあるとき）標準の読みの拼音（uni4E0D と重複しているが GSUB の置換（多音字のパターン）を無効にして強制的に置き換えるため）
        hanzi_glyf.ss02　（異読のピンインがあるとき）以降、異読
        ...
        """
        # Initialize cmap_uvs table if not exists
        if "cmap_uvs" not in self._font_data:
            self._font_data["cmap_uvs"] = {}

        cmap_uvs = self._font_data["cmap_uvs"]
        IVS_BASE = FontConstants.IVS_BASE  # 0xE01E0 (917984)

        # Add IVS entries for single-pronunciation characters
        for char_info in self.character_manager.iter_single_pronunciation_characters():
            if not self.mapping_manager.has_glyph_for_character(char_info.character):
                continue

            unicode_value = ord(char_info.character)
            cid = self.mapping_manager.convert_hanzi_to_cid(char_info.character)

            if cid:
                # IVS selector for ss00 (no pinyin variant)
                ivs_key = f"{unicode_value} {IVS_BASE}"
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
                    ivs_key = f"{unicode_value} {IVS_BASE + i}"
                    cmap_uvs[ivs_key] = f"{cid}.ss{i:02d}"

        self.logger.debug(f"cmap_uvs entries: {len(cmap_uvs)}")

    def _add_glyph_order(self) -> None:
        """Add glyph order definition."""
        # Start with existing glyph order
        existing_order = set(self._font_data.get("glyph_order", []))

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
        self._font_data["glyph_order"] = new_glyph_order

        self.logger.debug(f"glyph order entries: {len(new_glyph_order)}")

    def _add_glyf(self) -> None:
        """Add pinyin-annotated glyphs using exact legacy logic."""
        # CRITICAL FIX: Use glyf template data (substance_glyf_table) instead of main template glyf
        # This matches legacy font.py where substance_glyf_table contains actual glyph contour data

        # Get the base glyf table from MAIN template (for metadata structure)
        base_glyf = self._font_data.get("glyf", {})

        # Use glyph_manager to generate all pinyin-annotated glyphs
        self.glyph_manager.generate_pinyin_glyphs()  # Generate pinyin alphabet glyphs
        self.glyph_manager.generate_hanzi_glyphs()  # Generate hanzi+pinyin composite glyphs

        # Get all generated glyphs from glyph_manager
        generated_glyphs = self.glyph_manager.get_all_glyphs()

        # CRITICAL FIX: Start with template glyf data that contains actual contours
        # base_glyf from main template has empty contours, _glyf_data has the actual contours
        new_glyf = dict(
            self._glyf_data
        )  # Use template glyf with contours as starting point

        # DEBUG: Verify hiragana contours are preserved
        if "cid01460" in new_glyf:
            contour_count = len(new_glyf["cid01460"].get("contours", []))
            self.logger.debug(
                f"new_glyf starts with cid01460 having {contour_count} contours"
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
            f" Found {len(pinyin_alphabet_glyphs)} pinyin alphabet glyphs in generated_glyphs"
        )
        self.logger.debug(
            f" First few pinyin alphabet glyph names: {list(pinyin_alphabet_glyphs.keys())[:5]}"
        )
        self.logger.debug(f" Total generated_glyphs keys: {len(generated_glyphs)}")
        self.logger.debug(
            f" All generated_glyphs keys starting with 'py': {[k for k in generated_glyphs.keys() if k.startswith('py')][:10]}"
        )
        new_glyf.update(pinyin_alphabet_glyphs)
        self.logger.debug(
            f" new_glyf now has {len(new_glyf)} glyphs after adding pinyin alphabets"
        )

        # 3. Add substance glyphs (CRITICAL: use glyf template for contour data)
        # This is the missing piece - we need to use _glyf_data for actual glyph contours
        substance_glyphs = {
            k: v for k, v in generated_glyphs.items() if not k.startswith("py_alphabet")
        }

        self.logger.debug(f" Processing {len(substance_glyphs)} substance glyphs")

        # For substance glyphs, merge with template glyf data to preserve contours
        for glyph_name, glyph_data in substance_glyphs.items():
            # Check if this is a base glyph that should have contour data from template
            base_glyph_name = glyph_name.split(".")[0]  # Remove .ss## suffix

            if base_glyph_name in self._glyf_data:
                template_glyph = self._glyf_data[base_glyph_name]

                # CRITICAL FIX: If generated glyph has no useful content (no references/contours), use template
                has_references = (
                    "references" in glyph_data
                    and len(glyph_data.get("references", [])) > 0
                )
                has_contours = (
                    "contours" in glyph_data and len(glyph_data.get("contours", [])) > 0
                )
                template_has_contours = (
                    "contours" in template_glyph
                    and len(template_glyph.get("contours", [])) > 0
                )

                if not has_references and not has_contours and template_has_contours:
                    # Generated glyph is empty but template has contours - use template completely
                    new_glyf[glyph_name] = template_glyph.copy()
                    self.logger.debug(
                        f"Used template completely for empty generated glyph: {glyph_name}"
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
                        f" Preserved contours for .ss00 glyph: {glyph_name}"
                    )
                else:
                    # For all other glyphs (with pinyin), use generated references completely
                    # This preserves the pinyin positioning and display
                    new_glyf[glyph_name] = glyph_data
                    self.logger.debug(
                        f" Used generated data for pinyin glyph: {glyph_name}"
                    )
            else:
                # Use generated glyph as-is (likely a composite glyph)
                new_glyf[glyph_name] = glyph_data
                self.logger.debug(
                    f" Used generated data for composite glyph: {glyph_name}"
                )

        # CRITICAL FIX: Ensure all template glyphs are included, especially basic characters
        # This preserves hiragana, katakana, alphabet characters that are not processed by character manager
        template_glyphs_added = 0
        for glyph_name, glyph_data in self._glyf_data.items():
            if glyph_name not in new_glyf:
                # Use template data completely - this preserves contours for basic characters
                new_glyf[glyph_name] = glyph_data.copy()
                template_glyphs_added += 1

                # Debug specific basic characters
                if glyph_name in ["cid01460", "cid00034", "cid01461", "cid01462"]:
                    contour_count = len(glyph_data.get("contours", []))
                    self.logger.debug(
                        f"Added template glyph {glyph_name} with {contour_count} contours"
                    )

        self.logger.debug(
            f" Added {template_glyphs_added} template glyphs to preserve basic characters"
        )

        # Update the font data
        self._font_data["glyf"] = new_glyf

        # Validate glyph count limits (legacy compatibility)
        # OpenType fonts have a hard limit of 65536 glyphs due to 16-bit indexing
        if len(new_glyf) > 65536:
            raise Exception("glyf table cannot contain more than 65536 glyphs.")

        self.logger.debug(f"glyf num : {len(new_glyf)}")

    def _add_gsub(self) -> None:
        """Add GSUB table for contextual substitution."""
        from ..processing.gsub_table_generator import GSUBTableGenerator

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
        self._font_data["GSUB"] = gsub_table

        self.logger.info("GSUB table generation completed")

    def _set_about_size(self) -> None:
        """Set font size metadata."""
        from ..config.font_name_tables import VERSION

        # Set font revision in head table (legacy: head.fontRevision = name_table.VERSION)
        if "head" not in self._font_data:
            self._font_data["head"] = {}

        self._font_data["head"]["fontRevision"] = VERSION

        # Set creation and modification dates to current generation time
        # Use the font assembler's timestamp method for consistency
        font_timestamp = self.font_assembler._get_current_font_timestamp()
        self._font_data["head"]["created"] = font_timestamp
        self._font_data["head"]["modified"] = font_timestamp

        # Optional: Add generation timestamp info for debugging
        from datetime import datetime, timezone

        generation_time = datetime.now(timezone.utc)
        self.logger.info(
            f"Font metadata set - Version: {VERSION}, Generated: {generation_time.strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )

        # Get pinyin glyph metrics from glyph_manager
        # Assuming glyph_manager has a method to get pinyin glyph metrics
        # For now, use a placeholder or retrieve from a known pinyin glyph
        # This needs to be properly implemented in GlyphManager
        # For now, let's assume a default value or retrieve from a specific glyph
        # This is a critical part that needs to match legacy behavior

        # Placeholder for advanceAddedPinyinHeight - this needs to come from actual pinyin glyphs
        # For now, we'll use a value that is likely to be larger than default yMax/ascender
        # In a real scenario, this would be calculated from the generated pinyin glyphs

        # Retrieve pinyin glyph metrics from glyph_manager
        # This assumes glyph_manager has a method to provide this
        # If not, we need to add it to glyph_manager
        pinyin_metrics = self.glyph_manager.get_pinyin_metrics()

        if pinyin_metrics:
            advanceAddedPinyinHeight = pinyin_metrics.height

            if (
                "head" in self._font_data
                and "yMax" in self._font_data["head"]
                and advanceAddedPinyinHeight > self._font_data["head"]["yMax"]
            ):
                self._font_data["head"]["yMax"] = advanceAddedPinyinHeight

            if (
                "hhea" in self._font_data
                and "ascender" in self._font_data["hhea"]
                and advanceAddedPinyinHeight > self._font_data["hhea"]["ascender"]
            ):
                self._font_data["hhea"]["ascender"] = advanceAddedPinyinHeight
                # Also update OS/2 usWinAscent if hhea.ascender is updated
                if (
                    "OS_2" in self._font_data
                    and "usWinAscent" in self._font_data["OS_2"]
                ):
                    self._font_data["OS_2"]["usWinAscent"] = advanceAddedPinyinHeight

        self.logger.debug(f"font revision set to: {VERSION}")

    def _set_copyright(self) -> None:
        """Set font copyright and naming information."""
        from ..config import HAN_SERIF, HANDWRITTEN

        # Set name table based on font type
        if self.font_type == FontType.HAN_SERIF:
            self._font_data["name"] = HAN_SERIF
            self.logger.debug("name table set: HAN_SERIF")
        elif self.font_type == FontType.HANDWRITTEN:
            self._font_data["name"] = HANDWRITTEN
            self.logger.debug("name table set: HANDWRITTEN")
        else:
            raise ValueError(f"Unsupported font type: {self.font_type}")

        self.logger.debug(f"name table entries: {len(self._font_data['name'])}")

    def _save_as_json(self, output_path: Path) -> None:
        """Save font data as JSON."""
        with open(output_path, "wb") as f:
            f.write(orjson.dumps(self._font_data, option=orjson.OPT_INDENT_2))

    def _convert_json_to_otf(self, json_path: Path, output_path: Path) -> None:
        """Convert JSON font to OTF using external tools."""
        if self.external_tool:
            self.external_tool.convert_json_to_otf(json_path, output_path)
        else:
            # Fallback to shell command (legacy compatibility)
            import subprocess

            try:
                subprocess.run(
                    ["otfccbuild", str(json_path), "-o", str(output_path)],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Error during otfccbuild: {e.stderr}")
                raise
            except subprocess.TimeoutExpired as e:
                self.logger.error(f"otfccbuild timed out: {e}")
                raise
            except FileNotFoundError:
                self.logger.error(
                    "Error: otfccbuild command not found. Please ensure it's installed and in your PATH."
                )
                raise
