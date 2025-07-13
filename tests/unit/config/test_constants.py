# -*- coding: utf-8 -*-
"""
Tests for font constants and configuration values.

These tests verify that font constants have the expected values
and that duplicate character handling is correct.
"""

import pytest

from refactored.config.constants import (
    METADATA_FOR_HAN_SERIF,
    METADATA_FOR_HANDWRITTEN,
    FontConstants,
)


class TestFontConstants:
    """Test FontConstants class."""

    @pytest.mark.unit
    def test_pronunciation_indices(self):
        """Test pronunciation index constants."""
        assert FontConstants.NORMAL_PRONUNCIATION == 0
        assert FontConstants.VARIATIONAL_PRONUNCIATION == 1

        # Ensure they are different
        assert (
            FontConstants.NORMAL_PRONUNCIATION
            != FontConstants.VARIATIONAL_PRONUNCIATION
        )

    @pytest.mark.unit
    def test_stylistic_set_indices(self):
        """Test stylistic set index constants."""
        assert FontConstants.SS_NORMAL_PRONUNCIATION == 1
        assert FontConstants.SS_VARIATIONAL_PRONUNCIATION == 2

        # Ensure they are in correct order
        assert (
            FontConstants.SS_NORMAL_PRONUNCIATION
            < FontConstants.SS_VARIATIONAL_PRONUNCIATION
        )

    @pytest.mark.unit
    def test_ivs_base_value(self):
        """Test IVS (Ideographic Variant Selector) base value."""
        assert FontConstants.IVS_BASE == 0xE01E0
        assert FontConstants.IVS_BASE == 917984  # Decimal equivalent

        # Ensure it's in the correct Unicode range for IVS
        assert FontConstants.IVS_BASE >= 0xE0100  # IVS range start
        assert FontConstants.IVS_BASE <= 0xE01EF  # IVS range end

    @pytest.mark.unit
    def test_font_limits(self):
        """Test font limitation constants."""
        assert FontConstants.MAX_GLYPHS == 65536

        # Ensure it's the correct OpenType limit
        assert FontConstants.MAX_GLYPHS == 2**16

    @pytest.mark.unit
    def test_file_extensions(self):
        """Test file extension constants."""
        assert FontConstants.TTF_EXTENSION == ".ttf"
        assert FontConstants.JSON_EXTENSION == ".json"
        assert FontConstants.TXT_EXTENSION == ".txt"

        # Ensure they start with dot
        assert FontConstants.TTF_EXTENSION.startswith(".")
        assert FontConstants.JSON_EXTENSION.startswith(".")
        assert FontConstants.TXT_EXTENSION.startswith(".")

    @pytest.mark.unit
    def test_font_table_names(self):
        """Test OpenType font table name constants."""
        expected_tables = [
            "cmap",
            "cmap_uvs",
            "glyf",
            "GSUB",
            "head",
            "hhea",
            "OS_2",
            "name",
            "glyph_order",
        ]

        actual_tables = [
            FontConstants.CMAP_TABLE,
            FontConstants.CMAP_UVS_TABLE,
            FontConstants.GLYF_TABLE,
            FontConstants.GSUB_TABLE,
            FontConstants.HEAD_TABLE,
            FontConstants.HHEA_TABLE,
            FontConstants.OS2_TABLE,
            FontConstants.NAME_TABLE,
            FontConstants.GLYPH_ORDER,
        ]

        assert len(actual_tables) == len(expected_tables)
        for table in expected_tables:
            assert table in actual_tables

    @pytest.mark.unit
    def test_duplicate_character_definitions(self):
        """Test duplicate character handling constants."""
        # Test WU4 duplicate characters
        wu4_unicodes = FontConstants.DUPLICATE_WU4_UNICODES
        assert len(wu4_unicodes) == 3
        assert 0x2E8E in wu4_unicodes  # ⺎
        assert 0x5140 in wu4_unicodes  # 兀
        assert 0xFA0C in wu4_unicodes  # 兀 (variant)

        # Test HU4 duplicate characters
        hu4_unicodes = FontConstants.DUPLICATE_HU4_UNICODES
        assert len(hu4_unicodes) == 2
        assert 0x55C0 in hu4_unicodes  # 嗀
        assert 0xFA0D in hu4_unicodes  # 嗀 (variant)

        # Ensure no overlap between the two sets
        assert not set(wu4_unicodes) & set(hu4_unicodes)

    @pytest.mark.unit
    def test_performance_cache_sizes(self):
        """Test performance-related cache size constants."""
        cache_sizes = [
            FontConstants.LRU_CACHE_SIZE_SMALL,
            FontConstants.LRU_CACHE_SIZE_MEDIUM,
            FontConstants.LRU_CACHE_SIZE_LARGE,
            FontConstants.LRU_CACHE_SIZE_XLARGE,
        ]

        # Ensure they are in ascending order
        assert cache_sizes == sorted(cache_sizes)

        # Ensure they are reasonable values
        assert FontConstants.LRU_CACHE_SIZE_SMALL >= 64
        assert FontConstants.LRU_CACHE_SIZE_XLARGE <= 8192

    @pytest.mark.unit
    def test_date_time_constants(self):
        """Test date and time format constants."""
        assert FontConstants.FONT_EPOCH_BASE_DATE == "1904/01/01 00:00"
        assert FontConstants.DATE_FORMAT == "%Y/%m/%d %H:%M"

        # Test that the format can parse the base date
        from datetime import datetime

        parsed_date = datetime.strptime(
            FontConstants.FONT_EPOCH_BASE_DATE, FontConstants.DATE_FORMAT
        )
        assert parsed_date.year == 1904
        assert parsed_date.month == 1
        assert parsed_date.day == 1
        assert parsed_date.hour == 0
        assert parsed_date.minute == 0

    @pytest.mark.unit
    def test_constant_types(self):
        """Test that constants have correct types."""
        # Integer constants
        assert isinstance(FontConstants.NORMAL_PRONUNCIATION, int)
        assert isinstance(FontConstants.VARIATIONAL_PRONUNCIATION, int)
        assert isinstance(FontConstants.SS_NORMAL_PRONUNCIATION, int)
        assert isinstance(FontConstants.SS_VARIATIONAL_PRONUNCIATION, int)
        assert isinstance(FontConstants.IVS_BASE, int)
        assert isinstance(FontConstants.MAX_GLYPHS, int)

        # String constants
        assert isinstance(FontConstants.TTF_EXTENSION, str)
        assert isinstance(FontConstants.JSON_EXTENSION, str)
        assert isinstance(FontConstants.TXT_EXTENSION, str)
        assert isinstance(FontConstants.CMAP_TABLE, str)
        assert isinstance(FontConstants.FONT_EPOCH_BASE_DATE, str)
        assert isinstance(FontConstants.DATE_FORMAT, str)

        # List constants
        assert isinstance(FontConstants.DUPLICATE_WU4_UNICODES, list)
        assert isinstance(FontConstants.DUPLICATE_HU4_UNICODES, list)

        # All Unicode values should be integers
        for unicode_val in FontConstants.DUPLICATE_WU4_UNICODES:
            assert isinstance(unicode_val, int)
        for unicode_val in FontConstants.DUPLICATE_HU4_UNICODES:
            assert isinstance(unicode_val, int)


