# -*- coding: utf-8 -*-
"""
Tests for hanzi_pinyin module.

This module handles Chinese character to pinyin conversion and provides
efficient access to single/multiple pronunciation characters.
Following TDD principles with comprehensive coverage of all pinyin processing functionality.
"""

from unittest.mock import patch

import pytest

from refactored.utils.hanzi_pinyin import (
    PINYIN_MAPPING_TABLE,
    HanziPinyin,
    get_has_multiple_pinyin_hanzi,
    get_has_single_pinyin_hanzi,
    get_multiple_pronunciation_characters,
    get_single_pronunciation_characters,
    iter_all_hanzi_with_filter,
    iter_characters_by_pronunciation_count,
    iter_multiple_pinyin_hanzi,
    iter_multiple_pronunciation_characters,
    iter_single_pinyin_hanzi,
    iter_single_pronunciation_characters,
)


class TestHanziPinyinDataClass:
    """Test HanziPinyin dataclass functionality."""

    @pytest.mark.unit
    def test_dataclass_basic_creation(self):
        """Test basic HanziPinyin dataclass creation."""
        hp = HanziPinyin(character="中", pronunciations=["zhōng", "zhòng"])

        assert hp.character == "中"
        assert hp.pronunciations == ["zhōng", "zhòng"]

    @pytest.mark.unit
    def test_single_pronunciation_property(self):
        """Test is_single_pronunciation property."""
        single_hp = HanziPinyin(character="的", pronunciations=["de"])
        multiple_hp = HanziPinyin(character="中", pronunciations=["zhōng", "zhòng"])

        assert single_hp.is_single_pronunciation is True
        assert multiple_hp.is_single_pronunciation is False

    @pytest.mark.unit
    def test_multiple_pronunciation_property(self):
        """Test is_multiple_pronunciation property."""
        single_hp = HanziPinyin(character="的", pronunciations=["de"])
        multiple_hp = HanziPinyin(character="中", pronunciations=["zhōng", "zhòng"])

        assert single_hp.is_multiple_pronunciation is False
        assert multiple_hp.is_multiple_pronunciation is True

    @pytest.mark.unit
    def test_tuple_unpacking_compatibility(self):
        """Test backward compatibility with tuple unpacking."""
        hp = HanziPinyin(character="行", pronunciations=["xíng", "háng"])

        # Test tuple unpacking
        hanzi, pinyins = hp
        assert hanzi == "行"
        assert pinyins == ["xíng", "háng"]

    @pytest.mark.unit
    def test_index_access_compatibility(self):
        """Test backward compatibility with index access."""
        hp = HanziPinyin(character="好", pronunciations=["hǎo", "hào"])

        # Test index access
        assert hp[0] == "好"
        assert hp[1] == ["hǎo", "hào"]

        # Test index out of range
        with pytest.raises(IndexError):
            _ = hp[2]

    @pytest.mark.unit
    def test_iterator_protocol(self):
        """Test iterator protocol for tuple unpacking."""
        hp = HanziPinyin(character="和", pronunciations=["hé", "hè", "huó"])

        # Test iteration
        items = list(hp)
        assert items == ["和", ["hé", "hè", "huó"]]


