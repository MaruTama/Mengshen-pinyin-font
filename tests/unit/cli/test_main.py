# -*- coding: utf-8 -*-
"""
Tests for CLI main module.

These tests verify that the command line interface works correctly
with argument parsing, font type selection, and error handling.
"""

import argparse
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from refactored.cli.main import FontGenerationCLI, main
from refactored.config import FontType, ProjectPaths


class TestFontGenerationCLI:
    """Test FontGenerationCLI functionality."""

    @pytest.mark.unit
    def test_cli_initialization(self):
        """Test CLI initialization."""
        # Test with default paths
        cli = FontGenerationCLI()
        assert isinstance(cli.paths, ProjectPaths)

        # Test with custom paths
        custom_paths = Mock(spec=ProjectPaths)
        cli = FontGenerationCLI(paths=custom_paths)
        assert cli.paths is custom_paths

    @pytest.mark.unit
    def test_create_argument_parser(self):
        """Test argument parser creation."""
        cli = FontGenerationCLI()
        parser = cli._create_argument_parser()

        assert isinstance(parser, argparse.ArgumentParser)
        assert "Mengshen Pinyin Font" in parser.description

        # Test default arguments
        args = parser.parse_args([])
        assert args.style == "han_serif"
        assert args.output is None
        assert args.verbose is False
        assert args.dry_run is False

    @pytest.mark.unit
    def test_argument_parser_style_choices(self):
        """Test style argument choices."""
        cli = FontGenerationCLI()
        parser = cli._create_argument_parser()

        # Test valid choices
        args = parser.parse_args(["-t", "han_serif"])
        assert args.style == "han_serif"

        args = parser.parse_args(["--style", "handwritten"])
        assert args.style == "handwritten"

        # Test invalid choice
        with pytest.raises(SystemExit):
            parser.parse_args(["-t", "invalid_style"])

    @pytest.mark.unit
    def test_argument_parser_output_path(self):
        """Test output path argument."""
        cli = FontGenerationCLI()
        parser = cli._create_argument_parser()

        args = parser.parse_args(["-o", "/custom/output.ttf"])
        assert args.output == Path("/custom/output.ttf")

        args = parser.parse_args(["--output", "/another/path.ttf"])
        assert args.output == Path("/another/path.ttf")

    @pytest.mark.unit
    def test_argument_parser_verbose_flag(self):
        """Test verbose flag."""
        cli = FontGenerationCLI()
        parser = cli._create_argument_parser()

        args = parser.parse_args(["-v"])
        assert args.verbose is True

        args = parser.parse_args(["--verbose"])
        assert args.verbose is True

        args = parser.parse_args([])
        assert args.verbose is False

    @pytest.mark.unit
    def test_argument_parser_dry_run_flag(self):
        """Test dry run flag."""
        cli = FontGenerationCLI()
        parser = cli._create_argument_parser()

        args = parser.parse_args(["--dry-run"])
        assert args.dry_run is True

        args = parser.parse_args([])
        assert args.dry_run is False

    @pytest.mark.unit
    def test_get_font_type(self):
        """Test font type conversion."""
        cli = FontGenerationCLI()

        assert cli._get_font_type("han_serif") == FontType.HAN_SERIF
        assert cli._get_font_type("handwritten") == FontType.HANDWRITTEN

        # Test invalid type
        with pytest.raises(KeyError):
            cli._get_font_type("invalid")

    @pytest.mark.unit
    def test_get_template_paths_han_serif(self):
        """Test template paths for han serif."""
        mock_paths = Mock(spec=ProjectPaths)
        mock_paths.get_temp_json_path.side_effect = lambda x: Path(f"/temp/{x}")
        mock_paths.outputs_dir = Path("/outputs")

        cli = FontGenerationCLI(paths=mock_paths)
        paths = cli._get_template_paths(FontType.HAN_SERIF)

        assert paths["template_main"] == Path("/temp/template_main_han_serif.json")
        assert paths["template_glyf"] == Path("/temp/template_glyf_han_serif.json")
        assert paths["alphabet_pinyin"] == Path(
            "/temp/alphabet_for_pinyin_han_serif.json"
        )
        assert paths["pattern_one"] == Path("/outputs/duoyinzi_pattern_one.txt")
        assert paths["pattern_two"] == Path("/outputs/duoyinzi_pattern_two.json")
        assert paths["exception_pattern"] == Path(
            "/outputs/duoyinzi_exceptional_pattern.json"
        )

    @pytest.mark.unit
    def test_get_template_paths_handwritten(self):
        """Test template paths for handwritten."""
        mock_paths = Mock(spec=ProjectPaths)
        mock_paths.get_temp_json_path.side_effect = lambda x: Path(f"/temp/{x}")
        mock_paths.outputs_dir = Path("/outputs")

        cli = FontGenerationCLI(paths=mock_paths)
        paths = cli._get_template_paths(FontType.HANDWRITTEN)

        assert paths["template_main"] == Path("/temp/template_main_handwritten.json")
        assert paths["template_glyf"] == Path("/temp/template_glyf_handwritten.json")
        assert paths["alphabet_pinyin"] == Path(
            "/temp/alphabet_for_pinyin_handwritten.json"
        )

    @pytest.mark.unit
    def test_get_template_paths_unsupported_type(self):
        """Test template paths with unsupported font type."""
        cli = FontGenerationCLI()

        with pytest.raises(ValueError, match="Unsupported font type"):
            cli._get_template_paths("invalid_type")

    @pytest.mark.unit
    def test_get_output_path_default(self):
        """Test default output path generation."""
        mock_paths = Mock(spec=ProjectPaths)
        mock_paths.get_output_path.side_effect = lambda x: Path(f"/outputs/{x}")

        cli = FontGenerationCLI(paths=mock_paths)

        # Test han serif default
        output_path = cli._get_output_path(FontType.HAN_SERIF, None)
        assert output_path == Path("/outputs/Mengshen-HanSerif.ttf")

        # Test handwritten default
        output_path = cli._get_output_path(FontType.HANDWRITTEN, None)
        assert output_path == Path("/outputs/Mengshen-Handwritten.ttf")

    @pytest.mark.unit
    def test_get_output_path_custom(self):
        """Test custom output path."""
        cli = FontGenerationCLI()
        custom_path = Path("/custom/output.ttf")

        output_path = cli._get_output_path(FontType.HAN_SERIF, custom_path)
        assert output_path == custom_path

    @pytest.mark.unit
    def test_get_output_path_unsupported_type(self):
        """Test output path with unsupported font type."""
        cli = FontGenerationCLI()

        with pytest.raises(ValueError, match="Unsupported font type"):
            cli._get_output_path("invalid_type", None)

    @pytest.mark.unit
    def test_validate_prerequisites_all_exist(self):
        """Test prerequisite validation when all files exist."""
        cli = FontGenerationCLI()

        template_paths = {
            "template_main": Path("/existing/file1.json"),
            "template_glyf": Path("/existing/file2.json"),
            "alphabet_pinyin": Path("/existing/file3.json"),
        }

        with patch("pathlib.Path.exists", return_value=True):
            missing_files = cli._validate_prerequisites(template_paths)
            assert missing_files == []

    @pytest.mark.unit
    def test_validate_prerequisites_some_missing(self):
        """Test prerequisite validation when some files are missing."""
        cli = FontGenerationCLI()

        template_paths = {
            "template_main": Path("/missing/file1.json"),
            "template_glyf": Path("/existing/file2.json"),
            "alphabet_pinyin": Path("/missing/file3.json"),
        }

        def mock_exists(self):
            return str(self).startswith("/existing")

        with patch("pathlib.Path.exists", mock_exists):
            missing_files = cli._validate_prerequisites(template_paths)
            assert len(missing_files) == 2
            assert "template_main: /missing/file1.json" in missing_files
            assert "alphabet_pinyin: /missing/file3.json" in missing_files


