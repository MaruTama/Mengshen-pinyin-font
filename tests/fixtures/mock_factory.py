# -*- coding: utf-8 -*-
"""Shared mock factory for test consistency and reduction."""

from typing import Any, Dict, Optional
from unittest.mock import MagicMock, Mock

from refactored.config import FontType
from refactored.utils.shell_utils import ShellExecutor


class MockFactory:
    """Factory for creating consistent mock objects across tests."""

    @staticmethod
    def create_mock_shell_executor(command_results: Dict[str, str] = None) -> Mock:
        """Create a mock ShellExecutor with predefined command results."""
        mock_executor = Mock(spec=ShellExecutor)

        if command_results:

            def side_effect(cmd):
                if isinstance(cmd, list):
                    cmd_str = " ".join(cmd)
                else:
                    cmd_str = cmd
                return command_results.get(cmd_str, "mocked_output")

            mock_executor.execute.side_effect = side_effect
        else:
            mock_executor.execute.return_value = "mocked_output"

        return mock_executor

    @staticmethod
    def create_mock_font_config(font_type: FontType = FontType.HAN_SERIF) -> Mock:
        """Create a mock FontConfig with standard values."""
        mock_config = Mock()
        mock_config.font_type = font_type
        mock_config.hanzi_canvas_width = 2048
        mock_config.hanzi_canvas_height = 2048
        mock_config.pinyin_canvas_width = 2048
        mock_config.pinyin_canvas_height = 2628
        mock_config.pinyin_vertical_origin = 2312
        mock_config.tracking = 100
        return mock_config

    @staticmethod
    def create_mock_data_manager(data: Dict[str, Any] = None) -> Mock:
        """Create a mock data manager with optional data."""
        mock_manager = Mock()
        mock_manager.data = data or {}
        mock_manager.get_data.return_value = mock_manager.data
        mock_manager.load_data.return_value = True
        mock_manager.is_loaded = True
        return mock_manager

    @staticmethod
    def create_mock_glyph_manager(glyphs: Dict[str, Any] = None) -> Mock:
        """Create a mock glyph manager with optional glyph data."""
        mock_manager = Mock()
        mock_manager.glyphs = glyphs or {}
        mock_manager.get_glyph.side_effect = lambda name: mock_manager.glyphs.get(name)
        mock_manager.add_glyph.side_effect = (
            lambda name, glyph: mock_manager.glyphs.update({name: glyph})
        )
        mock_manager.generate_pinyin_glyphs.return_value = True
        return mock_manager

    @staticmethod
    def create_mock_font_builder(font_type: FontType = FontType.HAN_SERIF) -> Mock:
        """Create a mock FontBuilder with standard configuration."""
        mock_builder = Mock()
        mock_builder.font_type = font_type
        mock_builder.build.return_value = True
        mock_builder.output_path = f"/test/output/Mengshen-{font_type.name}.ttf"
        return mock_builder

    @staticmethod
    def create_mock_file_data(content: str = '{"test": "data"}') -> MagicMock:
        """Create a mock file object with specified content."""
        mock_file = MagicMock()
        mock_file.read.return_value = content
        mock_file.__enter__.return_value = mock_file
        mock_file.__exit__.return_value = None
        return mock_file

    @staticmethod
    def create_mock_json_data(data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create standard mock JSON data structure."""
        return data or {
            "test_key": "test_value",
            "nested": {"key": "value"},
            "list": ["item1", "item2"],
        }

    @staticmethod
    def create_mock_cmap_table(size: int = 100) -> Dict[str, str]:
        """Create a mock cmap table with specified size."""
        return {str(i): f"cid{i:05d}" for i in range(size)}

    @staticmethod
    def create_mock_pinyin_data(pronunciations: list = None) -> Dict[str, list]:
        """Create mock pinyin data with specified pronunciations."""
        if pronunciations is None:
            pronunciations = ["zhōng", "guó", "rén"]

        return {
            "一": ["yī"],
            "二": ["èr"],
            "三": ["sān"],
            "中": ["zhōng"],
            "国": ["guó"],
            "人": ["rén"],
        }

    @staticmethod
    def create_mock_error_conditions() -> Dict[str, Exception]:
        """Create standard error conditions for testing."""
        return {
            "file_not_found": FileNotFoundError("Test file not found"),
            "permission_denied": PermissionError("Permission denied"),
            "value_error": ValueError("Invalid value"),
            "key_error": KeyError("Missing key"),
            "security_error": Exception("Security violation"),
        }