class TestHanziPinyinRetrieval:
    """Test hanzi-pinyin data retrieval functions."""

    def _create_mock_mapping_table(self) -> dict:
        """Create mock pinyin mapping table."""
        return {
            "的": ["de"],
            "了": ["le"],
            "中": ["zhōng", "zhòng"],
            "国": ["guó"],
            "行": ["xíng", "háng"],
            "好": ["hǎo", "hào"],
            "和": ["hé", "hè", "huó"],
            "在": ["zài"],
        }

    @pytest.mark.unit
    def test_get_has_single_pinyin_hanzi(self):
        """Test retrieval of characters with single pinyin."""
        with patch(
            "refactored.utils.hanzi_pinyin.PINYIN_MAPPING_TABLE",
            self._create_mock_mapping_table(),
        ):
            # Clear cache
            get_has_single_pinyin_hanzi.cache_clear()

            result = get_has_single_pinyin_hanzi()

            # Should return HanziPinyin objects
            assert all(isinstance(hp, HanziPinyin) for hp in result)

            # Check single pronunciation characters
            single_chars = [hp.character for hp in result]
            assert "的" in single_chars
            assert "了" in single_chars
            assert "国" in single_chars
            assert "在" in single_chars

            # Check multiple pronunciation characters are excluded
            assert "中" not in single_chars
            assert "行" not in single_chars
            assert "好" not in single_chars
            assert "和" not in single_chars

    @pytest.mark.unit
    def test_get_has_multiple_pinyin_hanzi(self):
        """Test retrieval of characters with multiple pinyin."""
        with patch(
            "refactored.utils.hanzi_pinyin.PINYIN_MAPPING_TABLE",
            self._create_mock_mapping_table(),
        ):
            # Clear cache
            get_has_multiple_pinyin_hanzi.cache_clear()

            result = get_has_multiple_pinyin_hanzi()

            # Should return HanziPinyin objects
            assert all(isinstance(hp, HanziPinyin) for hp in result)

            # Check multiple pronunciation characters
            multi_chars = [hp.character for hp in result]
            assert "中" in multi_chars
            assert "行" in multi_chars
            assert "好" in multi_chars
            assert "和" in multi_chars

            # Check single pronunciation characters are excluded
            assert "的" not in multi_chars
            assert "了" not in multi_chars
            assert "国" not in multi_chars
            assert "在" not in multi_chars

    @pytest.mark.unit
    def test_get_single_pronunciation_characters(self):
        """Test modern version of single pronunciation retrieval."""
        with patch(
            "refactored.utils.hanzi_pinyin.PINYIN_MAPPING_TABLE",
            self._create_mock_mapping_table(),
        ):
            result = get_single_pronunciation_characters()

            # Should return HanziPinyin objects
            assert all(isinstance(hp, HanziPinyin) for hp in result)

            # Check results are all single pronunciation
            for hp in result:
                assert hp.is_single_pronunciation
                assert len(hp.pronunciations) == 1

    @pytest.mark.unit
    def test_get_multiple_pronunciation_characters(self):
        """Test modern version of multiple pronunciation retrieval."""
        with patch(
            "refactored.utils.hanzi_pinyin.PINYIN_MAPPING_TABLE",
            self._create_mock_mapping_table(),
        ):
            result = get_multiple_pronunciation_characters()

            # Should return HanziPinyin objects
            assert all(isinstance(hp, HanziPinyin) for hp in result)

            # Check results are all multiple pronunciation
            for hp in result:
                assert hp.is_multiple_pronunciation
                assert len(hp.pronunciations) > 1

    @pytest.mark.unit
    def test_caching_behavior(self):
        """Test LRU cache behavior for performance functions."""
        with patch(
            "refactored.utils.hanzi_pinyin.PINYIN_MAPPING_TABLE",
            self._create_mock_mapping_table(),
        ):
            # Clear caches
            get_has_single_pinyin_hanzi.cache_clear()
            get_has_multiple_pinyin_hanzi.cache_clear()

            # First call
            result1 = get_has_single_pinyin_hanzi()

            # Second call should use cache
            result2 = get_has_single_pinyin_hanzi()

            # Results should be identical (same objects due to caching)
            assert result1 is result2

            # Check cache info
            cache_info = get_has_single_pinyin_hanzi.cache_info()
            assert cache_info.hits >= 1


