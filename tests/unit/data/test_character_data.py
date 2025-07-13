# -*- coding: utf-8 -*-
"""
Tests for character data management and classification.

These tests verify that the character data system works correctly
with proper classification, iteration, and statistics.
"""

from unittest.mock import Mock

import pytest

from refactored.data.character_data import (
    CharacterClassifier,
    CharacterDataManager,
    CharacterInfo,
    MultiplePronunciationClassifier,
    SinglePronunciationClassifier,
    get_default_character_manager,
)
from refactored.data.pinyin_data import PinyinDataManager


class TestCharacterInfo:
    """Test CharacterInfo dataclass functionality."""

    @pytest.mark.unit
    def test_character_info_creation(self):
        """Test CharacterInfo creation and basic properties."""
        char_info = CharacterInfo(character="中", pronunciations=["zhōng", "zhòng"])

        assert char_info.character == "中"
        assert char_info.pronunciations == ["zhōng", "zhòng"]
        assert char_info.pronunciation_count == 2
        assert char_info.is_multiple_pronunciation is True
        assert char_info.is_single_pronunciation is False

    @pytest.mark.unit
    def test_character_info_single_pronunciation(self):
        """Test CharacterInfo with single pronunciation."""
        char_info = CharacterInfo(character="国", pronunciations=["guó"])

        assert char_info.character == "国"
        assert char_info.pronunciations == ["guó"]
        assert char_info.pronunciation_count == 1
        assert char_info.is_single_pronunciation is True
        assert char_info.is_multiple_pronunciation is False

    @pytest.mark.unit
    def test_character_info_empty_pronunciations(self):
        """Test CharacterInfo with empty pronunciations."""
        char_info = CharacterInfo(character="？", pronunciations=[])

        assert char_info.character == "？"
        assert char_info.pronunciations == []
        assert char_info.pronunciation_count == 0
        assert char_info.is_single_pronunciation is False
        assert char_info.is_multiple_pronunciation is False

    @pytest.mark.unit
    def test_character_info_iteration(self):
        """Test CharacterInfo iteration (backward compatibility)."""
        char_info = CharacterInfo(character="中", pronunciations=["zhōng", "zhòng"])

        # Test tuple unpacking
        char, pronunciations = char_info
        assert char == "中"
        assert pronunciations == ["zhōng", "zhòng"]

        # Test explicit iteration
        items = list(char_info)
        assert items == ["中", ["zhōng", "zhòng"]]

    @pytest.mark.unit
    def test_character_info_indexing(self):
        """Test CharacterInfo indexing (backward compatibility)."""
        char_info = CharacterInfo(character="中", pronunciations=["zhōng", "zhòng"])

        assert char_info[0] == "中"
        assert char_info[1] == ["zhōng", "zhòng"]

        with pytest.raises(IndexError):
            char_info[2]

    @pytest.mark.unit
    def test_character_info_immutability(self):
        """Test that CharacterInfo is immutable."""
        char_info = CharacterInfo(character="中", pronunciations=["zhōng", "zhòng"])

        # Should not be able to modify attributes
        with pytest.raises(AttributeError):
            char_info.character = "国"

        with pytest.raises(AttributeError):
            char_info.pronunciations = ["guó"]


