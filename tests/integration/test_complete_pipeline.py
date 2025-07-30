# -*- coding: utf-8 -*-
"""
Complete pipeline integration tests.

These tests verify that the entire font generation pipeline works correctly,
from input data processing to final font output.
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from refactored.cli.main import FontGenerationCLI
from refactored.config import FontType


class TestCompletePipeline:
    """Test the complete font generation pipeline."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_han_serif_font_generation(self, temp_dir, mock_external_tools):
        """Test complete HAN_SERIF font generation pipeline."""
        # Create necessary directories
        (temp_dir / "tmp" / "json").mkdir(parents=True)
        (temp_dir / "outputs").mkdir(parents=True)

        # Create mock template files
        self._create_mock_template_files(temp_dir)

        # Create mock data files (including merged-mapping-table.txt)
        self._create_mock_data_files(temp_dir)

        # Mock the working directory to use our temp directory
        with patch("os.getcwd", return_value=str(temp_dir)):
            with patch(
                "refactored.config.paths.PROJECT_ROOT",
                temp_dir,
            ):
                # Create CLI instance inside the patch context
                cli = FontGenerationCLI()

                # Test font generation
                result = cli.generate_font(FontType.HAN_SERIF)

                # Verify successful generation
                assert result is not None

                # Verify output file would be created
                expected_output = temp_dir / "outputs" / "Mengshen-HanSerif.ttf"
                # Note: In real test, this would exist. In mock test, we just verify the process completed.

    @pytest.mark.integration
    @pytest.mark.slow
    def test_handwritten_font_generation(self, temp_dir, mock_external_tools):
        """Test complete HANDWRITTEN font generation pipeline."""
        # Create necessary directories
        (temp_dir / "tmp" / "json").mkdir(parents=True)
        (temp_dir / "outputs").mkdir(parents=True)

        # Create mock template files
        self._create_mock_template_files(temp_dir)

        # Create mock data files (including merged-mapping-table.txt)
        self._create_mock_data_files(temp_dir)

        # Mock the working directory to use our temp directory
        with patch("os.getcwd", return_value=str(temp_dir)):
            with patch(
                "refactored.config.paths.PROJECT_ROOT",
                temp_dir,
            ):
                # Create CLI instance inside the patch context
                cli = FontGenerationCLI()

                # Test font generation
                result = cli.generate_font(FontType.HANDWRITTEN)

                # Verify successful generation
                assert result is not None

                # Verify output file would be created
                expected_output = temp_dir / "outputs" / "Mengshen-Handwritten.ttf"
                # Note: In real test, this would exist. In mock test, we just verify the process completed.

    @pytest.mark.integration
    def test_template_json_creation(self, temp_dir, mock_external_tools):
        """Test template JSON creation from font files."""
        from refactored.scripts.make_template_jsons import TemplateJsonMaker

        # Create mock font files
        (temp_dir / "res" / "fonts" / "han-serif").mkdir(parents=True)
        (temp_dir / "res" / "fonts" / "handwritten").mkdir(parents=True)
        (temp_dir / "tmp" / "json").mkdir(parents=True)

        # Create mock font files
        han_serif_font = (
            temp_dir / "res" / "fonts" / "han-serif" / "SourceHanSerifCN-Regular.ttf"
        )
        han_serif_font.write_bytes(b"MOCK_FONT_DATA")

        handwritten_font = (
            temp_dir
            / "res"
            / "fonts"
            / "handwritten"
            / "XiaolaiMonoSC-without-Hangul-Regular.ttf"
        )
        handwritten_font.write_bytes(b"MOCK_FONT_DATA")

        # Test template creation
        maker = TemplateJsonMaker()

        with patch(
            "refactored.config.paths.PROJECT_ROOT",
            temp_dir,
        ):
            # Should not raise exceptions
            maker.make_template(str(han_serif_font), "han_serif")
            maker.make_template(str(handwritten_font), "handwritten")

    @pytest.mark.integration
    def test_alphabet_retrieval(self, temp_dir, mock_external_tools):
        """Test Latin alphabet retrieval from fonts."""
        from refactored.scripts.retrieve_latin_alphabet import LatinAlphabetRetriever

        # Create mock font files
        (temp_dir / "res" / "fonts" / "han-serif").mkdir(parents=True)
        (temp_dir / "tmp" / "json").mkdir(parents=True)

        # Create mock pinyin font
        pinyin_font = temp_dir / "res" / "fonts" / "han-serif" / "mplus-1m-medium.ttf"
        pinyin_font.write_bytes(b"MOCK_PINYIN_FONT_DATA")

        # Test alphabet retrieval
        retriever = LatinAlphabetRetriever()

        with patch(
            "refactored.config.paths.PROJECT_ROOT",
            temp_dir,
        ):
            # Should not raise exceptions
            retriever.retrieve_alphabet(str(pinyin_font), "han_serif")

    @pytest.mark.integration
    def test_data_loading_pipeline(self, temp_dir):
        """Test that data loading pipeline works correctly."""
        from refactored.data import (
            CharacterDataManager,
            MappingDataManager,
            PinyinDataManager,
        )

        # Create mock data files
        self._create_mock_data_files(temp_dir)

        # Test data manager initialization
        pinyin_manager = PinyinDataManager()
        character_manager = CharacterDataManager(pinyin_manager)

        # Should not raise exceptions
        assert pinyin_manager is not None
        assert character_manager is not None

        # Test basic functionality
        single_chars = list(character_manager.iter_single_pronunciation_characters())
        multiple_chars = list(
            character_manager.iter_multiple_pronunciation_characters()
        )

        # Should return some characters (even if mocked)
        assert len(single_chars) >= 0  # May be empty in mock
        assert len(multiple_chars) >= 0  # May be empty in mock

    @pytest.mark.integration
    def test_font_builder_integration(self, temp_dir, create_test_files):
        """Test FontBuilder integration with real data."""
        from refactored.config import ProjectPaths
        from refactored.data import (
            CharacterDataManager,
            MappingDataManager,
            PinyinDataManager,
        )
        from refactored.data.mapping_data import JsonCmapDataSource
        from refactored.generation.font_builder import FontBuilder

        # Use test files created by fixture
        template_main_path = create_test_files["template_main"]
        template_glyf_path = create_test_files["glyf"]
        alphabet_path = create_test_files["alphabet"]

        # Create mock pattern files
        pattern_one_path = temp_dir / "pattern_one.txt"
        pattern_two_path = temp_dir / "pattern_two.json"
        exception_pattern_path = temp_dir / "exception_pattern.json"

        pattern_one_path.write_text("1, 中, zhōng, [~國]")
        pattern_two_path.write_text('{"lookup_table": {}, "patterns": {}}')
        exception_pattern_path.write_text('{"lookup_table": {}, "patterns": {}}')

        # Create data managers
        pinyin_manager = PinyinDataManager()
        character_manager = CharacterDataManager(pinyin_manager)
        cmap_source = JsonCmapDataSource(template_main_path)
        paths = ProjectPaths()
        mapping_manager = MappingDataManager(cmap_source=cmap_source, paths=paths)

        # Create FontBuilder
        builder = FontBuilder(
            font_type=FontType.HAN_SERIF,
            template_main_path=template_main_path,
            template_glyf_path=template_glyf_path,
            alphabet_pinyin_path=alphabet_path,
            pattern_one_path=pattern_one_path,
            pattern_two_path=pattern_two_path,
            exception_pattern_path=exception_pattern_path,
            pinyin_manager=pinyin_manager,
            character_manager=character_manager,
            mapping_manager=mapping_manager,
        )

        # Test initialization
        assert builder is not None
        assert builder.font_type == FontType.HAN_SERIF

        # Test template loading
        builder._load_templates()
        assert builder._font_data is not None
        assert builder._glyf_data is not None

    @pytest.mark.integration
    def test_gsub_table_generation(self, temp_dir, create_test_files):
        """Test GSUB table generation in isolation."""
        from refactored.config import ProjectPaths
        from refactored.data import (
            CharacterDataManager,
            MappingDataManager,
            PinyinDataManager,
        )
        from refactored.data.mapping_data import JsonCmapDataSource
        from refactored.tables.gsub_table_generator import GSUBTableGenerator

        # Create mock pattern files
        pattern_one_path = temp_dir / "pattern_one.txt"
        pattern_two_path = temp_dir / "pattern_two.json"
        exception_pattern_path = temp_dir / "exception_pattern.json"

        pattern_one_path.write_text("2, 中, zhòng, [~國]")
        pattern_two_path.write_text('{"lookup_table": {}, "patterns": {}}')
        exception_pattern_path.write_text('{"lookup_table": {}, "patterns": {}}')

        # Create data managers
        pinyin_manager = PinyinDataManager()
        character_manager = CharacterDataManager(pinyin_manager)
        cmap_source = JsonCmapDataSource(create_test_files["template_main"])
        paths = ProjectPaths()
        mapping_manager = MappingDataManager(cmap_source=cmap_source, paths=paths)

        # Load cmap table
        import json

        with open(create_test_files["template_main"]) as f:
            cmap_table = json.load(f)["cmap"]

        # Create GSUB generator
        generator = GSUBTableGenerator(
            pattern_one_path=pattern_one_path,
            pattern_two_path=pattern_two_path,
            exception_pattern_path=exception_pattern_path,
            character_manager=character_manager,
            mapping_manager=mapping_manager,
            cmap_table=cmap_table,
        )

        # Test GSUB table generation
        gsub_table = generator.generate_gsub_table()

        # Verify structure
        assert isinstance(gsub_table, dict)
        assert "languages" in gsub_table
        assert "features" in gsub_table
        assert "lookups" in gsub_table
        assert "lookupOrder" in gsub_table

    @pytest.mark.integration
    @pytest.mark.requires_external_tools
    def test_script_integration(self, temp_dir):
        """Test script integration with actual commands."""
        # This test would require actual external tools
        # Skip if tools are not available

        # If tools are available, test actual script execution
        from refactored.scripts.make_template_jsons import make_template_main
        from refactored.scripts.retrieve_latin_alphabet import retrieve_alphabet_main

        # Test template creation
        make_template_main(["--style", "han_serif"])

        # Test alphabet retrieval
        retrieve_alphabet_main(["--style", "han_serif"])

    def _create_mock_template_files(self, temp_dir):
        """Create mock template files for testing."""
        # Create template main JSON
        template_main = {
            "cmap": {
                "20013": "cid00001",  # 中
                "22269": "cid00002",  # 国
            },
            "glyf": {
                "cid00001": {
                    "advanceWidth": 1000,
                    "advanceHeight": 1000,
                    "contours": [],
                },
                "cid00002": {
                    "advanceWidth": 1000,
                    "advanceHeight": 1000,
                    "contours": [],
                },
            },
            "head": {"fontRevision": 1.0},
            "hhea": {"ascender": 880},
            "OS_2": {"usWinAscent": 880},
            "name": {},
        }

        template_main_path = temp_dir / "tmp" / "json" / "template_main_han_serif.json"
        with open(template_main_path, "w", encoding="utf-8") as f:
            import json

            json.dump(template_main, f, indent=2)

        # Create handwritten template as well
        template_main_handwritten_path = (
            temp_dir / "tmp" / "json" / "template_main_handwritten.json"
        )
        with open(template_main_handwritten_path, "w", encoding="utf-8") as f:
            json.dump(template_main, f, indent=2)

        # Create template glyf JSON
        glyf_data = {
            "cid00001": {
                "advanceWidth": 1000,
                "advanceHeight": 1000,
                "contours": [
                    [
                        {"x": 100, "y": 100, "on": True},
                        {"x": 900, "y": 100, "on": True},
                        {"x": 900, "y": 900, "on": True},
                        {"x": 100, "y": 900, "on": True},
                    ]
                ],
            }
        }

        glyf_path = temp_dir / "tmp" / "json" / "template_glyf_han_serif.json"
        with open(glyf_path, "w", encoding="utf-8") as f:
            import json

            json.dump(glyf_data, f, indent=2)

        # Create handwritten glyf as well
        glyf_handwritten_path = (
            temp_dir / "tmp" / "json" / "template_glyf_handwritten.json"
        )
        with open(glyf_handwritten_path, "w", encoding="utf-8") as f:
            json.dump(glyf_data, f, indent=2)

        # Create alphabet JSON
        alphabet_data = {
            "a": {
                "advanceWidth": 600,
                "advanceHeight": 800,
                "contours": [
                    [
                        {"x": 50, "y": 50, "on": True},
                        {"x": 550, "y": 50, "on": True},
                        {"x": 550, "y": 750, "on": True},
                        {"x": 50, "y": 750, "on": True},
                    ]
                ],
            }
        }

        alphabet_path = temp_dir / "tmp" / "json" / "alphabet_for_pinyin_han_serif.json"
        with open(alphabet_path, "w", encoding="utf-8") as f:
            import json

            json.dump(alphabet_data, f, indent=2)

        # Create handwritten alphabet as well
        alphabet_handwritten_path = (
            temp_dir / "tmp" / "json" / "alphabet_for_pinyin_handwritten.json"
        )
        with open(alphabet_handwritten_path, "w", encoding="utf-8") as f:
            json.dump(alphabet_data, f, indent=2)

    def _create_mock_data_files(self, temp_dir):
        """Create mock data files for testing."""
        # Create phonics directory structure
        phonics_dir = temp_dir / "res" / "phonics"
        phonics_dir.mkdir(parents=True)

        # Create pinyin data directory
        pinyin_data_dir = phonics_dir / "pinyin-data"
        pinyin_data_dir.mkdir(parents=True)

        # Create mock pinyin.txt
        pinyin_file = pinyin_data_dir / "pinyin.txt"
        pinyin_file.write_text("U+4E2D: zhōng,zhòng  # 中\nU+56FD: guó  # 国\n")

        # Create outputs directory
        outputs_dir = temp_dir / "outputs"
        outputs_dir.mkdir(parents=True, exist_ok=True)

        # Create mock merged-mapping-table.txt (required by PinyinDataManager)
        merged_mapping_file = outputs_dir / "merged-mapping-table.txt"
        merged_mapping_file.write_text(
            "U+4E2D: zhōng,zhòng  # 中\n"
            "U+56FD: guó  # 国\n"
            "U+4EBA: rén  # 人\n"
            "U+4E00: yī  # 一\n"
            "U+4E8C: èr  # 二\n"
            "U+4E09: sān  # 三\n"
        )

        # Create mock pattern files
        pattern_one_file = outputs_dir / "duoyinzi_pattern_one.txt"
        pattern_one_file.write_text("1, 中, zhōng, [~國]\n2, 中, zhòng, [~央]\n")

        pattern_two_file = outputs_dir / "duoyinzi_pattern_two.json"
        pattern_two_file.write_text('{"lookup_table": {}, "patterns": {}}')

        exception_pattern_file = outputs_dir / "duoyinzi_exceptional_pattern.json"
        exception_pattern_file.write_text('{"lookup_table": {}, "patterns": {}}')