class TestHanziPinyinIterators:
    """Test iterator-based hanzi-pinyin functions."""

    def _create_mock_mapping_table(self) -> dict:
        """Create mock pinyin mapping table."""
        return {
            "的": ["de"],
            "中": ["zhōng", "zhòng"],
            "国": ["guó"],
            "行": ["xíng", "háng"],
            "和": ["hé", "hè", "huó"],
        }

    @pytest.mark.unit
    def test_iter_single_pinyin_hanzi(self):
        """Test iterator for single pinyin characters."""
        with patch(
            "refactored.utils.hanzi_pinyin.PINYIN_MAPPING_TABLE",
            self._create_mock_mapping_table(),
        ):
            result = list(iter_single_pinyin_hanzi())

            # Should return HanziPinyin objects
            assert all(isinstance(hp, HanziPinyin) for hp in result)

            # Check all are single pronunciation
            single_chars = [hp.character for hp in result]
            assert "的" in single_chars
            assert "国" in single_chars
            assert "中" not in single_chars
            assert "行" not in single_chars
            assert "和" not in single_chars

    @pytest.mark.unit
    def test_iter_multiple_pinyin_hanzi(self):
        """Test iterator for multiple pinyin characters."""
        with patch(
            "refactored.utils.hanzi_pinyin.PINYIN_MAPPING_TABLE",
            self._create_mock_mapping_table(),
        ):
            result = list(iter_multiple_pinyin_hanzi())

            # Should return HanziPinyin objects
            assert all(isinstance(hp, HanziPinyin) for hp in result)

            # Check all are multiple pronunciation
            multi_chars = [hp.character for hp in result]
            assert "中" in multi_chars
            assert "行" in multi_chars
            assert "和" in multi_chars
            assert "的" not in multi_chars
            assert "国" not in multi_chars

    @pytest.mark.unit
    def test_iter_all_hanzi_with_filter(self):
        """Test flexible filtering iterator."""
        with patch(
            "refactored.utils.hanzi_pinyin.PINYIN_MAPPING_TABLE",
            self._create_mock_mapping_table(),
        ):
            # Test minimum count of 1 (all characters)
            result_all = list(iter_all_hanzi_with_filter(min_pinyin_count=1))
            assert len(result_all) == 5

            # Test minimum count of 2 (only multiple pronunciation)
            result_multi = list(iter_all_hanzi_with_filter(min_pinyin_count=2))
            multi_chars = [hp.character for hp in result_multi]
            assert "中" in multi_chars
            assert "行" in multi_chars
            assert "和" in multi_chars
            assert "的" not in multi_chars
            assert "国" not in multi_chars

            # Test minimum count of 3 (only characters with 3+ pronunciations)
            result_three = list(iter_all_hanzi_with_filter(min_pinyin_count=3))
            three_chars = [hp.character for hp in result_three]
            assert "和" in three_chars
            assert "中" not in three_chars
            assert "行" not in three_chars

    @pytest.mark.unit
    def test_iter_single_pronunciation_characters(self):
        """Test modern iterator for single pronunciation characters."""
        with patch(
            "refactored.utils.hanzi_pinyin.PINYIN_MAPPING_TABLE",
            self._create_mock_mapping_table(),
        ):
            result = list(iter_single_pronunciation_characters())

            # Check all are single pronunciation
            for hp in result:
                assert hp.is_single_pronunciation
                assert isinstance(hp, HanziPinyin)

    @pytest.mark.unit
    def test_iter_multiple_pronunciation_characters(self):
        """Test modern iterator for multiple pronunciation characters."""
        with patch(
            "refactored.utils.hanzi_pinyin.PINYIN_MAPPING_TABLE",
            self._create_mock_mapping_table(),
        ):
            result = list(iter_multiple_pronunciation_characters())

            # Check all are multiple pronunciation
            for hp in result:
                assert hp.is_multiple_pronunciation
                assert isinstance(hp, HanziPinyin)

    @pytest.mark.unit
    def test_iter_characters_by_pronunciation_count(self):
        """Test flexible pronunciation count filtering."""
        with patch(
            "refactored.utils.hanzi_pinyin.PINYIN_MAPPING_TABLE",
            self._create_mock_mapping_table(),
        ):
            # Test exact count (characters with exactly 2 pronunciations)
            result_two = list(
                iter_characters_by_pronunciation_count(min_count=2, max_count=2)
            )
            two_chars = [hp.character for hp in result_two]
            assert "中" in two_chars
            assert "行" in two_chars
            assert "和" not in two_chars  # has 3
            assert "的" not in two_chars  # has 1

            # Test range (characters with 1-2 pronunciations)
            result_range = list(
                iter_characters_by_pronunciation_count(min_count=1, max_count=2)
            )
            range_chars = [hp.character for hp in result_range]
            assert "的" in range_chars
            assert "中" in range_chars
            assert "行" in range_chars
            assert "国" in range_chars
            assert "和" not in range_chars  # has 3

    @pytest.mark.unit
    def test_iterator_memory_efficiency(self):
        """Test that iterators are generators (memory efficient)."""
        with patch(
            "refactored.utils.hanzi_pinyin.PINYIN_MAPPING_TABLE",
            self._create_mock_mapping_table(),
        ):
            # Test that functions return generators
            result = iter_single_pinyin_hanzi()
            assert hasattr(result, "__iter__")
            assert hasattr(result, "__next__")

            result2 = iter_multiple_pinyin_hanzi()
            assert hasattr(result2, "__iter__")
            assert hasattr(result2, "__next__")

    @pytest.mark.unit
    def test_tuple_unpacking_in_iterators(self):
        """Test backward compatibility with tuple unpacking in iterators."""
        with patch(
            "refactored.utils.hanzi_pinyin.PINYIN_MAPPING_TABLE",
            self._create_mock_mapping_table(),
        ):
            # Test tuple unpacking works with iterators
            for hanzi, pinyins in iter_single_pinyin_hanzi():
                assert isinstance(hanzi, str)
                assert isinstance(pinyins, list)
                assert len(pinyins) == 1
                break  # Just test the first one

            for hanzi, pinyins in iter_multiple_pinyin_hanzi():
                assert isinstance(hanzi, str)
                assert isinstance(pinyins, list)
                assert len(pinyins) > 1
                break  # Just test the first one


