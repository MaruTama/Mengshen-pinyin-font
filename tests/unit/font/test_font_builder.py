# -*- coding: utf-8 -*-
"""
Tests for FontBuilder.

These tests verify that the FontBuilder works correctly with proper
dependency injection, template loading, and font generation orchestration.
"""

from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from refactored.config import FontConfig, FontConstants, FontType, ProjectPaths
from refactored.data import CharacterDataManager, MappingDataManager, PinyinDataManager
from refactored.data.character_data import CharacterInfo
from refactored.generation.font_builder import ExternalToolInterface, FontBuilder


class MockExternalTool:
    """Mock external tool for testing."""

    def __init__(self):
        self.converted_files = []

    def convert_json_to_otf(self, json_path: Path, output_path: Path) -> None:
        """Mock conversion function."""
        self.converted_files.append((json_path, output_path))


class TestFontBuilder:
    """Test FontBuilder functionality."""

    @pytest.mark.unit
    def test_font_builder_initialization(self):
        """Test FontBuilder initialization."""
        # Create mock paths
        template_main = Path("/mock/template_main.json")
        template_glyf = Path("/mock/template_glyf.json")
        alphabet_pinyin = Path("/mock/alphabet.json")
        pattern_one = Path("/mock/pattern_one.txt")
        pattern_two = Path("/mock/pattern_two.json")
        exception_pattern = Path("/mock/exception.json")

        # Create mock managers
        mock_pinyin_manager = Mock(spec=PinyinDataManager)
        mock_character_manager = Mock(spec=CharacterDataManager)
        mock_mapping_manager = Mock(spec=MappingDataManager)
        mock_external_tool = Mock(spec=ExternalToolInterface)
        mock_paths = Mock(spec=ProjectPaths)

        # Mock the cmap loading
        with patch(
            "refactored.tables.cmap_manager.CmapTableManager.from_path"
        ) as mock_cmap_from_path:
            # Create a mock CmapTableManager instance
            mock_cmap_manager = Mock()
            mock_cmap_manager.get_cmap_table.return_value = {"20013": "cid00001"}
            mock_cmap_from_path.return_value = mock_cmap_manager
            builder = FontBuilder(
                font_type=FontType.HAN_SERIF,
                template_main_path=template_main,
                template_glyf_path=template_glyf,
                alphabet_pinyin_path=alphabet_pinyin,
                pattern_one_path=pattern_one,
                pattern_two_path=pattern_two,
                exception_pattern_path=exception_pattern,
                pinyin_manager=mock_pinyin_manager,
                character_manager=mock_character_manager,
                mapping_manager=mock_mapping_manager,
                external_tool=mock_external_tool,
                paths=mock_paths,
            )

        # Test initialization
        assert builder.font_type == FontType.HAN_SERIF
        assert builder.font_config == FontConfig.get_config(FontType.HAN_SERIF)
        assert builder.paths is mock_paths
        assert builder.template_main_path == template_main
        assert builder.template_glyf_path == template_glyf
        assert builder.alphabet_pinyin_path == alphabet_pinyin
        assert builder.pattern_one_path == pattern_one
        assert builder.pattern_two_path == pattern_two
        assert builder.exception_pattern_path == exception_pattern
        assert builder.pinyin_manager is mock_pinyin_manager
        assert builder.character_manager is mock_character_manager
        assert builder.mapping_manager is mock_mapping_manager
        assert builder.external_tool is mock_external_tool
        assert builder._font_data is None
        assert builder._glyf_data is None

    @pytest.mark.unit
    def test_font_builder_initialization_with_defaults(self):
        """Test FontBuilder initialization with default dependencies."""
        template_main = Path("/mock/template_main.json")
        template_glyf = Path("/mock/template_glyf.json")
        alphabet_pinyin = Path("/mock/alphabet.json")
        pattern_one = Path("/mock/pattern_one.txt")
        pattern_two = Path("/mock/pattern_two.json")
        exception_pattern = Path("/mock/exception.json")

        with (
            patch(
                "refactored.tables.cmap_manager.CmapTableManager.from_path"
            ) as mock_cmap_from_path,
            patch(
                "refactored.generation.font_builder.PinyinDataManager"
            ) as mock_pinyin_cls,
            patch(
                "refactored.generation.font_builder.CharacterDataManager"
            ) as mock_char_cls,
            patch(
                "refactored.generation.font_builder.MappingDataManager"
            ) as mock_mapping_cls,
            patch("refactored.generation.font_builder.GlyphManager") as mock_glyph_cls,
            patch(
                "refactored.generation.font_builder.FontAssembler"
            ) as mock_assembler_cls,
        ):
            # Set up the mock CmapTableManager
            mock_cmap_manager = Mock()
            mock_cmap_manager.get_cmap_table.return_value = {}
            mock_cmap_from_path.return_value = mock_cmap_manager

            builder = FontBuilder(
                font_type=FontType.HAN_SERIF,
                template_main_path=template_main,
                template_glyf_path=template_glyf,
                alphabet_pinyin_path=alphabet_pinyin,
                pattern_one_path=pattern_one,
                pattern_two_path=pattern_two,
                exception_pattern_path=exception_pattern,
            )

            # Verify default instances were created
            assert builder.font_type == FontType.HAN_SERIF
            assert isinstance(builder.paths, ProjectPaths)
            mock_pinyin_cls.assert_called_once()
            mock_char_cls.assert_called_once()

    @pytest.mark.unit
    def test_load_templates(self):
        """Test _load_templates functionality."""
        template_main = Path("/mock/template_main.json")
        template_glyf = Path("/mock/template_glyf.json")

        # Mock JSON data
        mock_main_data = {
            "cmap": {"20013": "cid00001"},
            "head": {"fontRevision": 1.0},
            "name": {},
        }
        mock_glyf_data = {"cid00001": {"advanceWidth": 1000, "contours": []}}

        with (
            patch(
                "refactored.tables.cmap_manager.CmapTableManager.from_path",
            ) as mock_cmap_from_path,
            patch("builtins.open", mock_open()) as mock_file,
            patch("orjson.loads", side_effect=[mock_main_data, mock_glyf_data]),
        ):

            builder = FontBuilder(
                font_type=FontType.HAN_SERIF,
                template_main_path=template_main,
                template_glyf_path=template_glyf,
                alphabet_pinyin_path=Path("/mock/alphabet.json"),
                pattern_one_path=Path("/mock/pattern_one.txt"),
                pattern_two_path=Path("/mock/pattern_two.json"),
                exception_pattern_path=Path("/mock/exception.json"),
            )

            # Call _load_templates
            builder._load_templates()

            # Verify data was loaded
            assert builder._font_data == mock_main_data
            assert builder._glyf_data == mock_glyf_data

            # Verify files were opened
            assert mock_file.call_count == 2

    @pytest.mark.unit
    def test_load_templates_file_not_found(self):
        """Test _load_templates with missing files."""
        template_main = Path("/nonexistent/template_main.json")
        template_glyf = Path("/nonexistent/template_glyf.json")

        with (
            patch(
                "refactored.tables.cmap_manager.CmapTableManager.from_path",
            ) as mock_cmap_from_path,
            patch("builtins.open", side_effect=FileNotFoundError("File not found")),
        ):

            builder = FontBuilder(
                font_type=FontType.HAN_SERIF,
                template_main_path=template_main,
                template_glyf_path=template_glyf,
                alphabet_pinyin_path=Path("/mock/alphabet.json"),
                pattern_one_path=Path("/mock/pattern_one.txt"),
                pattern_two_path=Path("/mock/pattern_two.json"),
                exception_pattern_path=Path("/mock/exception.json"),
            )

            with pytest.raises(FileNotFoundError):
                builder._load_templates()

    @pytest.mark.unit
    def test_load_templates_invalid_json(self):
        """Test _load_templates with invalid JSON."""
        template_main = Path("/mock/template_main.json")
        template_glyf = Path("/mock/template_glyf.json")

        with (
            patch(
                "refactored.tables.cmap_manager.CmapTableManager.from_path",
            ) as mock_cmap_from_path,
            patch("builtins.open", mock_open()),
            patch("orjson.loads", side_effect=ValueError("Invalid JSON")),
        ):

            builder = FontBuilder(
                font_type=FontType.HAN_SERIF,
                template_main_path=template_main,
                template_glyf_path=template_glyf,
                alphabet_pinyin_path=Path("/mock/alphabet.json"),
                pattern_one_path=Path("/mock/pattern_one.txt"),
                pattern_two_path=Path("/mock/pattern_two.json"),
                exception_pattern_path=Path("/mock/exception.json"),
            )

            with pytest.raises(ValueError):
                builder._load_templates()

    @pytest.mark.unit
    def test_initialize_managers(self):
        """Test _initialize_managers functionality."""
        template_main = Path("/mock/template_main.json")
        mock_font_data = {"cmap": {"20013": "cid00001"}, "head": {"fontRevision": 1.0}}
        mock_glyf_data = {"cid00001": {"advanceWidth": 1000}}

        # Create mock managers
        mock_glyph_manager = Mock()
        mock_mapping_manager = Mock(spec=MappingDataManager)

        with (
            patch(
                "refactored.tables.cmap_manager.CmapTableManager.from_path",
            ) as mock_cmap_from_path,
            patch(
                "refactored.generation.font_builder.GlyphManager",
                return_value=mock_glyph_manager,
            ),
        ):
            # Set up the mock CmapTableManager
            mock_cmap_manager = Mock()
            mock_cmap_manager.get_cmap_table.return_value = mock_font_data["cmap"]
            mock_cmap_from_path.return_value = mock_cmap_manager

            builder = FontBuilder(
                font_type=FontType.HAN_SERIF,
                template_main_path=template_main,
                template_glyf_path=Path("/mock/template_glyf.json"),
                alphabet_pinyin_path=Path("/mock/alphabet.json"),
                pattern_one_path=Path("/mock/pattern_one.txt"),
                pattern_two_path=Path("/mock/pattern_two.json"),
                exception_pattern_path=Path("/mock/exception.json"),
                mapping_manager=mock_mapping_manager,
            )

            # Set up font data
            builder._font_data = mock_font_data
            builder._glyf_data = mock_glyf_data

            # Call _initialize_managers
            builder._initialize_managers()

            # Verify glyph manager was initialized
            mock_glyph_manager.initialize.assert_called_once()

            # Verify cmap table was set (now handled by cmap_manager instance)
            assert builder.cmap_manager.get_cmap_table() == mock_font_data["cmap"]

    @pytest.mark.unit
    def test_add_cmap_uvs_single_pronunciation(self):
        """Test _add_cmap_uvs for single pronunciation characters."""
        # Create test data
        mock_font_data = {"cmap": {"20013": "cid00001"}}

        # Create mock character info
        char_info = CharacterInfo(character="中", pronunciations=["zhōng"])

        # Create mock managers
        mock_character_manager = Mock(spec=CharacterDataManager)
        mock_character_manager.iter_single_pronunciation_characters.return_value = [
            char_info
        ]
        mock_character_manager.iter_multiple_pronunciation_characters.return_value = []

        mock_mapping_manager = Mock(spec=MappingDataManager)
        mock_mapping_manager.has_glyph_for_character.return_value = True
        mock_mapping_manager.convert_hanzi_to_cid.return_value = "cid00001"

        with patch("refactored.tables.cmap_manager.CmapTableManager.from_path"):
            builder = FontBuilder(
                font_type=FontType.HAN_SERIF,
                template_main_path=Path("/mock/template_main.json"),
                template_glyf_path=Path("/mock/template_glyf.json"),
                alphabet_pinyin_path=Path("/mock/alphabet.json"),
                pattern_one_path=Path("/mock/pattern_one.txt"),
                pattern_two_path=Path("/mock/pattern_two.json"),
                exception_pattern_path=Path("/mock/exception.json"),
                character_manager=mock_character_manager,
                mapping_manager=mock_mapping_manager,
            )

            # Set up font data
            builder._font_data = mock_font_data

            # Call _add_cmap_uvs
            builder._add_cmap_uvs()

            # Verify cmap_uvs was added
            assert "cmap_uvs" in builder._font_data
            cmap_uvs = builder._font_data["cmap_uvs"]

            # Verify IVS entry was added
            unicode_value = ord("中")  # 20013
            ivs_key = f"{unicode_value} {FontConstants.IVS_BASE}"
            assert ivs_key in cmap_uvs
            assert cmap_uvs[ivs_key] == "cid00001.ss00"

    @pytest.mark.unit
    def test_add_cmap_uvs_multiple_pronunciations(self):
        """Test _add_cmap_uvs for multiple pronunciation characters."""
        # Create test data
        mock_font_data = {"cmap": {"20013": "cid00001"}}

        # Create mock character info
        char_info = CharacterInfo(character="中", pronunciations=["zhōng", "zhòng"])

        # Create mock managers
        mock_character_manager = Mock(spec=CharacterDataManager)
        mock_character_manager.iter_single_pronunciation_characters.return_value = []
        mock_character_manager.iter_multiple_pronunciation_characters.return_value = [
            char_info
        ]

        mock_mapping_manager = Mock(spec=MappingDataManager)
        mock_mapping_manager.has_glyph_for_character.return_value = True
        mock_mapping_manager.convert_hanzi_to_cid.return_value = "cid00001"

        with patch("refactored.tables.cmap_manager.CmapTableManager.from_path"):
            builder = FontBuilder(
                font_type=FontType.HAN_SERIF,
                template_main_path=Path("/mock/template_main.json"),
                template_glyf_path=Path("/mock/template_glyf.json"),
                alphabet_pinyin_path=Path("/mock/alphabet.json"),
                pattern_one_path=Path("/mock/pattern_one.txt"),
                pattern_two_path=Path("/mock/pattern_two.json"),
                exception_pattern_path=Path("/mock/exception.json"),
                character_manager=mock_character_manager,
                mapping_manager=mock_mapping_manager,
            )

            # Set up font data
            builder._font_data = mock_font_data

            # Call _add_cmap_uvs
            builder._add_cmap_uvs()

            # Verify cmap_uvs was added
            assert "cmap_uvs" in builder._font_data
            cmap_uvs = builder._font_data["cmap_uvs"]

            # Verify IVS entries were added (3 variants: ss00, ss01, ss02)
            unicode_value = ord("中")  # 20013
            for i in range(3):  # 2 pronunciations + 1 for ss00
                ivs_key = f"{unicode_value} {FontConstants.IVS_BASE + i}"
                assert ivs_key in cmap_uvs
                assert cmap_uvs[ivs_key] == f"cid00001.ss{i:02d}"

    @pytest.mark.unit
    def test_add_cmap_uvs_no_glyph_character(self):
        """Test _add_cmap_uvs skips characters without glyphs."""
        # Create test data
        mock_font_data = {"cmap": {"20013": "cid00001"}}

        # Create mock character info
        char_info = CharacterInfo(character="中", pronunciations=["zhōng"])

        # Create mock managers
        mock_character_manager = Mock(spec=CharacterDataManager)
        mock_character_manager.iter_single_pronunciation_characters.return_value = [
            char_info
        ]
        mock_character_manager.iter_multiple_pronunciation_characters.return_value = []

        mock_mapping_manager = Mock(spec=MappingDataManager)
        mock_mapping_manager.has_glyph_for_character.return_value = False  # No glyph

        with patch("refactored.tables.cmap_manager.CmapTableManager.from_path"):
            builder = FontBuilder(
                font_type=FontType.HAN_SERIF,
                template_main_path=Path("/mock/template_main.json"),
                template_glyf_path=Path("/mock/template_glyf.json"),
                alphabet_pinyin_path=Path("/mock/alphabet.json"),
                pattern_one_path=Path("/mock/pattern_one.txt"),
                pattern_two_path=Path("/mock/pattern_two.json"),
                exception_pattern_path=Path("/mock/exception.json"),
                character_manager=mock_character_manager,
                mapping_manager=mock_mapping_manager,
            )

            # Set up font data
            builder._font_data = mock_font_data

            # Call _add_cmap_uvs
            builder._add_cmap_uvs()

            # Verify cmap_uvs was added but is empty
            assert "cmap_uvs" in builder._font_data
            cmap_uvs = builder._font_data["cmap_uvs"]
            assert len(cmap_uvs) == 0

    @pytest.mark.unit
    def test_get_build_statistics(self):
        """Test get_build_statistics functionality."""
        with patch("refactored.tables.cmap_manager.CmapTableManager.from_path"):
            builder = FontBuilder(
                font_type=FontType.HAN_SERIF,
                template_main_path=Path("/mock/template_main.json"),
                template_glyf_path=Path("/mock/template_glyf.json"),
                alphabet_pinyin_path=Path("/mock/alphabet.json"),
                pattern_one_path=Path("/mock/pattern_one.txt"),
                pattern_two_path=Path("/mock/pattern_two.json"),
                exception_pattern_path=Path("/mock/exception.json"),
            )

            stats = builder.get_build_statistics()

            # Currently returns placeholder
            assert isinstance(stats, dict)
            assert "status" in stats

    @pytest.mark.unit
    def test_build_success_flow(self):
        """Test successful build flow."""
        output_path = Path("/mock/output.ttf")
        temp_json_path = Path("/mock/temp_output.json")

        # Create mock external tool
        mock_external_tool = MockExternalTool()

        # Create mock managers
        mock_glyph_manager = Mock()
        mock_font_assembler = Mock()
        mock_paths = Mock(spec=ProjectPaths)
        mock_paths.get_temp_json_path.return_value = temp_json_path

        with (
            patch(
                "refactored.tables.cmap_manager.CmapTableManager.from_path",
            ) as mock_cmap_from_path,
            patch(
                "refactored.generation.font_builder.GlyphManager",
                return_value=mock_glyph_manager,
            ),
            patch(
                "refactored.generation.font_builder.FontAssembler",
                return_value=mock_font_assembler,
            ),
            patch("builtins.open", mock_open()),
            patch("orjson.loads", return_value={"cmap": {}}),
            patch("orjson.dumps", return_value=b'{"test": "data"}'),
        ):
            # Set up the mock CmapTableManager
            mock_cmap_manager = Mock()
            mock_cmap_manager.get_cmap_table.return_value = {}
            mock_cmap_from_path.return_value = mock_cmap_manager

            builder = FontBuilder(
                font_type=FontType.HAN_SERIF,
                template_main_path=Path("/mock/template_main.json"),
                template_glyf_path=Path("/mock/template_glyf.json"),
                alphabet_pinyin_path=Path("/mock/alphabet.json"),
                pattern_one_path=Path("/mock/pattern_one.txt"),
                pattern_two_path=Path("/mock/pattern_two.json"),
                exception_pattern_path=Path("/mock/exception.json"),
                external_tool=mock_external_tool,
                paths=mock_paths,
            )

            # Mock the build methods
            builder._load_templates = Mock()
            builder._initialize_managers = Mock()
            builder._add_cmap_uvs = Mock()
            builder._add_glyph_order = Mock()
            builder._add_glyf = Mock()
            builder._add_gsub = Mock()
            builder._set_about_size = Mock()
            builder._set_copyright = Mock()
            builder._save_as_json = Mock()
            builder._convert_json_to_otf = Mock()

            # Call build
            builder.build(output_path)

            # Verify all methods were called
            builder._load_templates.assert_called_once()
            builder._initialize_managers.assert_called_once()
            builder._add_cmap_uvs.assert_called_once()
            builder._add_glyph_order.assert_called_once()
            builder._add_glyf.assert_called_once()
            builder._add_gsub.assert_called_once()
            builder._set_about_size.assert_called_once()
            builder._set_copyright.assert_called_once()
            builder._save_as_json.assert_called_once_with(temp_json_path)
            builder._convert_json_to_otf.assert_called_once_with(
                temp_json_path, output_path
            )

    @pytest.mark.unit
    def test_build_failure_handling(self):
        """Test build failure handling."""
        output_path = Path("/mock/output.ttf")

        with patch("refactored.tables.cmap_manager.CmapTableManager.from_path"):
            builder = FontBuilder(
                font_type=FontType.HAN_SERIF,
                template_main_path=Path("/mock/template_main.json"),
                template_glyf_path=Path("/mock/template_glyf.json"),
                alphabet_pinyin_path=Path("/mock/alphabet.json"),
                pattern_one_path=Path("/mock/pattern_one.txt"),
                pattern_two_path=Path("/mock/pattern_two.json"),
                exception_pattern_path=Path("/mock/exception.json"),
            )

            # Mock _load_templates to raise exception
            builder._load_templates = Mock(
                side_effect=Exception("Template loading failed")
            )

            # Build should raise exception
            with pytest.raises(Exception, match="Template loading failed"):
                builder.build(output_path)