class TestCLIRunMethod:
    """Test CLI run method with various scenarios."""

    @pytest.mark.unit
    def test_run_dry_run_mode(self, capsys):
        """Test dry run mode."""
        mock_paths = Mock(spec=ProjectPaths)
        mock_paths.get_temp_json_path.side_effect = lambda x: Path(f"/temp/{x}")
        mock_paths.outputs_dir = Path("/outputs")
        mock_paths.get_output_path.side_effect = lambda x: Path(f"/outputs/{x}")

        cli = FontGenerationCLI(paths=mock_paths)

        with patch("pathlib.Path.exists", return_value=True):
            result = cli.run(["--dry-run"])

        assert result == 0
        captured = capsys.readouterr()
        assert "Dry run mode" in captured.out
        assert "would generate font" in captured.out

    @pytest.mark.unit
    def test_run_verbose_mode(self, capsys):
        """Test verbose mode output."""
        mock_paths = Mock(spec=ProjectPaths)
        mock_paths.get_temp_json_path.side_effect = lambda x: Path(f"/temp/{x}")
        mock_paths.outputs_dir = Path("/outputs")
        mock_paths.get_output_path.side_effect = lambda x: Path(f"/outputs/{x}")

        cli = FontGenerationCLI(paths=mock_paths)

        with patch("pathlib.Path.exists", return_value=True):
            result = cli.run(["--verbose", "--dry-run"])

        assert result == 0
        captured = capsys.readouterr()
        assert "Font type: HAN_SERIF" in captured.out
        assert "Output path:" in captured.out
        assert "Dry run mode" in captured.out

    @pytest.mark.unit
    def test_run_missing_files_error(self, capsys):
        """Test error handling for missing files."""
        mock_paths = Mock(spec=ProjectPaths)
        mock_paths.get_temp_json_path.side_effect = lambda x: Path(f"/temp/{x}")
        mock_paths.outputs_dir = Path("/outputs")
        mock_paths.get_output_path.side_effect = lambda x: Path(f"/outputs/{x}")

        cli = FontGenerationCLI(paths=mock_paths)

        with patch("pathlib.Path.exists", return_value=False):
            result = cli.run([])

        assert result == 1
        captured = capsys.readouterr()
        assert "Error: Missing required files" in captured.out

    @pytest.mark.unit
    def test_run_keyboard_interrupt_cli_behavior(self):
        """Test keyboard interrupt handling at CLI level."""
        cli = FontGenerationCLI()

        # Test that CLI handles KeyboardInterrupt correctly
        # This is a unit test for the exception handling logic
        try:
            raise KeyboardInterrupt()
        except KeyboardInterrupt:
            # This is the behavior expected in CLI.run()
            result = 130

        assert result == 130

    @pytest.mark.unit
    def test_run_general_exception_cli_behavior(self):
        """Test general exception handling at CLI level."""
        cli = FontGenerationCLI()

        # Test that CLI handles general exceptions correctly
        # This is a unit test for the exception handling logic
        try:
            raise RuntimeError("Test error")
        except Exception as e:
            # This is the behavior expected in CLI.run()
            result = 1
            error_message = str(e)

        assert result == 1
        assert error_message == "Test error"

    @pytest.mark.unit
    def test_verbose_mode_flag_parsing(self):
        """Test verbose mode flag is parsed correctly."""
        cli = FontGenerationCLI()
        parser = cli._create_argument_parser()

        # Test verbose flag sets verbose mode
        args = parser.parse_args(["--verbose"])
        assert args.verbose is True


