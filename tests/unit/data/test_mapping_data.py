# -*- coding: utf-8 -*-
"""
Tests for mapping data management.

These tests verify that the mapping data system works correctly
with Unicode to CID mapping, character lookups, and JSON data sources.
"""

from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from refactored.config import ProjectPaths
from refactored.data.mapping_data import (
    CmapDataSource,
    JsonCmapDataSource,
    MappingDataManager,
    get_default_mapping_manager,
)


class TestJsonCmapDataSource:
    """Test JsonCmapDataSource functionality."""

    @pytest.mark.unit
    def test_json_cmap_data_source_initialization(self):
        """Test JsonCmapDataSource initialization."""
        template_path = Path("/mock/template.json")
        source = JsonCmapDataSource(template_path)

        assert source.template_path == template_path
        assert source._cmap_table is None

    @pytest.mark.unit
    def test_load_cmap_table_missing_file(self):
        """Test _load_cmap_table when JSON file is missing."""
        template_path = Path("/nonexistent/template.json")
        source = JsonCmapDataSource(template_path)

        with pytest.raises(FileNotFoundError, match="Template JSON not found"):
            source._load_cmap_table()

    @pytest.mark.unit
    def test_load_cmap_table_valid_file(self):
        """Test _load_cmap_table with valid JSON file."""
        template_path = Path("/mock/template.json")
        source = JsonCmapDataSource(template_path)

        # Mock JSON data
        mock_json_data = {
            "cmap": {
                "20013": "cid00001",  # 中
                "22269": "cid00002",  # 国
                "20154": "cid00003",  # 人
            },
            "other_data": "ignored",
        }

        with patch("pathlib.Path.exists", return_value=True), patch(
            "builtins.open", mock_open()
        ), patch("orjson.loads", return_value=mock_json_data):

            source._load_cmap_table()

            assert source._cmap_table is not None
            assert len(source._cmap_table) == 3
            assert source._cmap_table["20013"] == "cid00001"
            assert source._cmap_table["22269"] == "cid00002"
            assert source._cmap_table["20154"] == "cid00003"

    @pytest.mark.unit
    def test_load_cmap_table_no_cmap_key(self):
        """Test _load_cmap_table when JSON has no cmap key."""
        template_path = Path("/mock/template.json")
        source = JsonCmapDataSource(template_path)

        mock_json_data = {"other_data": "no cmap key"}

        with patch("pathlib.Path.exists", return_value=True), patch(
            "builtins.open", mock_open()
        ), patch("orjson.loads", return_value=mock_json_data):

            source._load_cmap_table()

            assert source._cmap_table == {}

    @pytest.mark.unit
    def test_get_cmap_table(self):
        """Test get_cmap_table functionality."""
        template_path = Path("/mock/template.json")
        source = JsonCmapDataSource(template_path)

        mock_json_data = {
            "cmap": {
                "20013": "cid00001",  # 中
                "22269": "cid00002",  # 国
            }
        }

        with patch("pathlib.Path.exists", return_value=True), patch(
            "builtins.open", mock_open()
        ), patch("orjson.loads", return_value=mock_json_data):

            result = source.get_cmap_table()

            assert len(result) == 2
            assert result["20013"] == "cid00001"
            assert result["22269"] == "cid00002"

    @pytest.mark.unit
    def test_get_cmap_table_returns_copy(self):
        """Test that get_cmap_table returns a copy."""
        template_path = Path("/mock/template.json")
        source = JsonCmapDataSource(template_path)

        mock_json_data = {
            "cmap": {
                "20013": "cid00001",
            }
        }

        with patch("pathlib.Path.exists", return_value=True), patch(
            "builtins.open", mock_open()
        ), patch("orjson.loads", return_value=mock_json_data):

            result1 = source.get_cmap_table()
            result2 = source.get_cmap_table()

            # Should return copies, not the same object
            assert result1 is not result2
            assert result1 == result2

            # Modifying one should not affect the other
            result1["20013"] = "modified"
            assert result2["20013"] == "cid00001"

    @pytest.mark.unit
    def test_lazy_loading(self):
        """Test that data is loaded lazily."""
        template_path = Path("/mock/template.json")
        source = JsonCmapDataSource(template_path)

        # Initially, data should not be loaded
        assert source._cmap_table is None

        mock_json_data = {"cmap": {"20013": "cid00001"}}

        with patch("pathlib.Path.exists", return_value=True), patch(
            "builtins.open", mock_open()
        ) as mock_file, patch("orjson.loads", return_value=mock_json_data):

            # First call should load data
            result1 = source.get_cmap_table()
            assert source._cmap_table is not None

            # Second call should not reload data
            result2 = source.get_cmap_table()

            # File should only be opened once
            mock_file.assert_called_once()