class TestCharacterClassifiers:
    """Test character classifier functionality."""

    @pytest.mark.unit
    def test_single_pronunciation_classifier(self):
        """Test SinglePronunciationClassifier."""
        classifier = SinglePronunciationClassifier()

        single_char = CharacterInfo(character="国", pronunciations=["guó"])
        multiple_char = CharacterInfo(character="中", pronunciations=["zhōng", "zhòng"])
        empty_char = CharacterInfo(character="？", pronunciations=[])

        assert classifier.classify_character(single_char) is True
        assert classifier.classify_character(multiple_char) is False
        assert classifier.classify_character(empty_char) is False

    @pytest.mark.unit
    def test_multiple_pronunciation_classifier(self):
        """Test MultiplePronunciationClassifier."""
        classifier = MultiplePronunciationClassifier()

        single_char = CharacterInfo(character="国", pronunciations=["guó"])
        multiple_char = CharacterInfo(character="中", pronunciations=["zhōng", "zhòng"])
        three_pronunciations = CharacterInfo(
            character="行", pronunciations=["xíng", "háng", "hàng"]
        )

        assert classifier.classify_character(single_char) is False
        assert classifier.classify_character(multiple_char) is True
        assert classifier.classify_character(three_pronunciations) is True

    @pytest.mark.unit
    def test_custom_classifier(self):
        """Test custom classifier implementation."""

        class HasSpecificPronunciationClassifier:
            def __init__(self, target_pronunciation: str):
                self.target_pronunciation = target_pronunciation

            def classify_character(self, char_info: CharacterInfo) -> bool:
                return self.target_pronunciation in char_info.pronunciations

        classifier = HasSpecificPronunciationClassifier("zhōng")

        with_zhong = CharacterInfo(character="中", pronunciations=["zhōng", "zhòng"])
        without_zhong = CharacterInfo(character="国", pronunciations=["guó"])

        assert classifier.classify_character(with_zhong) is True
        assert classifier.classify_character(without_zhong) is False