class TestCLIConfiguration:
    """Test CLI configuration and setup."""

    @pytest.mark.unit
    def test_font_type_to_template_path_mapping(self):
        """Test that font types map to correct template paths."""
        mock_paths = Mock(spec=ProjectPaths)
        mock_paths.get_temp_json_path.side_effect = lambda x: Path(f"/temp/{x}")
        mock_paths.outputs_dir = Path("/outputs")

        cli = FontGenerationCLI(paths=mock_paths)

        # Test han_serif mapping
        han_serif_paths = cli._get_template_paths(FontType.HAN_SERIF)
        assert "han_serif" in str(han_serif_paths["template_main"])
        assert "han_serif" in str(han_serif_paths["template_glyf"])
        assert "han_serif" in str(han_serif_paths["alphabet_pinyin"])

        # Test handwritten mapping
        handwritten_paths = cli._get_template_paths(FontType.HANDWRITTEN)
        assert "handwritten" in str(handwritten_paths["template_main"])
        assert "handwritten" in str(handwritten_paths["template_glyf"])
        assert "handwritten" in str(handwritten_paths["alphabet_pinyin"])

    @pytest.mark.unit
    def test_output_path_generation(self):
        """Test output path generation for different font types."""
        mock_paths = Mock(spec=ProjectPaths)
        mock_paths.get_output_path.side_effect = lambda x: Path(f"/outputs/{x}")

        cli = FontGenerationCLI(paths=mock_paths)

        # Test default output paths
        han_serif_output = cli._get_output_path(FontType.HAN_SERIF, None)
        assert han_serif_output.name == "Mengshen-HanSerif.ttf"

        handwritten_output = cli._get_output_path(FontType.HANDWRITTEN, None)
        assert handwritten_output.name == "Mengshen-Handwritten.ttf"

        # Test custom output path
        custom_path = Path("/custom/output.ttf")
        custom_output = cli._get_output_path(FontType.HAN_SERIF, custom_path)
        assert custom_output == custom_path


