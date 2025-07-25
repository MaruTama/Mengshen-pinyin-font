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
    """Protocol interface for external tool execution.

    レガシー実装からの重要な知識（元コメントを完全保持）:
    外部ツールの実行を抽象化し、テスト可能性を向上させます。

    This protocol defines the interface for external tool execution,
    primarily used for font conversion operations. It enables:

    - Dependency injection for testing
    - Mock implementations for unit tests
    - Alternative tool implementations
    - Isolated testing without external dependencies

    The main use case is the otfccbuild tool for converting JSON font
    descriptions to binary OTF font files.

    Implementation Note:
        Production code typically uses direct subprocess calls to otfccbuild,
        while test code can use mock implementations that avoid actual
        external tool execution.
    """

    def convert_json_to_otf(self, json_path: Path, output_path: Path) -> None:
        """Convert JSON font description to OTF font file.

        Args:
            json_path: Path to the input JSON font description file
            output_path: Path where the output OTF font file should be created

        Raises:
            subprocess.CalledProcessError: If the conversion tool fails
            FileNotFoundError: If the conversion tool is not available
            OSError: If file operations fail

        Note:
            Implementations should handle timeouts and provide detailed error
            information for debugging font conversion issues.
        """


class FontBuilder:
    """Main font builder that orchestrates the complete font generation process.

    レガシー実装からの重要な知識（元コメントを完全保持）:
    このクラスはフォント生成の全体プロセスを統制し、正確な順序で実行します。

    FontBuilder is the central coordinator for generating pinyin-annotated Chinese fonts.
    It manages the complex process of:

    1. Font Template Processing:
       - Loading base font templates (main + glyf)
       - Preserving original character contours and metrics
       - Setting up font metadata and structure

    2. Pinyin Integration:
       - Generating pinyin alphabet glyphs
       - Creating composite hanzi+pinyin glyphs
       - Managing stylistic set variants for multi-pronunciation characters

    3. OpenType Feature Generation:
       - Unicode IVS (Ideographic Variant Selector) support
       - GSUB table for contextual substitution
       - Proper glyph ordering and naming

    4. Font Assembly and Output:
       - Metric calculation and adjustment
       - Final font validation
       - Binary font file generation via otfccbuild

    Key Design Principles:
    - Dependency injection for testing and flexibility
    - Comprehensive error handling and logging
    - Legacy compatibility with original implementation
    - Modular design with clear separation of concerns

    Attributes:
        font_type: The type of font being generated (HAN_SERIF or HANDWRITTEN)
        font_config: Configuration object for the specific font type
        paths: Project paths for file locations
        logger: Configured logger for this component
        glyph_manager: Manages glyph generation and processing
        font_assembler: Handles font metadata and assembly
        character_manager: Manages character data and pronunciations
        mapping_manager: Handles character-to-glyph mapping
        external_tool: Interface for external tool execution (optional)
    """

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
        """Initialize FontBuilder with all required dependencies and file paths.

        レガシー実装からの重要な知識（元コメントを完全保持）:
        依存性注入によってテスト可能性と柔軟性を確保します。

        Args:
            font_type: Type of font to generate (HAN_SERIF or HANDWRITTEN)
            template_main_path: Path to main font template JSON file
            template_glyf_path: Path to glyf template JSON file with contour data
            alphabet_pinyin_path: Path to pinyin alphabet glyph JSON file
            pattern_one_path: Path to pattern one file for multi-character contexts
            pattern_two_path: Path to pattern two file JSON for contextual rules
            exception_pattern_path: Path to exception pattern JSON file
            pinyin_manager: Optional pinyin data manager (creates default if None)
            character_manager: Optional character data manager (creates default if None)
            mapping_manager: Optional mapping data manager (creates default if None)
            external_tool: Optional external tool interface for testing
            paths: Optional project paths configuration (creates default if None)

        Raises:
            ValueError: If invalid font_type is provided
            FileNotFoundError: If required template files don't exist

        Note:
            The constructor sets up all managers and paths but doesn't load font data.
            Call build() method to start the actual font generation process.
            Dependency injection allows for easy testing and customization.
        """
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
        """Build the complete font following exact legacy processing order.

        レガシー実装からの重要な知識（元コメントを完全保持）:
        フォント作成の正確な順序が重要です。以下の順序で実行されます:

        1. Load font templates (フォントテンプレート読み込み)
        2. Initialize managers (マネージャー初期化)
        3. Add cmap_uvs table (Unicode IVSサポート)
        4. Add glyph_order table (グリフ順序定義)
        5. Add glyf table (ピンイン付きグリフ生成)
        6. Add GSUB table (文脈的置換ルール)
        7. Set font metadata (フォントメタデータ設定)
        8. Save and convert (保存と変換)

        Args:
            output_path: Path where the final font file will be saved

        Raises:
            ValueError: If font data cannot be loaded or is invalid
            RuntimeError: If font generation process fails
            OSError: If file operations fail
            KeyError: If required font tables are missing
            TypeError: If data types are incompatible
        """
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
        """Get comprehensive statistics about the built font.

        Returns detailed metrics about the font generation process including:
        - Build status (built/not_built)
        - Font type identifier
        - Total glyph counts (if available)
        - Generated glyph counts from glyph_manager
        - Pinyin-specific glyph counts
        - Font metrics (yMax, ascender, font revision)

        Returns:
            StatsDict: Dictionary containing font statistics with the following keys:
                - status: "built" or "not_built"
                - font_type: Integer font type identifier
                - total_glyphs: Total number of glyphs (optional)
                - generated_glyphs: Number of generated glyphs (optional)
                - pinyin_glyphs: Number of pinyin glyphs (optional)
                - ymax: Font yMax value (optional)
                - ascender: Font ascender value (optional)
                - font_revision: Font revision number (optional)

        Note:
            Optional fields are only included if the corresponding data is available
            and the font has been successfully built.
        """
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
        """Load font template files containing base font structure and glyph data.

        レガシー実装からの重要な知識（元コメントを完全保扶）:
        テンプレートファイルの読み込みがフォント生成の基礎となります。

        This method loads two critical template files:

        1. Main Template (template_main_path):
           - Contains font metadata, metrics, and basic structure
           - Includes cmap table, head table, hhea table, etc.
           - Provides the foundation for the new font

        2. Glyf Template (template_glyf_path):
           - Contains actual glyph contour data
           - Preserves original character shapes
           - Essential for character rendering

        Both files are JSON format created by otfcc tool from source fonts.

        Raises:
            FileNotFoundError: If template files don't exist
            orjson.JSONDecodeError: If template files contain invalid JSON
            OSError: If file reading fails

        Note:
            Template loading must succeed before any other font processing can begin.
            The separation of main and glyf templates allows for efficient processing
            of large font files where glyf data can be several megabytes.
        """
        with open(self.template_main_path, "rb") as f:
            self._font_data = orjson.loads(f.read())

        with open(self.template_glyf_path, "rb") as f:
            self._glyf_data = orjson.loads(f.read())

    def _initialize_managers(self) -> None:
        """Initialize component managers with loaded font data.

        レガシー実装からの重要な知識（元コメントを完全保持）:
        マネージャーの初期化が正しい順序で実行されることが重要です。

        This method initializes the core processing managers with the loaded font data:

        1. GlyphManager Initialization:
           - Provides font data and glyf data dictionaries
           - Sets up alphabet pinyin path for character processing
           - Configures template main path for reference

        2. Global CMap Table Setup:
           - Extracts cmap data from font template
           - Sets global cmap table for character-to-CID conversion
           - Enables consistent character mapping across all components

        The initialization order is critical for proper font generation.
        All managers must be initialized before font table generation begins.

        Raises:
            ValueError: If font data is not loaded
            TypeError: If data types are incompatible

        Note:
            This method must be called after _load_templates() and before any
            font table generation methods. The cmap table setup enables global
            character-to-glyph mapping used throughout the font generation process.
        """
        if self._font_data is None or self._glyf_data is None:
            raise ValueError("Font data not loaded")

        # Cast to proper types for the glyph manager
        font_data_dict = cast(Dict[str, Dict[str, Any]], self._font_data)
        glyf_data_dict = cast(Dict[str, Dict[str, Any]], self._glyf_data)

        self.glyph_manager.initialize(
            font_data_dict,
            glyf_data_dict,
            self.alphabet_pinyin_path,
        )

        cmap_data = self._font_data.get("cmap")
        if isinstance(cmap_data, dict):
            cmap_table = cast(Dict[str, str], cmap_data)
            set_cmap_table(cmap_table)

    def _add_cmap_uvs(self) -> None:
        """Add Unicode IVS (Ideographic Variant Selector) support.

        レガシー実装からの重要な知識（元コメントを完全保持）:

        IVS (Ideographic Variant Selector) の使用例:
        - hanzi_glyf　　　　標準の読みの拼音
        - hanzi_glyf.ss00　ピンインの無い漢字グリフ。設定を変更するだけで拼音を変更できる
        - hanzi_glyf.ss01　（異読のピンインがあるとき）標準の読みの拼音
          （uni4E0D と重複しているが GSUB の置換（多音字のパターン）を無効にして強制的に置き換えるため）
        - hanzi_glyf.ss02　（異読のピンインがあるとき）以降、異読
        - ...

        This method creates IVS entries for both single and multiple pronunciation characters,
        allowing users to select specific pronunciations through variant selectors.

        Technical Details:
        - Uses IVS base value (0xE01E0 / 917984) as starting point
        - Creates .ss00 variants for no-pinyin display
        - Creates .ss01+ variants for alternative pronunciations
        - Handles both single and multiple pronunciation characters
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
        """Add glyph order definition for proper font rendering.

        レガシー実装からの重要な知識（元コメントを完全保持）:
        グリフ順序の正確な定義がフォントの正常なレンダリングに必要です。

        This method defines the order in which glyphs appear in the font file.
        Proper glyph ordering is essential for:
        - Font rendering engines
        - Text shaping systems
        - Glyph lookup operations
        - Unicode compliance

        The glyph order includes:
        1. Existing glyphs from template
        2. Stylistic set variants (.ss00, .ss01, etc.) for single pronunciations
        3. Multiple stylistic set variants for multi-pronunciation characters
        4. Pinyin alphabet glyphs

        All glyphs are sorted alphabetically for consistent ordering.

        Note:
            The glyph order affects font file structure but not visual rendering.
            However, consistent ordering is important for font tools and debugging.
        """
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
        """Add pinyin-annotated glyphs using exact legacy logic.

        レガシー実装からの重要な知識（元コメントを完全保持）:
        - Use glyf template data (substance_glyf_table) instead of main template glyf
        - This matches legacy font.py where substance_glyf_table contains actual glyph contour data
        """
        if self._font_data is None or self._glyf_data is None:
            raise ValueError("Font data not loaded")

        # Step 1: Prepare base glyf structure with template data
        new_glyf = self._prepare_base_glyf_structure()

        # Step 2: Generate and add pinyin glyphs
        generated_glyphs = self._generate_pinyin_glyphs()

        # Step 3: Add pinyin alphabet glyphs (from legacy py_alphabet)
        self._add_pinyin_alphabet_glyphs(new_glyf, generated_glyphs)

        # Step 4: Add substance glyphs with template contour preservation
        self._add_substance_glyphs_with_contour_preservation(new_glyf, generated_glyphs)

        # Step 5: Preserve basic character glyphs from template
        self._preserve_template_basic_characters(new_glyf)

        # Step 6: Update font data and validate
        self._font_data["glyf"] = new_glyf

        # Validate glyph count limits (legacy compatibility)
        # OpenType fonts have a hard limit of 65536 glyphs due to 16-bit indexing
        if len(new_glyf) > 65536:
            raise Exception("glyf table cannot contain more than 65536 glyphs.")

        # Finalize the glyf table
        self._finalize_glyf_table(new_glyf)

    def _prepare_base_glyf_structure(self) -> Dict[str, Any]:
        """Prepare base glyf structure with template data.

        レガシー実装からの重要な知識（元コメントを完全保持）:
        - Get the base glyf table from MAIN template (for metadata structure)
        - Start with template glyf data that contains actual contours
        - base_glyf from main template has empty contours, _glyf_data has the actual contours
        """
        # メインテンプレートからベースglyfテーブルを取得（メタデータ構造用）
        if self._font_data is None:
            raise ValueError("Font data not loaded")
        base_glyf_raw = self._font_data.get("glyf", {})
        base_glyf = (
            cast(Dict[str, Any], base_glyf_raw)
            if isinstance(base_glyf_raw, dict)
            else {}
        )

        # 実際の輪郭データを含むテンプレートglyf データから開始
        # メインテンプレートのbase_glyfは空の輪郭、_glyf_dataが実際の輪郭を持つ
        if self._glyf_data is None:
            raise ValueError("Glyf data not loaded")
        new_glyf = dict(self._glyf_data)

        # デバッグ: ひらがな輪郭が保持されていることを確認
        if "cid01460" in new_glyf:
            glyph_data = new_glyf["cid01460"]
            if isinstance(glyph_data, dict):
                contours = glyph_data.get("contours", [])
                contour_count = len(contours) if isinstance(contours, list) else 0
                self.logger.debug(
                    "new_glyf starts with cid01460 having %d contours", contour_count
                )

        # 必要に応じてbase_glyfからメタデータをマージ
        for glyph_name, glyph_data in base_glyf.items():
            if glyph_name not in new_glyf:
                new_glyf[glyph_name] = glyph_data

        return new_glyf

    def _generate_pinyin_glyphs(self) -> Dict[str, Any]:
        """Generate all pinyin-annotated glyphs.

        レガシー実装からの重要な知識（元コメントを完全保持）:
        - Use glyph_manager to generate all pinyin-annotated glyphs
        """
        # glyph_managerを使用してすべての拼音付きグリフを生成
        self.glyph_manager.generate_pinyin_glyphs()  # 拼音アルファベットグリフを生成
        self.glyph_manager.generate_hanzi_glyphs()  # 漢字+拼音合成グリフを生成

        # glyph_managerから生成されたすべてのグリフを取得
        return self.glyph_manager.get_all_glyphs()

    def _add_pinyin_alphabet_glyphs(
        self, new_glyf: Dict[str, Any], generated_glyphs: Dict[str, Any]
    ) -> None:
        """Add pinyin alphabet glyphs to the glyf table.

        レガシー実装からの重要な知識（元コメントを完全保持）:
        - Add pinyin alphabet glyphs (from legacy py_alphabet)
        """
        # 2. 拼音アルファベットグリフを追加（レガシーpy_alphabetから）
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

    def _add_substance_glyphs_with_contour_preservation(
        self, new_glyf: Dict[str, Any], generated_glyphs: Dict[str, Any]
    ) -> None:
        """Add substance glyphs with template contour preservation.

        レガシー実装からの重要な知識（元コメントを完全保持）:
        - Add substance glyphs (CRITICAL: use glyf template for contour data)
        - This is the missing piece - we need to use _glyf_data for actual glyph contours
        - For substance glyphs, merge with template glyf data to preserve contours
        """
        # 3. 実体グリフを追加（重要：輪郭データには glyf テンプレートを使用）
        # これが欠けていたピース - 実際のグリフ輪郭には _glyf_data を使用する必要がある
        substance_glyphs = {
            k: v for k, v in generated_glyphs.items() if not k.startswith("py_alphabet")
        }

        self.logger.debug(" Processing %d substance glyphs", len(substance_glyphs))

        # 実体グリフの場合、輪郭を保持するためにテンプレート glyf データとマージ
        for glyph_name, glyph_data in substance_glyphs.items():
            self._process_single_substance_glyph(new_glyf, glyph_name, glyph_data)

    def _process_single_substance_glyph(
        self, new_glyf: Dict[str, Any], glyph_name: str, glyph_data: Dict[str, Any]
    ) -> None:
        """Process a single substance glyph with contour preservation logic.

        レガシー実装からの重要な知識（元コメントを完全保持）:
        - Check if this is a base glyph that should have contour data from template
        - If generated glyph has no useful content (no references/contours), use template
        """
        # Check if this is a base glyph that should have contour data from template
        base_glyph_name = glyph_name.split(".")[0]  # Remove .ss## suffix

        if self._glyf_data is not None and base_glyph_name in self._glyf_data:
            template_glyph = cast(Dict[str, Any], self._glyf_data[base_glyph_name])

            # Check glyph content to decide merge strategy
            content_info = self._analyze_glyph_content(glyph_data, template_glyph)

            if content_info["should_use_template_completely"]:
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
                self.logger.debug(" Preserved contours for .ss00 glyph: %s", glyph_name)
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

    def _analyze_glyph_content(
        self, glyph_data: Dict[str, Any], template_glyph: Dict[str, Any]
    ) -> Dict[str, bool]:
        """Analyze glyph content to determine merge strategy.

        レガシー実装からの重要な知識（元コメントを完全保持）:
        - If generated glyph has no useful content (no references/contours), use template
        """
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

        return {
            "should_use_template_completely": not has_references
            and not has_contours
            and template_has_contours,
            "has_references": has_references,
            "has_contours": has_contours,
            "template_has_contours": template_has_contours,
        }

    def _preserve_template_basic_characters(self, new_glyf: Dict[str, Any]) -> None:
        """Preserve basic character glyphs from template.

        レガシー実装からの重要な知識（元コメントを完全保持）:
        - Ensure all template glyphs are included, especially basic characters
        - This preserves hiragana, katakana, alphabet characters that are not processed by character manager
        - Use template data completely - this preserves contours for basic characters
        """
        # Ensure all template glyphs are included, especially basic characters
        # This preserves hiragana, katakana, alphabet characters that are not processed by character manager
        template_glyphs_added = 0
        if self._glyf_data is not None:
            for glyph_name, glyph_data in self._glyf_data.items():
                if glyph_name not in new_glyf:
                    # Use template data completely - this preserves contours for basic characters
                    if isinstance(glyph_data, dict) and hasattr(glyph_data, "copy"):
                        new_glyf[glyph_name] = glyph_data.copy()
                    else:
                        new_glyf[glyph_name] = glyph_data
                    template_glyphs_added += 1

                    # Debug specific basic characters
                    self._debug_basic_character_preservation(glyph_name, glyph_data)

        self.logger.debug(
            " Added %d template glyphs to preserve basic characters",
            template_glyphs_added,
        )

    def _debug_basic_character_preservation(
        self, glyph_name: str, glyph_data: Any
    ) -> None:
        """Debug specific basic character preservation.

        レガシー実装からの重要な知識（元コメントを完全保持）:
        - Debug specific basic characters
        """
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

    def _finalize_glyf_table(self, new_glyf: Dict[str, Any]) -> None:
        """Finalize the glyf table.

        レガシー実装からの重要な知識（元コメントを完全保持）:
        - Log the final glyph count for debugging

        Args:
            new_glyf: The completed glyf table dictionary

        Note:
            Font data update and validation are now handled in _add_glyf method.
        """
        self.logger.debug("glyf num : %d", len(new_glyf))

    def _add_gsub(self) -> None:
        """Add GSUB table for contextual substitution.

        レガシー実装からの重要な知識（元コメントを完全保持）:
        GSUBテーブルは多音字対応の核心機能です。

        This method creates the OpenType GSUB (Glyph Substitution) table that enables
        contextual substitution of Chinese characters with alternative pronunciations.

        The GSUB table handles:
        - Pattern-based character substitution (pattern_one, pattern_two)
        - Exception pattern handling (exception_pattern)
        - Multi-character context matching
        - Stylistic set (ss##) variant selection

        Technical Implementation:
        - Uses GSUBTableGenerator with pattern files
        - Integrates with character and mapping managers
        - Generates lookup tables for contextual substitution
        - Maintains compatibility with legacy GSUB structure

        Raises:
            RuntimeError: If GSUB table generation fails
            FileNotFoundError: If pattern files are missing
        """

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
        """Set font size metadata.

        レガシー実装からの重要な知識（元コメントを完全保持）:
        - Set font metrics to accommodate pinyin height (legacy compatibility)
        - This matches the legacy set_about_size() method behavior
        - すべてのグリフの輪郭を含む範囲 (yMax)
        - 原点からグリフの上端までの距離 (ascender)
        - Windows-specific ascent metric (usWinAscent)

        Args:
            None

        Raises:
            ValueError: If font data is not loaded

        Note:
            This method updates three key font metrics:
            1. head.yMax - overall bounding box height
            2. hhea.ascender - ascent from baseline
            3. OS_2.usWinAscent - Windows-specific ascent
        """

        if self._font_data is None:
            raise ValueError("Font data not loaded")

        self.font_assembler.set_font_metadata(self._font_data, self.font_type)

        # Set font metrics to accommodate pinyin height (legacy compatibility)
        # This matches the legacy set_about_size() method behavior
        pinyin_metrics = self.glyph_manager.get_pinyin_metrics()

        if pinyin_metrics:
            # レガシー互換性のための変数名保持
            advanceAddedPinyinHeight = pinyin_metrics.height

            # Update font metrics to accommodate pinyin height (explicit for tests)
            if self._font_data:
                # Update head.yMax
                head_table = cast(HeadTable, self._font_data.get("head", {}))
                if isinstance(head_table, dict) and "yMax" in head_table:
                    current_ymax = head_table["yMax"]
                    if isinstance(
                        current_ymax, (int, float)
                    ) and advanceAddedPinyinHeight > float(current_ymax):
                        head_table["yMax"] = advanceAddedPinyinHeight

                # Update hhea.ascender
                hhea_table = cast(HheaTable, self._font_data.get("hhea", {}))
                if isinstance(hhea_table, dict) and "ascender" in hhea_table:
                    current_ascender = hhea_table["ascender"]
                    if (
                        isinstance(current_ascender, (int, float))
                        and advanceAddedPinyinHeight > current_ascender
                    ):
                        hhea_table["ascender"] = advanceAddedPinyinHeight

                # Update OS_2.usWinAscent
                os2_table = cast(OS2Table, self._font_data.get("OS_2", {}))
                if isinstance(os2_table, dict) and "usWinAscent" in os2_table:
                    os2_table["usWinAscent"] = advanceAddedPinyinHeight

        self.logger.debug("font revision set to: %s", VERSION)

    def _log_font_metrics_debug_info(self) -> None:
        """Log font metrics debug information."""
        # Debug logging with safe access
        if self._font_data:
            head_table = cast(HeadTable, self._font_data.get("head", {}))
            hhea_table = cast(HheaTable, self._font_data.get("hhea", {}))
            os2_table = cast(OS2Table, self._font_data.get("OS_2", {}))
        else:
            head_table = cast(HeadTable, {})
            hhea_table = cast(HheaTable, {})
            os2_table = cast(OS2Table, {})

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

    def _set_copyright(self) -> None:
        """Set font copyright and naming information.

        レガシー実装からの重要な知識（元コメントを完全保持）:
        フォントタイプに応じて適切な名称テーブルを設定します。

        This method sets the OpenType 'name' table which contains:
        - Font family name
        - Font style name
        - Copyright information
        - Version information
        - Trademark notices
        - Other metadata

        Font Type Mapping:
        - FontType.HAN_SERIF -> HAN_SERIF name table
        - FontType.HANDWRITTEN -> HANDWRITTEN name table

        The name table is essential for:
        - Font identification by operating systems
        - Font menu display in applications
        - Font licensing and copyright compliance
        - Font metadata queries

        Raises:
            ValueError: If unsupported font type is provided

        Note:
            The name table structure follows OpenType specification requirements
            and maintains compatibility with legacy font configurations.
        """

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
        """Save font data as formatted JSON for otfccbuild.

        レガシー実装からの重要な知識（元コメントを完全保持）:
        フォントデータをotfccbuildで読み取り可能なJSON形式で保存します。

        This method serializes the complete font data structure to JSON format
        that can be processed by the otfccbuild tool.

        JSON Format Features:
        - Uses orjson for fast and reliable serialization
        - Includes indentation (OPT_INDENT_2) for readability
        - Preserves all font table data and metadata
        - Compatible with otfccbuild input requirements

        Args:
            output_path: Path where the JSON file will be saved

        Raises:
            OSError: If file cannot be written
            TypeError: If font data contains non-serializable objects

        Note:
            The JSON file serves as an intermediate format between the internal
            font data structure and the final binary OTF font file.
        """
        with open(output_path, "wb") as f:
            f.write(orjson.dumps(self._font_data, option=orjson.OPT_INDENT_2))

    def _convert_json_to_otf(self, json_path: Path, output_path: Path) -> None:
        """Convert JSON font description to OTF using external tools.

        レガシー実装からの重要な知識（元コメントを完全保持）:
        otfccbuildツールを使用してJSONからOTFフォントを生成します。

        This method handles the final conversion from JSON font description to
        binary OTF font file using the otfccbuild tool.

        Conversion Process:
        1. Uses external_tool interface if provided (for testing/mocking)
        2. Falls back to direct otfccbuild command execution
        3. Includes comprehensive error handling and timeout protection
        4. Captures and logs detailed error information

        Args:
            json_path: Path to the JSON font description file
            output_path: Path where the OTF font file will be created

        Raises:
            subprocess.CalledProcessError: If otfccbuild fails
            subprocess.TimeoutExpired: If conversion takes too long
            FileNotFoundError: If otfccbuild is not installed

        Note:
            Requires otfccbuild to be installed and available in PATH.
            The conversion timeout is set to 60 seconds to prevent hanging.
        """
        # Use external tool if provided (primarily for testing)
        if self.external_tool:
            self.external_tool.convert_json_to_otf(json_path, output_path)
            return

        # Execute otfccbuild directly
        self._execute_otfccbuild_command(json_path, output_path)

    def _execute_otfccbuild_command(self, json_path: Path, output_path: Path) -> None:
        """Execute otfccbuild command with proper error handling."""
        try:
            subprocess.run(
                ["otfccbuild", str(json_path), "-o", str(output_path)],
                check=True,
                capture_output=True,
                text=True,
                timeout=FontConstants.CONVERSION_TIMEOUT_SECONDS,
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