class TestCharacterDataManager:
    """Test CharacterDataManager functionality."""

    @pytest.mark.unit
    def test_character_data_manager_initialization(self):
        """Test CharacterDataManager initialization."""
        # Test with default pinyin manager
        manager = CharacterDataManager()
        assert manager is not None
        assert manager._pinyin_manager is not None

        # Test with custom pinyin manager
        custom_pinyin_manager = Mock(spec=PinyinDataManager)
        manager = CharacterDataManager(pinyin_manager=custom_pinyin_manager)
        assert manager._pinyin_manager is custom_pinyin_manager

    @pytest.mark.unit
    def test_get_character_info_found(self):
        """Test get_character_info with existing character."""
        mock_pinyin_manager = Mock(spec=PinyinDataManager)
        mock_pinyin_manager.get_pinyin.return_value = ["zhōng", "zhòng"]

        manager = CharacterDataManager(pinyin_manager=mock_pinyin_manager)
        result = manager.get_character_info("中")

        assert result is not None
        assert result.character == "中"
        assert result.pronunciations == ["zhōng", "zhòng"]
        assert result.is_multiple_pronunciation is True
        mock_pinyin_manager.get_pinyin.assert_called_once_with("中")

    @pytest.mark.unit
    def test_get_character_info_not_found(self):
        """Test get_character_info with non-existing character."""
        mock_pinyin_manager = Mock(spec=PinyinDataManager)
        mock_pinyin_manager.get_pinyin.return_value = None

        manager = CharacterDataManager(pinyin_manager=mock_pinyin_manager)
        result = manager.get_character_info("不存在")

        assert result is None
        mock_pinyin_manager.get_pinyin.assert_called_once_with("不存在")

    @pytest.mark.unit
    def test_iter_all_characters(self):
        """Test iter_all_characters functionality."""
        mock_pinyin_manager = Mock(spec=PinyinDataManager)
        mock_data = {"中": ["zhōng", "zhòng"], "国": ["guó"], "人": ["rén"]}
        mock_pinyin_manager.get_all_mappings.return_value = mock_data

        manager = CharacterDataManager(pinyin_manager=mock_pinyin_manager)
        chars = list(manager.iter_all_characters())

        assert len(chars) == 3
        char_dict = {char.character: char.pronunciations for char in chars}
        assert char_dict == mock_data
        mock_pinyin_manager.get_all_mappings.assert_called_once()

    @pytest.mark.unit
    def test_iter_characters_by_classifier(self):
        """Test iter_characters_by_classifier functionality."""
        mock_pinyin_manager = Mock(spec=PinyinDataManager)
        mock_data = {
            "中": ["zhōng", "zhòng"],  # Multiple
            "国": ["guó"],  # Single
            "人": ["rén"],  # Single
            "行": ["xíng", "háng"],  # Multiple
        }
        mock_pinyin_manager.get_all_mappings.return_value = mock_data

        manager = CharacterDataManager(pinyin_manager=mock_pinyin_manager)
        classifier = SinglePronunciationClassifier()

        single_chars = list(manager.iter_characters_by_classifier(classifier))

        assert len(single_chars) == 2
        single_char_names = [char.character for char in single_chars]
        assert "国" in single_char_names
        assert "人" in single_char_names
        assert "中" not in single_char_names
        assert "行" not in single_char_names

    @pytest.mark.unit
    def test_iter_single_pronunciation_characters(self):
        """Test iter_single_pronunciation_characters functionality."""
        mock_pinyin_manager = Mock(spec=PinyinDataManager)
        mock_data = {
            "中": ["zhōng", "zhòng"],  # Multiple
            "国": ["guó"],  # Single
            "人": ["rén"],  # Single
        }
        mock_pinyin_manager.get_all_mappings.return_value = mock_data

        manager = CharacterDataManager(pinyin_manager=mock_pinyin_manager)
        single_chars = list(manager.iter_single_pronunciation_characters())

        assert len(single_chars) == 2
        single_char_names = [char.character for char in single_chars]
        assert "国" in single_char_names
        assert "人" in single_char_names
        assert "中" not in single_char_names

    @pytest.mark.unit
    def test_iter_multiple_pronunciation_characters(self):
        """Test iter_multiple_pronunciation_characters functionality."""
        mock_pinyin_manager = Mock(spec=PinyinDataManager)
        mock_data = {
            "中": ["zhōng", "zhòng"],  # Multiple
            "国": ["guó"],  # Single
            "行": ["xíng", "háng"],  # Multiple
        }
        mock_pinyin_manager.get_all_mappings.return_value = mock_data

        manager = CharacterDataManager(pinyin_manager=mock_pinyin_manager)
        multiple_chars = list(manager.iter_multiple_pronunciation_characters())

        assert len(multiple_chars) == 2
        multiple_char_names = [char.character for char in multiple_chars]
        assert "中" in multiple_char_names
        assert "行" in multiple_char_names
        assert "国" not in multiple_char_names

    @pytest.mark.unit
    def test_get_single_pronunciation_characters_cached(self):
        """Test get_single_pronunciation_characters with caching."""
        mock_pinyin_manager = Mock(spec=PinyinDataManager)
        mock_data = {
            "中": ["zhōng", "zhòng"],  # Multiple
            "国": ["guó"],  # Single
            "人": ["rén"],  # Single
        }
        mock_pinyin_manager.get_all_mappings.return_value = mock_data

        manager = CharacterDataManager(pinyin_manager=mock_pinyin_manager)

        # First call
        result1 = manager.get_single_pronunciation_characters()
        assert len(result1) == 2

        # Second call - should use cache
        result2 = manager.get_single_pronunciation_characters()
        assert len(result2) == 2
        assert result1 is result2  # Should be the same object due to caching

        # get_all_mappings should only be called once due to caching
        mock_pinyin_manager.get_all_mappings.assert_called_once()

    @pytest.mark.unit
    def test_get_multiple_pronunciation_characters_cached(self):
        """Test get_multiple_pronunciation_characters with caching."""
        mock_pinyin_manager = Mock(spec=PinyinDataManager)
        mock_data = {
            "中": ["zhōng", "zhòng"],  # Multiple
            "国": ["guó"],  # Single
            "行": ["xíng", "háng"],  # Multiple
        }
        mock_pinyin_manager.get_all_mappings.return_value = mock_data

        manager = CharacterDataManager(pinyin_manager=mock_pinyin_manager)

        # First call
        result1 = manager.get_multiple_pronunciation_characters()
        assert len(result1) == 2

        # Second call - should use cache
        result2 = manager.get_multiple_pronunciation_characters()
        assert len(result2) == 2
        assert result1 is result2  # Should be the same object due to caching

    @pytest.mark.unit
    def test_get_statistics(self):
        """Test get_statistics functionality."""
        mock_pinyin_manager = Mock(spec=PinyinDataManager)
        mock_data = {
            "中": ["zhōng", "zhòng"],  # Multiple
            "国": ["guó"],  # Single
            "人": ["rén"],  # Single
            "行": ["xíng", "háng"],  # Multiple
        }
        mock_pinyin_manager.get_all_mappings.return_value = mock_data

        manager = CharacterDataManager(pinyin_manager=mock_pinyin_manager)
        stats = manager.get_statistics()

        assert stats["total_characters"] == 4
        assert stats["single_pronunciation"] == 2
        assert stats["multiple_pronunciation"] == 2
        assert stats["homograph_percentage"] == 50.0

    @pytest.mark.unit
    def test_get_statistics_empty_data(self):
        """Test get_statistics with empty data."""
        mock_pinyin_manager = Mock(spec=PinyinDataManager)
        mock_pinyin_manager.get_all_mappings.return_value = {}

        manager = CharacterDataManager(pinyin_manager=mock_pinyin_manager)
        stats = manager.get_statistics()

        assert stats["total_characters"] == 0
        assert stats["single_pronunciation"] == 0
        assert stats["multiple_pronunciation"] == 0
        assert stats["homograph_percentage"] == 0

    @pytest.mark.unit
    def test_get_statistics_all_single_pronunciations(self):
        """Test get_statistics with all single pronunciations."""
        mock_pinyin_manager = Mock(spec=PinyinDataManager)
        mock_data = {"国": ["guó"], "人": ["rén"], "文": ["wén"]}
        mock_pinyin_manager.get_all_mappings.return_value = mock_data

        manager = CharacterDataManager(pinyin_manager=mock_pinyin_manager)
        stats = manager.get_statistics()

        assert stats["total_characters"] == 3
        assert stats["single_pronunciation"] == 3
        assert stats["multiple_pronunciation"] == 0
        assert stats["homograph_percentage"] == 0.0