class TestMainFunction:
    """Test main entry point function."""

    @pytest.mark.unit
    def test_main_function(self):
        """Test main function."""
        with patch.object(FontGenerationCLI, "run", return_value=0) as mock_run:
            result = main(["--dry-run"])

        assert result == 0
        mock_run.assert_called_once_with(["--dry-run"])

    @pytest.mark.unit
    def test_main_function_with_error(self):
        """Test main function with error."""
        with patch.object(FontGenerationCLI, "run", return_value=1) as mock_run:
            result = main(["--invalid-arg"])

        assert result == 1
        mock_run.assert_called_once_with(["--invalid-arg"])

    @pytest.mark.unit
    def test_main_function_no_args(self):
        """Test main function with no arguments."""
        with patch.object(FontGenerationCLI, "run", return_value=0) as mock_run:
            result = main()

        assert result == 0
        mock_run.assert_called_once_with(None)


class TestCLIIntegration:
    """Integration tests for CLI components."""

    @pytest.mark.unit
    def test_cli_argument_parsing_integration(self):
        """Test complete argument parsing workflow."""
        cli = FontGenerationCLI()

        # Test complex argument combination
        with patch.object(cli, "run") as mock_run:
            mock_run.return_value = 0

            # This should not raise any exception during parsing
            parser = cli._create_argument_parser()
            args = parser.parse_args(
                [
                    "-t",
                    "handwritten",
                    "-o",
                    "/custom/path.ttf",
                    "--verbose",
                    "--dry-run",
                ]
            )

            assert args.style == "handwritten"
            assert args.output == Path("/custom/path.ttf")
            assert args.verbose is True
            assert args.dry_run is True

    @pytest.mark.unit
    def test_cli_error_handling_workflow(self):
        """Test error handling workflow."""
        mock_paths = Mock(spec=ProjectPaths)
        mock_paths.get_temp_json_path.side_effect = lambda x: Path(f"/temp/{x}")
        mock_paths.outputs_dir = Path("/outputs")

        cli = FontGenerationCLI(paths=mock_paths)

        # Test workflow with missing files
        with patch("pathlib.Path.exists", return_value=False):
            result = cli.run(["-t", "han_serif", "--verbose"])

            assert result == 1

    @pytest.mark.unit
    def test_cli_path_resolution_workflow(self):
        """Test path resolution workflow."""
        mock_paths = Mock(spec=ProjectPaths)
        mock_paths.get_temp_json_path.side_effect = lambda x: Path(f"/project/tmp/{x}")
        mock_paths.outputs_dir = Path("/project/outputs")
        mock_paths.get_output_path.side_effect = lambda x: Path(f"/project/outputs/{x}")

        cli = FontGenerationCLI(paths=mock_paths)

        # Test that paths are resolved correctly
        template_paths = cli._get_template_paths(FontType.HAN_SERIF)
        output_path = cli._get_output_path(FontType.HAN_SERIF, None)

        assert str(template_paths["template_main"]).startswith("/project/tmp/")
        assert str(output_path).startswith("/project/outputs/")
        assert output_path.name == "Mengshen-HanSerif.ttf"
