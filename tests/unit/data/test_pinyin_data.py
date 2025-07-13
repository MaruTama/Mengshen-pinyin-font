# -*- coding: utf-8 -*-
"""
Tests for pinyin data management.

These tests verify that the pinyin data system works correctly
with proper caching, multiple data sources, and backward compatibility.
"""

from unittest.mock import Mock, mock_open, patch

import pytest

from refactored.config import ProjectPaths
from refactored.data.pinyin_data import (
    OfflinePinyinDataSource,
    PinyinDataManager,
    PinyinDataSource,
    get_default_pinyin_manager,
    get_pinyin_table_with_mapping_table,
)


class TestPinyinDataManager:
    """Test PinyinDataManager functionality."""

    @pytest.mark.unit
    def test_pinyin_data_manager_initialization(self):
        """Test PinyinDataManager initialization."""
        # Test with default data source
        manager = PinyinDataManager()
        assert manager is not None
        assert isinstance(manager._data_source, OfflinePinyinDataSource)

        # Test with custom data source
        mock_source = Mock(spec=PinyinDataSource)
        manager = PinyinDataManager(data_source=mock_source)
        assert manager._data_source is mock_source

    @pytest.mark.unit
    def test_get_pinyin_with_mock_data(self):
        """Test get_pinyin with mock data source."""
        # Create mock data source
        mock_source = Mock(spec=PinyinDataSource)
        mock_source.get_pinyin.return_value = ["zhōng", "zhòng"]

        manager = PinyinDataManager(data_source=mock_source)
        result = manager.get_pinyin("中")

        assert result == ["zhōng", "zhòng"]
        mock_source.get_pinyin.assert_called_once_with("中")

    @pytest.mark.unit
    def test_get_pinyin_with_none_result(self):
        """Test get_pinyin when character not found."""
        mock_source = Mock(spec=PinyinDataSource)
        mock_source.get_pinyin.return_value = None

        manager = PinyinDataManager(data_source=mock_source)
        result = manager.get_pinyin("不存在")

        assert result is None
        mock_source.get_pinyin.assert_called_once_with("不存在")

    @pytest.mark.unit
    def test_get_all_mappings(self):
        """Test get_all_mappings functionality."""
        mock_source = Mock(spec=PinyinDataSource)
        mock_data = {"中": ["zhōng", "zhòng"], "国": ["guó"], "人": ["rén"]}
        mock_source.get_all_mappings.return_value = mock_data

        manager = PinyinDataManager(data_source=mock_source)
        result = manager.get_all_mappings()

        assert result == mock_data
        mock_source.get_all_mappings.assert_called_once()

    @pytest.mark.unit
    def test_has_multiple_pronunciations(self):
        """Test has_multiple_pronunciations functionality."""
        mock_source = Mock(spec=PinyinDataSource)

        # Test character with multiple pronunciations
        mock_source.get_pinyin.return_value = ["zhōng", "zhòng"]
        manager = PinyinDataManager(data_source=mock_source)
        assert manager.has_multiple_pronunciations("中") is True

        # Test character with single pronunciation
        mock_source.get_pinyin.return_value = ["guó"]
        assert manager.has_multiple_pronunciations("国") is False

        # Test character not found
        mock_source.get_pinyin.return_value = None
        assert manager.has_multiple_pronunciations("不存在") is False

    @pytest.mark.unit
    def test_has_single_pronunciation(self):
        """Test has_single_pronunciation functionality."""
        mock_source = Mock(spec=PinyinDataSource)

        # Test character with single pronunciation
        mock_source.get_pinyin.return_value = ["guó"]
        manager = PinyinDataManager(data_source=mock_source)
        assert manager.has_single_pronunciation("国") is True

        # Test character with multiple pronunciations
        mock_source.get_pinyin.return_value = ["zhōng", "zhòng"]
        assert manager.has_single_pronunciation("中") is False

        # Test character not found
        mock_source.get_pinyin.return_value = None
        assert manager.has_single_pronunciation("不存在") is False

    @pytest.mark.unit
    def test_get_character_count(self):
        """Test get_character_count functionality."""
        mock_source = Mock(spec=PinyinDataSource)
        mock_data = {"中": ["zhōng", "zhòng"], "国": ["guó"], "人": ["rén"]}
        mock_source.get_all_mappings.return_value = mock_data

        manager = PinyinDataManager(data_source=mock_source)
        result = manager.get_character_count()

        assert result == 3
        mock_source.get_all_mappings.assert_called_once()

    @pytest.mark.unit
    def test_get_homograph_count(self):
        """Test get_homograph_count functionality."""
        mock_source = Mock(spec=PinyinDataSource)
        mock_data = {
            "中": ["zhōng", "zhòng"],  # Multiple pronunciations
            "国": ["guó"],  # Single pronunciation
            "人": ["rén"],  # Single pronunciation
            "行": ["xíng", "háng"],  # Multiple pronunciations
        }
        mock_source.get_all_mappings.return_value = mock_data

        manager = PinyinDataManager(data_source=mock_source)
        result = manager.get_homograph_count()

        assert result == 2  # 中 and 行 have multiple pronunciations
        mock_source.get_all_mappings.assert_called_once()

    @pytest.mark.unit
    def test_caching_behavior(self):
        """Test that caching works correctly."""
        mock_source = Mock(spec=PinyinDataSource)
        mock_source.get_pinyin.return_value = ["zhōng", "zhòng"]

        manager = PinyinDataManager(data_source=mock_source)

        # First call
        result1 = manager.get_pinyin("中")
        assert result1 == ["zhōng", "zhòng"]

        # Second call - should use cache
        result2 = manager.get_pinyin("中")
        assert result2 == ["zhōng", "zhòng"]

        # Mock should only be called once due to caching
        mock_source.get_pinyin.assert_called_once_with("中")


