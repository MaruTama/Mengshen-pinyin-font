# -*- coding: utf-8 -*-
"""
Tests for CmapTableManager class.

These tests verify that the CmapTableManager works correctly with
character mapping tables, conversion functions, and file loading.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from refactored.tables.cmap_manager import CmapTableManager


class TestCmapTableManager:
    """Test CmapTableManager class functionality."""

    def test_initialization(self):
        """Test CmapTableManager initialization."""
        # Test empty initialization
        manager = CmapTableManager()
        assert manager.get_cmap_table() == {}

        # Test initialization with data
        test_cmap = {"12345": "uni3039", "20013": "uni4E2D"}
        manager = CmapTableManager(test_cmap)
        assert manager.get_cmap_table() == test_cmap

    def test_set_and_get_cmap_table(self):
        """Test setting and getting cmap table."""
        manager = CmapTableManager()
        test_cmap = {"12345": "uni3039"}

        manager.set_cmap_table(test_cmap)
        assert manager.get_cmap_table() == test_cmap

    def test_convert_hanzi_to_cid(self):
        """Test hanzi to CID conversion."""
        test_cmap = {"20013": "uni4E2D"}  # 中 character
        manager = CmapTableManager(test_cmap)

        # Test valid conversion
        result = manager.convert_hanzi_to_cid("中")
        assert result == "uni4E2D"

        # Test invalid character
        result = manager.convert_hanzi_to_cid("非")
        assert result == ""

        # Test invalid input
        result = manager.convert_hanzi_to_cid("")
        assert result == ""

        result = manager.convert_hanzi_to_cid("多字")
        assert result == ""

    def test_convert_hanzi_to_cid_safe(self):
        """Test safe hanzi to CID conversion."""
        test_cmap = {"20013": "uni4E2D"}  # 中 character
        manager = CmapTableManager(test_cmap)

        # Test valid conversion
        result = manager.convert_hanzi_to_cid_safe("中")
        assert result == "uni4E2D"

        # Test invalid character returns None
        result = manager.convert_hanzi_to_cid_safe("非")
        assert result is None

        # Test invalid input
        result = manager.convert_hanzi_to_cid_safe("")
        assert result is None

        result = manager.convert_hanzi_to_cid_safe("多字")
        assert result is None

    def test_batch_convert_hanzi_to_cid(self):
        """Test batch conversion of hanzi to CID."""
        test_cmap = {"20013": "uni4E2D", "22269": "uni56FD"}  # 中国
        manager = CmapTableManager(test_cmap)

        result = manager.batch_convert_hanzi_to_cid(["中", "国"])
        assert result == ["uni4E2D", "uni56FD"]

        # Test with missing character
        result = manager.batch_convert_hanzi_to_cid(["中", "非", "国"])
        assert result == ["uni4E2D", "", "uni56FD"]

    def test_from_path_classmethod(self):
        """Test loading CmapTableManager from file path."""
        test_font_data = {"cmap": {"20013": "uni4E2D", "22269": "uni56FD"}, "glyf": {}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_font_data, f)
            temp_path = f.name

        try:
            manager = CmapTableManager.from_path(temp_path)
            assert manager.get_cmap_table() == test_font_data["cmap"]
        finally:
            Path(temp_path).unlink()

    def test_from_path_file_not_found(self):
        """Test from_path with non-existent file."""
        with pytest.raises(FileNotFoundError):
            CmapTableManager.from_path("/non/existent/path.json")

    def test_from_path_missing_cmap(self):
        """Test from_path with missing cmap section."""
        test_data = {"glyf": {}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name

        try:
            with pytest.raises(RuntimeError, match="Failed to load cmap table"):
                CmapTableManager.from_path(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_from_template_main_success(self):
        """Test loading from template_main.json."""
        test_font_data = {"cmap": {"20013": "uni4E2D"}, "glyf": {}}

        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", create=True) as mock_open,
            patch("orjson.loads", return_value=test_font_data),
        ):

            manager = CmapTableManager.from_template_main()
            assert manager.get_cmap_table() == test_font_data["cmap"]

    def test_from_template_main_file_not_found(self):
        """Test from_template_main with missing file."""
        with patch("os.path.exists", return_value=False):
            with pytest.raises(FileNotFoundError):
                CmapTableManager.from_template_main()

    def test_lru_cache_functionality(self):
        """Test that LRU cache works correctly."""
        test_cmap = {"20013": "uni4E2D"}
        manager = CmapTableManager(test_cmap)

        # First call
        result1 = manager.convert_hanzi_to_cid("中")
        assert result1 == "uni4E2D"

        # Second call should use cache
        result2 = manager.convert_hanzi_to_cid("中")
        assert result2 == "uni4E2D"

        # Cache should be cleared when table changes
        new_cmap = {"20013": "uni4E2D_NEW"}
        manager.set_cmap_table(new_cmap)
        result3 = manager.convert_hanzi_to_cid("中")
        assert result3 == "uni4E2D_NEW"


class TestCmapTableManagerEdgeCases:
    """Test edge cases and error conditions."""

    def test_type_safety(self):
        """Test type safety in conversion methods."""
        manager = CmapTableManager()

        # Test convert_hanzi_to_cid_safe with non-string types
        result = manager.convert_hanzi_to_cid_safe(None)  # type: ignore
        assert result is None

        result = manager.convert_hanzi_to_cid_safe(123)  # type: ignore
        assert result is None

    def test_empty_cmap_table(self):
        """Test behavior with empty cmap table."""
        manager = CmapTableManager({})

        result = manager.convert_hanzi_to_cid("中")
        assert result == ""

        result = manager.convert_hanzi_to_cid_safe("中")
        assert result is None

    def test_invalid_cmap_data_type(self):
        """Test error handling for invalid cmap data."""
        test_data = {"cmap": "not_a_dict"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name

        try:
            with pytest.raises(RuntimeError, match="Failed to load cmap table"):
                CmapTableManager.from_path(temp_path)
        finally:
            Path(temp_path).unlink()