class TestHanziPinyinIntegration:
    """Test integration scenarios and edge cases."""

    @pytest.mark.unit
    def test_empty_mapping_table(self):
        """Test behavior with empty mapping table."""
        with patch("refactored.utils.hanzi_pinyin.PINYIN_MAPPING_TABLE", {}):
            # Clear caches
            get_has_single_pinyin_hanzi.cache_clear()
            get_has_multiple_pinyin_hanzi.cache_clear()

            assert get_has_single_pinyin_hanzi() == []
            assert get_has_multiple_pinyin_hanzi() == []
            assert list(iter_single_pinyin_hanzi()) == []
            assert list(iter_multiple_pinyin_hanzi()) == []

    @pytest.mark.unit
    def test_real_data_types(self):
        """Test with actual data from PINYIN_MAPPING_TABLE."""
        # Don't patch - use real data
        result = get_single_pronunciation_characters()

        # Should have some results from real data
        assert len(result) > 0

        # All should be HanziPinyin objects
        assert all(isinstance(hp, HanziPinyin) for hp in result)

        # All should have single pronunciation
        for hp in result:
            assert hp.is_single_pronunciation
            assert len(hp.pronunciations) == 1

    @pytest.mark.unit
    def test_consistency_between_functions(self):
        """Test consistency between different retrieval methods."""
        # Test that cached and non-cached versions return equivalent data
        with patch(
            "refactored.utils.hanzi_pinyin.PINYIN_MAPPING_TABLE",
            {"中": ["zhōng", "zhòng"], "的": ["de"]},
        ):
            get_has_single_pinyin_hanzi.cache_clear()

            cached_single = get_has_single_pinyin_hanzi()
            modern_single = get_single_pronunciation_characters()
            iterator_single = list(iter_single_pronunciation_characters())

            # Should have same characters
            cached_chars = [hp.character for hp in cached_single]
            modern_chars = [hp.character for hp in modern_single]
            iterator_chars = [hp.character for hp in iterator_single]

            assert set(cached_chars) == set(modern_chars) == set(iterator_chars)

    @pytest.mark.unit
    def test_performance_characteristics(self):
        """Test performance characteristics of different approaches."""
        test_data = {f"char_{i}": [f"pinyin_{i}"] for i in range(100)}

        with patch("refactored.utils.hanzi_pinyin.PINYIN_MAPPING_TABLE", test_data):
            get_has_single_pinyin_hanzi.cache_clear()

            # Test that caching works
            result1 = get_has_single_pinyin_hanzi()
            result2 = get_has_single_pinyin_hanzi()

            # Second call should be cached
            cache_info = get_has_single_pinyin_hanzi.cache_info()
            assert cache_info.hits >= 1

            # Test iterator is memory efficient (doesn't create list immediately)
            iterator = iter_single_pronunciation_characters()
            assert hasattr(iterator, "__next__")

    @pytest.mark.unit
    def test_unicode_handling(self):
        """Test proper Unicode handling for Chinese characters."""
        unicode_data = {
            "你": ["nǐ"],
            "好": ["hǎo", "hào"],
            "世": ["shì"],
            "界": ["jiè"],
        }

        with patch("refactored.utils.hanzi_pinyin.PINYIN_MAPPING_TABLE", unicode_data):
            result = get_single_pronunciation_characters()

            # Should handle Chinese characters properly
            single_chars = [hp.character for hp in result]
            assert "你" in single_chars
            assert "世" in single_chars
            assert "界" in single_chars
            assert "好" not in single_chars  # multiple pronunciations

    @pytest.mark.unit
    def test_edge_cases_pronunciation_counts(self):
        """Test edge cases with unusual pronunciation counts."""
        edge_data = {
            "zero": [],  # Edge case: no pronunciations
            "one": ["a"],
            "many": [f"pron_{i}" for i in range(10)],  # Many pronunciations
        }

        with patch("refactored.utils.hanzi_pinyin.PINYIN_MAPPING_TABLE", edge_data):
            # Characters with no pronunciations should be excluded
            single_result = list(iter_single_pronunciation_characters())
            single_chars = [hp.character for hp in single_result]
            assert "zero" not in single_chars
            assert "one" in single_chars
            assert "many" not in single_chars

            # Test flexible filtering with high counts
            many_result = list(iter_characters_by_pronunciation_count(min_count=5))
            many_chars = [hp.character for hp in many_result]
            assert "many" in many_chars
            assert "one" not in many_chars