class TestLegacyMetadataConstants:
    """Test legacy metadata constants for backward compatibility."""

    @pytest.mark.unit
    def test_metadata_for_han_serif(self):
        """Test METADATA_FOR_HAN_SERIF constant."""
        assert METADATA_FOR_HAN_SERIF is not None

        # Should have the expected structure
        assert hasattr(METADATA_FOR_HAN_SERIF, "pinyin_canvas")
        assert hasattr(METADATA_FOR_HAN_SERIF, "hanzi_canvas")
        assert hasattr(METADATA_FOR_HAN_SERIF, "is_avoid_overlapping_mode")
        assert hasattr(
            METADATA_FOR_HAN_SERIF, "x_scale_reduction_for_avoid_overlapping"
        )

        # Should have the expected values
        assert METADATA_FOR_HAN_SERIF.pinyin_canvas.width == 850.0
        assert METADATA_FOR_HAN_SERIF.pinyin_canvas.height == 283.3
        assert METADATA_FOR_HAN_SERIF.is_avoid_overlapping_mode is False

    @pytest.mark.unit
    def test_metadata_for_handwritten(self):
        """Test METADATA_FOR_HANDWRITTEN constant."""
        assert METADATA_FOR_HANDWRITTEN is not None

        # Should have the expected structure
        assert hasattr(METADATA_FOR_HANDWRITTEN, "pinyin_canvas")
        assert hasattr(METADATA_FOR_HANDWRITTEN, "hanzi_canvas")
        assert hasattr(METADATA_FOR_HANDWRITTEN, "is_avoid_overlapping_mode")
        assert hasattr(
            METADATA_FOR_HANDWRITTEN, "x_scale_reduction_for_avoid_overlapping"
        )

        # Should have the expected values
        assert METADATA_FOR_HANDWRITTEN.pinyin_canvas.width == 800.0
        assert METADATA_FOR_HANDWRITTEN.pinyin_canvas.height == 300.0
        assert METADATA_FOR_HANDWRITTEN.is_avoid_overlapping_mode is True

    @pytest.mark.unit
    def test_metadata_consistency(self):
        """Test that metadata constants are consistent with FontConfig."""
        from refactored.config import FontConfig, FontType

        # Should match FontConfig values
        han_serif_config = FontConfig.get_config(FontType.HAN_SERIF)
        handwritten_config = FontConfig.get_config(FontType.HANDWRITTEN)

        assert METADATA_FOR_HAN_SERIF == han_serif_config
        assert METADATA_FOR_HANDWRITTEN == handwritten_config

    @pytest.mark.unit
    def test_unicode_character_validation(self):
        """Test that Unicode characters in constants are valid."""
        # Test WU4 characters
        for unicode_val in FontConstants.DUPLICATE_WU4_UNICODES:
            # Should be valid Unicode code points
            assert 0 <= unicode_val <= 0x10FFFF

            # Should be able to create character
            char = chr(unicode_val)
            assert len(char) == 1

        # Test HU4 characters
        for unicode_val in FontConstants.DUPLICATE_HU4_UNICODES:
            # Should be valid Unicode code points
            assert 0 <= unicode_val <= 0x10FFFF

            # Should be able to create character
            char = chr(unicode_val)
            assert len(char) == 1

    @pytest.mark.unit
    def test_constant_values_remain_stable(self):
        """Test that constant values remain stable."""
        # Store original values
        original_ivs_base = FontConstants.IVS_BASE
        original_wu4 = FontConstants.DUPLICATE_WU4_UNICODES.copy()
        original_hu4 = FontConstants.DUPLICATE_HU4_UNICODES.copy()

        # Even if someone modifies the class attributes (which is possible),
        # the original values should be as expected
        assert original_ivs_base == 0xE01E0
        assert original_wu4 == [0x2E8E, 0x5140, 0xFA0C]
        assert original_hu4 == [0x55C0, 0xFA0D]

        # Verify current values match expected values
        assert FontConstants.IVS_BASE == 0xE01E0
        assert FontConstants.DUPLICATE_WU4_UNICODES == [0x2E8E, 0x5140, 0xFA0C]
        assert FontConstants.DUPLICATE_HU4_UNICODES == [0x55C0, 0xFA0D]