class TestOfflinePinyinDataSource:
    """Test OfflinePinyinDataSource functionality."""

    @pytest.mark.unit
    def test_offline_data_source_initialization(self):
        """Test OfflinePinyinDataSource initialization."""
        # Test with default paths
        source = OfflinePinyinDataSource()
        assert source.paths is not None
        assert isinstance(source.paths, ProjectPaths)
        assert source._data is None

        # Test with custom paths
        custom_paths = ProjectPaths()
        source = OfflinePinyinDataSource(paths=custom_paths)
        assert source.paths is custom_paths

    @pytest.mark.unit
    def test_load_data_missing_file(self):
        """Test _load_data when mapping file is missing."""
        mock_paths = Mock(spec=ProjectPaths)
        mock_file = Mock()
        mock_file.exists.return_value = False
        mock_paths.get_output_path.return_value = mock_file

        source = OfflinePinyinDataSource(paths=mock_paths)

        with pytest.raises(FileNotFoundError, match="Merged mapping table not found"):
            source._load_data()

    @pytest.mark.unit
    def test_load_data_with_valid_file(self):
        """Test _load_data with valid mapping file."""
        # Mock file content
        file_content = """# Test pinyin mapping file
U+4E2D: zhōng,zhòng  # 中
U+56FD: guó  # 国
U+4EBA: rén  # 人

# Empty line above should be ignored
U+884C: xíng,háng  # 行
"""

        mock_paths = Mock(spec=ProjectPaths)
        mock_file = Mock()
        mock_file.exists.return_value = True
        mock_paths.get_output_path.return_value = mock_file

        source = OfflinePinyinDataSource(paths=mock_paths)

        with patch("builtins.open", mock_open(read_data=file_content)):
            source._load_data()

        # Verify data was loaded correctly
        assert source._data is not None
        assert len(source._data) == 4
        assert source._data["中"] == ["zhōng", "zhòng"]
        assert source._data["国"] == ["guó"]
        assert source._data["人"] == ["rén"]
        assert source._data["行"] == ["xíng", "háng"]

    @pytest.mark.unit
    def test_load_data_with_invalid_lines(self):
        """Test _load_data with invalid lines."""
        file_content = """# Valid lines
U+4E2D: zhōng,zhòng  # 中
Invalid line without colon
U+56FD  # Missing colon
U+4EBA: rén  # 人
"""

        mock_paths = Mock(spec=ProjectPaths)
        mock_file = Mock()
        mock_file.exists.return_value = True
        mock_paths.get_output_path.return_value = mock_file

        source = OfflinePinyinDataSource(paths=mock_paths)

        with patch("builtins.open", mock_open(read_data=file_content)):
            source._load_data()

        # Should only load valid lines
        assert len(source._data) == 2
        assert source._data["中"] == ["zhōng", "zhòng"]
        assert source._data["人"] == ["rén"]

    @pytest.mark.unit
    def test_get_pinyin_functionality(self):
        """Test get_pinyin with loaded data."""
        file_content = "U+4E2D: zhōng,zhòng  # 中\nU+56FD: guó  # 国\n"

        mock_paths = Mock(spec=ProjectPaths)
        mock_file = Mock()
        mock_file.exists.return_value = True
        mock_paths.get_output_path.return_value = mock_file

        source = OfflinePinyinDataSource(paths=mock_paths)

        with patch("builtins.open", mock_open(read_data=file_content)):
            result = source.get_pinyin("中")
            assert result == ["zhōng", "zhòng"]

            result = source.get_pinyin("国")
            assert result == ["guó"]

            result = source.get_pinyin("不存在")
            assert result is None

    @pytest.mark.unit
    def test_get_all_mappings_functionality(self):
        """Test get_all_mappings with loaded data."""
        file_content = "U+4E2D: zhōng,zhòng  # 中\nU+56FD: guó  # 国\n"

        mock_paths = Mock(spec=ProjectPaths)
        mock_file = Mock()
        mock_file.exists.return_value = True
        mock_paths.get_output_path.return_value = mock_file

        source = OfflinePinyinDataSource(paths=mock_paths)

        with patch("builtins.open", mock_open(read_data=file_content)):
            result = source.get_all_mappings()

            assert len(result) == 2
            assert result["中"] == ["zhōng", "zhòng"]
            assert result["国"] == ["guó"]

            # Verify it returns a copy
            result["中"] = ["modified"]
            result2 = source.get_all_mappings()
            assert result2["中"] == ["zhōng", "zhòng"]  # Should not be modified

    @pytest.mark.unit
    def test_lazy_loading(self):
        """Test that data is loaded lazily."""
        mock_paths = Mock(spec=ProjectPaths)
        mock_file = Mock()
        mock_file.exists.return_value = True
        mock_paths.get_output_path.return_value = mock_file

        source = OfflinePinyinDataSource(paths=mock_paths)

        # Initially, data should not be loaded
        assert source._data is None

        # Mock the file opening
        with patch("builtins.open", mock_open(read_data="U+4E2D: zhōng  # 中\n")):
            # First call should load data
            result = source.get_pinyin("中")
            assert result == ["zhōng"]
            assert source._data is not None

            # Second call should not reload data
            result2 = source.get_pinyin("中")
            assert result2 == ["zhōng"]
            # The mock should only be called once
            mock_paths.get_output_path.assert_called_once()