class TestGlobalFunctions:
    """Test global utility functions."""

    @pytest.mark.unit
    def test_get_default_character_manager(self):
        """Test get_default_character_manager functionality."""
        # Clear any existing global instance
        import refactored.data.character_data

        refactored.data.character_data._default_character_manager = None

        # First call should create instance
        manager1 = get_default_character_manager()
        assert manager1 is not None
        assert isinstance(manager1, CharacterDataManager)

        # Second call should return same instance
        manager2 = get_default_character_manager()
        assert manager1 is manager2


class TestCharacterDataIntegration:
    """Integration tests for character data components."""

    @pytest.mark.unit
    def test_full_character_data_integration(self):
        """Test full integration of character data components."""
        # Create mock pinyin manager with comprehensive data
        mock_pinyin_manager = Mock(spec=PinyinDataManager)
        mock_data = {
            "中": ["zhōng", "zhòng"],  # Multiple (2)
            "国": ["guó"],  # Single
            "人": ["rén"],  # Single
            "行": ["xíng", "háng"],  # Multiple (2)
            "了": ["le", "liǎo"],  # Multiple (2)
            "不": ["bù", "bú"],  # Multiple (2)
            "上": ["shàng"],  # Single
            "下": ["xià"],  # Single
            "大": ["dà"],  # Single
            "小": ["xiǎo"],  # Single
        }
        mock_pinyin_manager.get_all_mappings.return_value = mock_data

        # Create character data manager
        manager = CharacterDataManager(pinyin_manager=mock_pinyin_manager)

        # Configure mock to return specific values for specific characters
        def mock_get_pinyin(character):
            return mock_data.get(character)

        mock_pinyin_manager.get_pinyin.side_effect = mock_get_pinyin

        # Test individual character info
        zhong_info = manager.get_character_info("中")
        assert zhong_info.character == "中"
        assert zhong_info.is_multiple_pronunciation is True
        assert zhong_info.pronunciation_count == 2

        guo_info = manager.get_character_info("国")
        assert guo_info.character == "国"
        assert guo_info.is_single_pronunciation is True
        assert guo_info.pronunciation_count == 1

        # Test classification
        single_chars = list(manager.iter_single_pronunciation_characters())
        multiple_chars = list(manager.iter_multiple_pronunciation_characters())

        assert len(single_chars) == 6  # 国,人,上,下,大,小
        assert len(multiple_chars) == 4  # 中,行,了,不

        # Test statistics
        stats = manager.get_statistics()
        assert stats["total_characters"] == 10
        assert stats["single_pronunciation"] == 6
        assert stats["multiple_pronunciation"] == 4
        assert stats["homograph_percentage"] == 40.0

        # Test that all characters are accounted for
        all_chars = list(manager.iter_all_characters())
        assert len(all_chars) == 10

        # Verify no duplicates
        char_names = [char.character for char in all_chars]
        assert len(char_names) == len(set(char_names))

    @pytest.mark.unit
    def test_character_info_backward_compatibility(self):
        """Test backward compatibility of CharacterInfo."""
        # Test that CharacterInfo can be used like the old tuple format
        char_info = CharacterInfo(character="中", pronunciations=["zhōng", "zhòng"])

        # Test tuple unpacking (old code pattern)
        character, pronunciations = char_info
        assert character == "中"
        assert pronunciations == ["zhōng", "zhòng"]

        # Test index access (old code pattern)
        assert char_info[0] == "中"
        assert char_info[1] == ["zhōng", "zhòng"]

        # Test iteration (old code pattern)
        items = list(char_info)
        assert len(items) == 2
        assert items[0] == "中"
        assert items[1] == ["zhōng", "zhòng"]

    @pytest.mark.unit
    def test_memory_efficiency(self):
        """Test memory efficiency of iterator-based approach."""
        # Create mock with large dataset
        mock_pinyin_manager = Mock(spec=PinyinDataManager)
        large_data = {f"char_{i}": [f"pin_{i}"] for i in range(10000)}
        mock_pinyin_manager.get_all_mappings.return_value = large_data

        manager = CharacterDataManager(pinyin_manager=mock_pinyin_manager)

        # Test that iterator doesn't load all data at once
        iterator = manager.iter_all_characters()

        # Get first few items
        first_items = []
        for i, char_info in enumerate(iterator):
            first_items.append(char_info)
            if i >= 2:  # Only get first 3 items
                break

        assert len(first_items) == 3
        # Iterator should work without loading all 10k items into memory
        # (This is more of a design verification than a strict test)

    @pytest.mark.unit
    def test_error_handling_robustness(self):
        """Test error handling in various scenarios."""
        # Test with pinyin manager that raises exceptions
        mock_pinyin_manager = Mock(spec=PinyinDataManager)
        mock_pinyin_manager.get_pinyin.side_effect = Exception("Network error")

        manager = CharacterDataManager(pinyin_manager=mock_pinyin_manager)

        # Should handle exceptions gracefully
        with pytest.raises(Exception):
            manager.get_character_info("中")

        # Test with empty results
        mock_pinyin_manager.get_pinyin.side_effect = None
        mock_pinyin_manager.get_pinyin.return_value = []

        char_info = manager.get_character_info("中")
        assert char_info is not None
        assert char_info.pronunciation_count == 0
        assert char_info.is_single_pronunciation is False
        assert char_info.is_multiple_pronunciation is False