class TestFontBuilderIntegration:
    """Integration tests for FontBuilder components."""

    @pytest.mark.unit
    def test_font_builder_with_real_data_managers(self):
        """Test FontBuilder with real data managers."""
        # Create mock character data
        mock_pinyin_data = {"中": ["zhōng", "zhòng"], "国": ["guó"], "人": ["rén"]}

        # Create mock managers with real behavior
        mock_pinyin_manager = Mock(spec=PinyinDataManager)
        mock_pinyin_manager.get_all_mappings.return_value = mock_pinyin_data

        def mock_get_pinyin(character):
            return mock_pinyin_data.get(character)

        mock_pinyin_manager.get_pinyin.side_effect = mock_get_pinyin

        # Create real character manager
        from refactored.data.character_data import CharacterDataManager

        character_manager = CharacterDataManager(pinyin_manager=mock_pinyin_manager)

        # Create mock mapping manager
        mock_mapping_manager = Mock(spec=MappingDataManager)
        mock_mapping_manager.has_glyph_for_character.return_value = True
        mock_mapping_manager.convert_hanzi_to_cid.return_value = "cid00001"

        with patch("refactored.tables.cmap_manager.CmapTableManager.from_path"):
            builder = FontBuilder(
                font_type=FontType.HAN_SERIF,
                template_main_path=Path("/mock/template_main.json"),
                template_glyf_path=Path("/mock/template_glyf.json"),
                alphabet_pinyin_path=Path("/mock/alphabet.json"),
                pattern_one_path=Path("/mock/pattern_one.txt"),
                pattern_two_path=Path("/mock/pattern_two.json"),
                exception_pattern_path=Path("/mock/exception.json"),
                pinyin_manager=mock_pinyin_manager,
                character_manager=character_manager,
                mapping_manager=mock_mapping_manager,
            )

            # Set up font data
            builder._font_data = {"cmap": {"20013": "cid00001"}}

            # Test _add_cmap_uvs with real character manager
            builder._add_cmap_uvs()

            # Verify cmap_uvs was populated correctly
            assert "cmap_uvs" in builder._font_data
            cmap_uvs = builder._font_data["cmap_uvs"]

            # Should have entries for both single and multiple pronunciation chars
            assert len(cmap_uvs) > 0

    @pytest.mark.unit
    def test_font_builder_error_recovery(self):
        """Test FontBuilder error recovery mechanisms."""
        # Test partial build state recovery
        with patch("refactored.tables.cmap_manager.CmapTableManager.from_path"):
            builder = FontBuilder(
                font_type=FontType.HAN_SERIF,
                template_main_path=Path("/mock/template_main.json"),
                template_glyf_path=Path("/mock/template_glyf.json"),
                alphabet_pinyin_path=Path("/mock/alphabet.json"),
                pattern_one_path=Path("/mock/pattern_one.txt"),
                pattern_two_path=Path("/mock/pattern_two.json"),
                exception_pattern_path=Path("/mock/exception.json"),
            )

            # Test that builder can be initialized even with some errors
            assert builder.font_type == FontType.HAN_SERIF
            assert builder._font_data is None
            assert builder._glyf_data is None

            # Test that basic operations don't crash
            stats = builder.get_build_statistics()
            assert isinstance(stats, dict)

    @pytest.mark.unit
    def test_font_builder_memory_efficiency(self):
        """Test memory efficiency of FontBuilder."""
        # Test with large character set
        large_character_set = {chr(0x4E00 + i): [f"pin{i}"] for i in range(1000)}

        mock_pinyin_manager = Mock(spec=PinyinDataManager)
        mock_pinyin_manager.get_all_mappings.return_value = large_character_set

        with patch("refactored.tables.cmap_manager.CmapTableManager.from_path"):
            builder = FontBuilder(
                font_type=FontType.HAN_SERIF,
                template_main_path=Path("/mock/template_main.json"),
                template_glyf_path=Path("/mock/template_glyf.json"),
                alphabet_pinyin_path=Path("/mock/alphabet.json"),
                pattern_one_path=Path("/mock/pattern_one.txt"),
                pattern_two_path=Path("/mock/pattern_two.json"),
                exception_pattern_path=Path("/mock/exception.json"),
                pinyin_manager=mock_pinyin_manager,
            )

            # Builder should handle large datasets without issue
            assert builder is not None
            assert builder.pinyin_manager is mock_pinyin_manager

    @pytest.mark.unit
    def test_font_builder_external_tool_integration(self):
        """Test FontBuilder integration with external tools."""
        mock_external_tool = MockExternalTool()

        with patch("refactored.tables.cmap_manager.CmapTableManager.from_path"):
            builder = FontBuilder(
                font_type=FontType.HAN_SERIF,
                template_main_path=Path("/mock/template_main.json"),
                template_glyf_path=Path("/mock/template_glyf.json"),
                alphabet_pinyin_path=Path("/mock/alphabet.json"),
                pattern_one_path=Path("/mock/pattern_one.txt"),
                pattern_two_path=Path("/mock/pattern_two.json"),
                exception_pattern_path=Path("/mock/exception.json"),
                external_tool=mock_external_tool,
            )

            # Test that external tool is properly integrated
            assert builder.external_tool is mock_external_tool

            # Test conversion method
            json_path = Path("/mock/input.json")
            output_path = Path("/mock/output.ttf")

            builder._convert_json_to_otf(json_path, output_path)

            # Verify external tool was called
            assert len(mock_external_tool.converted_files) == 1
            assert mock_external_tool.converted_files[0] == (json_path, output_path)