class TestGlobalFunctions:
    """Test global utility functions."""

    @pytest.mark.unit
    def test_get_default_pinyin_manager(self):
        """Test get_default_pinyin_manager functionality."""
        # Clear any existing global instance
        import refactored.data.pinyin_data

        refactored.data.pinyin_data._default_manager = None

        # First call should create instance
        manager1 = get_default_pinyin_manager()
        assert manager1 is not None
        assert isinstance(manager1, PinyinDataManager)

        # Second call should return same instance
        manager2 = get_default_pinyin_manager()
        assert manager1 is manager2

    @pytest.mark.unit
    def test_get_pinyin_table_with_mapping_table(self):
        """Test backward compatibility function."""
        # This function should delegate to the default manager
        with patch(
            "refactored.data.pinyin_data.get_default_pinyin_manager"
        ) as mock_get_manager:
            mock_manager = Mock(spec=PinyinDataManager)
            mock_data = {"中": ["zhōng", "zhòng"]}
            mock_manager.get_all_mappings.return_value = mock_data
            mock_get_manager.return_value = mock_manager

            result = get_pinyin_table_with_mapping_table()

            assert result == mock_data
            mock_get_manager.assert_called_once()
            mock_manager.get_all_mappings.assert_called_once()


class TestPinyinDataIntegration:
    """Integration tests for pinyin data components."""

    @pytest.mark.unit
    def test_full_integration_with_mock_file(self):
        """Test full integration with mock file data."""
        file_content = """# Integration test data
U+4E2D: zhōng,zhòng  # 中 - multiple pronunciations
U+56FD: guó  # 国 - single pronunciation
U+4EBA: rén  # 人 - single pronunciation
U+884C: xíng,háng  # 行 - multiple pronunciations
"""

        mock_paths = Mock(spec=ProjectPaths)
        mock_file = Mock()
        mock_file.exists.return_value = True
        mock_paths.get_output_path.return_value = mock_file

        with patch("builtins.open", mock_open(read_data=file_content)):
            # Create data source and manager
            source = OfflinePinyinDataSource(paths=mock_paths)
            manager = PinyinDataManager(data_source=source)

            # Test individual character lookups
            assert manager.get_pinyin("中") == ["zhōng", "zhòng"]
            assert manager.get_pinyin("国") == ["guó"]
            assert manager.get_pinyin("人") == ["rén"]
            assert manager.get_pinyin("行") == ["xíng", "háng"]
            assert manager.get_pinyin("不存在") is None

            # Test multiple/single pronunciation checks
            assert manager.has_multiple_pronunciations("中") is True
            assert manager.has_multiple_pronunciations("国") is False
            assert manager.has_single_pronunciation("国") is True
            assert manager.has_single_pronunciation("中") is False

            # Test count functions
            assert manager.get_character_count() == 4
            assert manager.get_homograph_count() == 2  # 中 and 行

            # Test get_all_mappings
            all_mappings = manager.get_all_mappings()
            assert len(all_mappings) == 4
            assert all_mappings["中"] == ["zhōng", "zhòng"]

    @pytest.mark.unit
    def test_error_handling_integration(self):
        """Test error handling in integration scenarios."""
        # Test with missing file
        mock_paths = Mock(spec=ProjectPaths)
        mock_file = Mock()
        mock_file.exists.return_value = False
        mock_paths.get_output_path.return_value = mock_file

        source = OfflinePinyinDataSource(paths=mock_paths)
        manager = PinyinDataManager(data_source=source)

        with pytest.raises(FileNotFoundError):
            manager.get_pinyin("中")

        # Test with corrupted file
        mock_file.exists.return_value = True

        with patch("builtins.open", mock_open(read_data="corrupted file content")):
            result = manager.get_pinyin("中")
            assert result is None  # Should handle gracefully

    @pytest.mark.unit
    def test_performance_characteristics(self):
        """Test performance characteristics of the system."""
        # Test with large dataset
        large_file_content = "\n".join(
            [f"U+{0x4E00+i:04X}: pin{i}  # {chr(0x4E00+i)}" for i in range(1000)]
        )

        mock_paths = Mock(spec=ProjectPaths)
        mock_file = Mock()
        mock_file.exists.return_value = True
        mock_paths.get_output_path.return_value = mock_file

        with patch("builtins.open", mock_open(read_data=large_file_content)):
            source = OfflinePinyinDataSource(paths=mock_paths)
            manager = PinyinDataManager(data_source=source)

            # Test that large dataset loads correctly
            assert manager.get_character_count() == 1000

            # Test caching behavior with multiple calls
            char = chr(0x4E00)
            result1 = manager.get_pinyin(char)
            result2 = manager.get_pinyin(char)
            assert result1 == result2