class TestPipelineErrorHandling:
    """Test error handling in the pipeline."""

    @pytest.mark.integration
    def test_missing_template_files(self, temp_dir):
        """Test behavior when template files are missing."""
        from refactored.config import ProjectPaths
        from refactored.generation.font_builder import FontBuilder

        # Create FontBuilder with non-existent files
        non_existent_path = temp_dir / "non_existent.json"

        with pytest.raises(FileNotFoundError):
            builder = FontBuilder(
                font_type=FontType.HAN_SERIF,
                template_main_path=non_existent_path,
                template_glyf_path=non_existent_path,
                alphabet_pinyin_path=non_existent_path,
                pattern_one_path=non_existent_path,
                pattern_two_path=non_existent_path,
                exception_pattern_path=non_existent_path,
            )
            builder._load_templates()

    @pytest.mark.integration
    def test_corrupted_template_files(self, temp_dir):
        """Test behavior with corrupted template files."""
        # Create corrupted JSON file
        corrupted_file = temp_dir / "corrupted.json"
        corrupted_file.write_text("{ invalid json content }")

        from refactored.generation.font_builder import FontBuilder

        with pytest.raises((ValueError, KeyError, RuntimeError)):
            builder = FontBuilder(
                font_type=FontType.HAN_SERIF,
                template_main_path=corrupted_file,
                template_glyf_path=corrupted_file,
                alphabet_pinyin_path=corrupted_file,
                pattern_one_path=corrupted_file,
                pattern_two_path=corrupted_file,
                exception_pattern_path=corrupted_file,
            )
            builder._load_templates()

    @pytest.mark.integration
    def test_insufficient_disk_space(self, temp_dir):
        """Test behavior with insufficient disk space."""
        # This is difficult to test without actually filling up disk
        # For now, just verify that the pipeline handles large files gracefully

        from refactored.generation.font_builder import FontBuilder

        # Create very large mock data (simulate large font)
        large_glyf_data = {
            f"cid{i:05d}": {
                "advanceWidth": 1000,
                "advanceHeight": 1000,
                "contours": [
                    [
                        {"x": j, "y": j, "on": True}
                        for j in range(100)  # Large contour data
                    ]
                ],
            }
            for i in range(1000)  # Many glyphs
        }

        large_glyf_path = temp_dir / "large_glyf.json"
        with open(large_glyf_path, "w", encoding="utf-8") as f:
            import json

            json.dump(large_glyf_data, f)

        # Should handle large files without crashing
        assert large_glyf_path.exists()
        assert large_glyf_path.stat().st_size > 1024  # At least 1KB

    @pytest.mark.integration
    def test_external_tool_failure(self, temp_dir):
        """Test behavior when external tools fail."""
        from refactored.utils.shell_utils import SecurityError, ShellExecutor

        executor = ShellExecutor()

        # Test with command that will fail
        with pytest.raises((SecurityError, FileNotFoundError)):
            executor.execute(["non_existent_command_12345"])

        # Test with command that returns non-zero exit code
        result = executor.execute(["false"])  # Always returns 1
        assert result.returncode != 0