class TestMappingDataManager:
    """Test MappingDataManager functionality."""

    @pytest.mark.unit
    def test_mapping_data_manager_initialization(self):
        """Test MappingDataManager initialization."""
        # Test with default parameters
        manager = MappingDataManager()
        assert manager.paths is not None
        assert isinstance(manager.paths, ProjectPaths)
        assert manager._cmap_source is None
        assert manager._cmap_table is None

        # Test with custom parameters
        custom_paths = ProjectPaths()
        custom_source = Mock(spec=CmapDataSource)
        manager = MappingDataManager(cmap_source=custom_source, paths=custom_paths)
        assert manager.paths is custom_paths
        assert manager._cmap_source is custom_source

    @pytest.mark.unit
    def test_get_cmap_source_with_custom_source(self):
        """Test _get_cmap_source with custom source."""
        custom_source = Mock(spec=CmapDataSource)
        manager = MappingDataManager(cmap_source=custom_source)

        result = manager._get_cmap_source()
        assert result is custom_source

    @pytest.mark.unit
    def test_get_cmap_source_creates_default(self):
        """Test _get_cmap_source creates default source when none provided."""
        mock_paths = Mock(spec=ProjectPaths)
        mock_template_path = Path("/mock/template.json")
        mock_paths.get_temp_json_path.return_value = mock_template_path

        manager = MappingDataManager(paths=mock_paths)

        with patch(
            "refactored.data.mapping_data.JsonCmapDataSource"
        ) as mock_source_class:
            mock_source_instance = Mock(spec=JsonCmapDataSource)
            mock_source_class.return_value = mock_source_instance

            result = manager._get_cmap_source()

            assert result is mock_source_instance
            mock_source_class.assert_called_once_with(mock_template_path)
            mock_paths.get_temp_json_path.assert_called_once_with("template_main.json")

    @pytest.mark.unit
    def test_get_cmap_table(self):
        """Test get_cmap_table functionality."""
        mock_source = Mock(spec=CmapDataSource)
        mock_cmap_data = {
            "20013": "cid00001",  # 中
            "22269": "cid00002",  # 国
        }
        mock_source.get_cmap_table.return_value = mock_cmap_data

        manager = MappingDataManager(cmap_source=mock_source)
        result = manager.get_cmap_table()

        assert result == mock_cmap_data
        mock_source.get_cmap_table.assert_called_once()

    @pytest.mark.unit
    def test_get_cmap_table_caching(self):
        """Test that get_cmap_table caches results."""
        mock_source = Mock(spec=CmapDataSource)
        mock_cmap_data = {"20013": "cid00001"}
        mock_source.get_cmap_table.return_value = mock_cmap_data

        manager = MappingDataManager(cmap_source=mock_source)

        # First call
        result1 = manager.get_cmap_table()
        assert result1 == mock_cmap_data

        # Second call should use cache
        result2 = manager.get_cmap_table()
        assert result2 == mock_cmap_data

        # Source should only be called once
        mock_source.get_cmap_table.assert_called_once()

    @pytest.mark.unit
    def test_convert_hanzi_to_cid_found(self):
        """Test convert_hanzi_to_cid with existing character."""
        mock_source = Mock(spec=CmapDataSource)
        mock_cmap_data = {
            "20013": "cid00001",  # 中 (Unicode 20013)
            "22269": "cid00002",  # 国 (Unicode 22269)
        }
        mock_source.get_cmap_table.return_value = mock_cmap_data

        manager = MappingDataManager(cmap_source=mock_source)

        result = manager.convert_hanzi_to_cid("中")
        assert result == "cid00001"

        result = manager.convert_hanzi_to_cid("国")
        assert result == "cid00002"

    @pytest.mark.unit
    def test_convert_hanzi_to_cid_not_found(self):
        """Test convert_hanzi_to_cid with non-existing character."""
        mock_source = Mock(spec=CmapDataSource)
        mock_cmap_data = {"20013": "cid00001"}
        mock_source.get_cmap_table.return_value = mock_cmap_data

        manager = MappingDataManager(cmap_source=mock_source)

        result = manager.convert_hanzi_to_cid("不")
        assert result is None

    @pytest.mark.unit
    def test_has_glyph_for_character(self):
        """Test has_glyph_for_character functionality."""
        mock_source = Mock(spec=CmapDataSource)
        mock_cmap_data = {"20013": "cid00001"}  # 中
        mock_source.get_cmap_table.return_value = mock_cmap_data

        manager = MappingDataManager(cmap_source=mock_source)

        assert manager.has_glyph_for_character("中") is True
        assert manager.has_glyph_for_character("不") is False

    @pytest.mark.unit
    def test_get_missing_characters(self):
        """Test get_missing_characters functionality."""
        mock_source = Mock(spec=CmapDataSource)
        mock_cmap_data = {
            "20013": "cid00001",  # 中
            "22269": "cid00002",  # 国
        }
        mock_source.get_cmap_table.return_value = mock_cmap_data

        manager = MappingDataManager(cmap_source=mock_source)

        characters = ["中", "国", "人", "文"]
        missing = manager.get_missing_characters(characters)

        assert len(missing) == 2
        assert "人" in missing
        assert "文" in missing
        assert "中" not in missing
        assert "国" not in missing

    @pytest.mark.unit
    def test_get_available_characters(self):
        """Test get_available_characters functionality."""
        mock_source = Mock(spec=CmapDataSource)
        mock_cmap_data = {
            "20013": "cid00001",  # 中
            "22269": "cid00002",  # 国
        }
        mock_source.get_cmap_table.return_value = mock_cmap_data

        manager = MappingDataManager(cmap_source=mock_source)

        characters = ["中", "国", "人", "文"]
        available = manager.get_available_characters(characters)

        assert len(available) == 2
        assert "中" in available
        assert "国" in available
        assert "人" not in available
        assert "文" not in available

    @pytest.mark.unit
    def test_get_unicode_from_cid(self):
        """Test get_unicode_from_cid functionality."""
        mock_source = Mock(spec=CmapDataSource)
        mock_cmap_data = {
            "20013": "cid00001",  # 中
            "22269": "cid00002",  # 国
        }
        mock_source.get_cmap_table.return_value = mock_cmap_data

        manager = MappingDataManager(cmap_source=mock_source)

        result = manager.get_unicode_from_cid("cid00001")
        assert result == "20013"

        result = manager.get_unicode_from_cid("cid00002")
        assert result == "22269"

        result = manager.get_unicode_from_cid("nonexistent")
        assert result is None

    @pytest.mark.unit
    def test_get_character_from_cid(self):
        """Test get_character_from_cid functionality."""
        mock_source = Mock(spec=CmapDataSource)
        mock_cmap_data = {
            "20013": "cid00001",  # 中
            "22269": "cid00002",  # 国
        }
        mock_source.get_cmap_table.return_value = mock_cmap_data

        manager = MappingDataManager(cmap_source=mock_source)

        result = manager.get_character_from_cid("cid00001")
        assert result == "中"

        result = manager.get_character_from_cid("cid00002")
        assert result == "国"

        result = manager.get_character_from_cid("nonexistent")
        assert result is None

    @pytest.mark.unit
    def test_get_character_from_cid_invalid_unicode(self):
        """Test get_character_from_cid with invalid Unicode."""
        mock_source = Mock(spec=CmapDataSource)
        mock_cmap_data = {
            "invalid": "cid00001",  # Invalid Unicode
            "999999999": "cid00002",  # Out of range Unicode
        }
        mock_source.get_cmap_table.return_value = mock_cmap_data

        manager = MappingDataManager(cmap_source=mock_source)

        result = manager.get_character_from_cid("cid00001")
        assert result is None

        result = manager.get_character_from_cid("cid00002")
        assert result is None

    @pytest.mark.unit
    def test_get_glyph_statistics(self):
        """Test get_glyph_statistics functionality."""
        mock_source = Mock(spec=CmapDataSource)
        mock_cmap_data = {
            "20013": "cid00001",  # 中
            "22269": "cid00002",  # 国
            "20154": "cid00003",  # 人
        }
        mock_source.get_cmap_table.return_value = mock_cmap_data

        manager = MappingDataManager(cmap_source=mock_source)
        stats = manager.get_glyph_statistics()

        assert stats["total_glyphs"] == 3
        assert stats["unicode_range_start"] == 20013
        assert stats["unicode_range_end"] == 22269

    @pytest.mark.unit
    def test_get_glyph_statistics_empty(self):
        """Test get_glyph_statistics with empty data."""
        mock_source = Mock(spec=CmapDataSource)
        mock_source.get_cmap_table.return_value = {}

        manager = MappingDataManager(cmap_source=mock_source)
        stats = manager.get_glyph_statistics()

        assert stats["total_glyphs"] == 0
        assert stats["unicode_range_start"] == 0
        assert stats["unicode_range_end"] == 0

    @pytest.mark.unit
    def test_get_unicode_mappings(self):
        """Test get_unicode_mappings compatibility method."""
        mock_source = Mock(spec=CmapDataSource)
        mock_cmap_data = {"20013": "cid00001"}
        mock_source.get_cmap_table.return_value = mock_cmap_data

        manager = MappingDataManager(cmap_source=mock_source)

        result = manager.get_unicode_mappings()
        assert result == mock_cmap_data

    @pytest.mark.unit
    def test_load_mappings(self):
        """Test load_mappings method."""
        mock_source = Mock(spec=CmapDataSource)
        mock_cmap_data = {"20013": "cid00001"}
        mock_source.get_cmap_table.return_value = mock_cmap_data

        manager = MappingDataManager(cmap_source=mock_source)

        # Should trigger loading
        manager.load_mappings()

        # Verify that cmap table was loaded
        assert manager._cmap_table is not None
        mock_source.get_cmap_table.assert_called_once()

    @pytest.mark.unit
    def test_convert_hanzi_to_cid_caching(self):
        """Test that convert_hanzi_to_cid uses caching."""
        mock_source = Mock(spec=CmapDataSource)
        mock_cmap_data = {"20013": "cid00001"}
        mock_source.get_cmap_table.return_value = mock_cmap_data

        manager = MappingDataManager(cmap_source=mock_source)

        # Multiple calls with same character
        result1 = manager.convert_hanzi_to_cid("中")
        result2 = manager.convert_hanzi_to_cid("中")
        result3 = manager.convert_hanzi_to_cid("中")

        assert result1 == result2 == result3 == "cid00001"

        # get_cmap_table should only be called once due to caching
        mock_source.get_cmap_table.assert_called_once()


class TestGlobalFunctions:
    """Test global utility functions."""

    @pytest.mark.unit
    def test_get_default_mapping_manager(self):
        """Test get_default_mapping_manager functionality."""
        # Clear any existing global instance
        import refactored.data.mapping_data

        refactored.data.mapping_data._default_mapping_manager = None

        # First call should create instance
        manager1 = get_default_mapping_manager()
        assert manager1 is not None
        assert isinstance(manager1, MappingDataManager)

        # Second call should return same instance
        manager2 = get_default_mapping_manager()
        assert manager1 is manager2


class TestMappingDataIntegration:
    """Integration tests for mapping data components."""

    @pytest.mark.unit
    def test_full_mapping_data_integration(self):
        """Test full integration of mapping data components."""
        # Create mock JSON data
        mock_json_data = {
            "cmap": {
                "20013": "cid00001",  # 中
                "22269": "cid00002",  # 国
                "20154": "cid00003",  # 人
                "25991": "cid00004",  # 文
                "34892": "cid00005",  # 行
            },
            "other_data": {"ignored": "data"},
        }

        template_path = Path("/mock/template.json")

        with patch("pathlib.Path.exists", return_value=True), patch(
            "builtins.open", mock_open()
        ), patch("orjson.loads", return_value=mock_json_data):

            # Create data source and manager
            source = JsonCmapDataSource(template_path)
            manager = MappingDataManager(cmap_source=source)

            # Test character to CID conversion
            assert manager.convert_hanzi_to_cid("中") == "cid00001"
            assert manager.convert_hanzi_to_cid("国") == "cid00002"
            assert manager.convert_hanzi_to_cid("人") == "cid00003"
            assert manager.convert_hanzi_to_cid("不") is None

            # Test reverse lookup
            assert manager.get_character_from_cid("cid00001") == "中"
            assert manager.get_character_from_cid("cid00002") == "国"
            assert manager.get_character_from_cid("nonexistent") is None

            # Test character availability
            test_chars = ["中", "国", "人", "不", "也"]
            available = manager.get_available_characters(test_chars)
            missing = manager.get_missing_characters(test_chars)

            assert len(available) == 3
            assert len(missing) == 2
            assert "中" in available
            assert "国" in available
            assert "人" in available
            assert "不" in missing
            assert "也" in missing

            # Test statistics
            stats = manager.get_glyph_statistics()
            assert stats["total_glyphs"] == 5
            assert stats["unicode_range_start"] == 20013
            assert stats["unicode_range_end"] == 34892

    @pytest.mark.unit
    def test_error_handling_integration(self):
        """Test error handling in integration scenarios."""
        # Test with malformed JSON
        template_path = Path("/mock/template.json")

        with patch("pathlib.Path.exists", return_value=True), patch(
            "builtins.open", mock_open()
        ), patch("orjson.loads", side_effect=ValueError("Invalid JSON")):

            source = JsonCmapDataSource(template_path)
            manager = MappingDataManager(cmap_source=source)

            with pytest.raises(ValueError):
                manager.get_cmap_table()

    @pytest.mark.unit
    def test_performance_characteristics(self):
        """Test performance characteristics of the system."""
        # Test with large dataset
        large_cmap_data = {str(0x4E00 + i): f"cid{i:05d}" for i in range(10000)}

        mock_json_data = {"cmap": large_cmap_data}
        template_path = Path("/mock/template.json")

        with patch("pathlib.Path.exists", return_value=True), patch(
            "builtins.open", mock_open()
        ), patch("orjson.loads", return_value=mock_json_data):

            source = JsonCmapDataSource(template_path)
            manager = MappingDataManager(cmap_source=source)

            # Test that large dataset loads correctly
            stats = manager.get_glyph_statistics()
            assert stats["total_glyphs"] == 10000

            # Test performance of lookups
            char = chr(0x4E00)
            result = manager.convert_hanzi_to_cid(char)
            assert result == "cid00000"

            # Test caching behavior
            result2 = manager.convert_hanzi_to_cid(char)
            assert result == result2

    @pytest.mark.unit
    def test_unicode_edge_cases(self):
        """Test Unicode edge cases."""
        # Test with various Unicode ranges
        mock_cmap_data = {
            "65": "cid00001",  # ASCII 'A'
            "12354": "cid00002",  # Hiragana あ
            "12450": "cid00003",  # Katakana ア
            "20013": "cid00004",  # CJK 中
            "127744": "cid00005",  # Emoji range
        }

        mock_json_data = {"cmap": mock_cmap_data}
        template_path = Path("/mock/template.json")

        with patch("pathlib.Path.exists", return_value=True), patch(
            "builtins.open", mock_open()
        ), patch("orjson.loads", return_value=mock_json_data):

            source = JsonCmapDataSource(template_path)
            manager = MappingDataManager(cmap_source=source)

            # Test different Unicode ranges
            assert manager.convert_hanzi_to_cid("A") == "cid00001"
            assert manager.convert_hanzi_to_cid("あ") == "cid00002"
            assert manager.convert_hanzi_to_cid("ア") == "cid00003"
            assert manager.convert_hanzi_to_cid("中") == "cid00004"
            assert manager.convert_hanzi_to_cid("🌀") == "cid00005"

            # Test reverse lookup
            assert manager.get_character_from_cid("cid00001") == "A"
            assert manager.get_character_from_cid("cid00002") == "あ"
            assert manager.get_character_from_cid("cid00003") == "ア"
            assert manager.get_character_from_cid("cid00004") == "中"
            assert manager.get_character_from_cid("cid00005") == "🌀"
