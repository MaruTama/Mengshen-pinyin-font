# -*- coding: utf-8 -*-
"""
Tests for font configuration management.

These tests verify that the font configuration system works correctly
and provides the expected values for different font types.
"""

import pytest

from refactored.config import (
    FontConfig,
    FontMetadata,
    FontType,
    HanziCanvas,
    PinyinCanvas,
)


class TestFontConfig:
    """Test FontConfig class functionality."""

    @pytest.mark.unit
    def test_font_config_initialization(self):
        """Test that FontConfig initializes correctly."""
        # Should not raise any exceptions
        han_serif_config = FontConfig.get_config(FontType.HAN_SERIF)
        handwritten_config = FontConfig.get_config(FontType.HANDWRITTEN)

        assert isinstance(han_serif_config, FontMetadata)
        assert isinstance(handwritten_config, FontMetadata)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "font_type,expected_values",
        [
            (
                FontType.HAN_SERIF,
                {
                    "pinyin_canvas": {
                        "width": 850.0,
                        "height": 283.3,
                        "base_line": 935.0,
                        "tracking": 22.145,
                    },
                    "hanzi_canvas": {"width": 1000.0, "height": 1000.0},
                    "is_avoid_overlapping_mode": False,
                    "x_scale_reduction_for_avoid_overlapping": 0.1,
                },
            ),
            (
                FontType.HANDWRITTEN,
                {
                    "pinyin_canvas": {
                        "width": 800.0,
                        "height": 300.0,
                        "base_line": 880.0,
                        "tracking": 5.0,
                    },
                    "hanzi_canvas": {"width": 1000.0, "height": 1000.0},
                    "is_avoid_overlapping_mode": True,
                    "x_scale_reduction_for_avoid_overlapping": 0.1,
                },
            ),
        ],
    )
    def test_font_configuration_values(self, font_type, expected_values):
        """Test font configuration values for all font types."""
        config = FontConfig.get_config(font_type)

        # Test pinyin canvas configuration
        pinyin_expected = expected_values["pinyin_canvas"]
        assert config.pinyin_canvas.width == pinyin_expected["width"]
        assert config.pinyin_canvas.height == pinyin_expected["height"]
        assert config.pinyin_canvas.base_line == pinyin_expected["base_line"]
        assert config.pinyin_canvas.tracking == pinyin_expected["tracking"]

        # Test hanzi canvas configuration
        hanzi_expected = expected_values["hanzi_canvas"]
        assert config.hanzi_canvas.width == hanzi_expected["width"]
        assert config.hanzi_canvas.height == hanzi_expected["height"]

        # Test overlap mode configuration
        assert (
            config.is_avoid_overlapping_mode
            == expected_values["is_avoid_overlapping_mode"]
        )
        assert (
            config.x_scale_reduction_for_avoid_overlapping
            == expected_values["x_scale_reduction_for_avoid_overlapping"]
        )

    @pytest.mark.unit
    def test_configuration_differences(self):
        """Test that different font types have different configurations."""
        han_serif = FontConfig.get_config(FontType.HAN_SERIF)
        handwritten = FontConfig.get_config(FontType.HANDWRITTEN)

        # These should be different
        assert han_serif.pinyin_canvas.width != handwritten.pinyin_canvas.width
        assert han_serif.pinyin_canvas.height != handwritten.pinyin_canvas.height
        assert han_serif.pinyin_canvas.base_line != handwritten.pinyin_canvas.base_line
        assert han_serif.pinyin_canvas.tracking != handwritten.pinyin_canvas.tracking
        assert (
            han_serif.is_avoid_overlapping_mode != handwritten.is_avoid_overlapping_mode
        )

        # These should be the same
        assert han_serif.hanzi_canvas.width == handwritten.hanzi_canvas.width
        assert han_serif.hanzi_canvas.height == handwritten.hanzi_canvas.height
        assert (
            han_serif.x_scale_reduction_for_avoid_overlapping
            == handwritten.x_scale_reduction_for_avoid_overlapping
        )

    @pytest.mark.unit
    def test_invalid_font_type(self):
        """Test that invalid font types raise appropriate errors."""
        with pytest.raises(ValueError, match="Unsupported font type"):
            FontConfig.get_config(999)  # Invalid font type

    @pytest.mark.unit
    def test_font_config_immutability(self):
        """Test that font configurations are immutable."""
        config = FontConfig.get_config(FontType.HAN_SERIF)

        # Dataclass is frozen, so these should raise AttributeError
        with pytest.raises(AttributeError):
            config.pinyin_canvas.width = 999

        with pytest.raises(AttributeError):
            config.hanzi_canvas.width = 999

        with pytest.raises(AttributeError):
            config.is_avoid_overlapping_mode = True

    @pytest.mark.unit
    def test_pinyin_canvas_helper_methods(self):
        """Test PinyinCanvas helper methods."""
        han_serif_canvas = FontConfig.get_pinyin_canvas(FontType.HAN_SERIF)
        handwritten_canvas = FontConfig.get_pinyin_canvas(FontType.HANDWRITTEN)

        assert isinstance(han_serif_canvas, PinyinCanvas)
        assert isinstance(handwritten_canvas, PinyinCanvas)

        # Should match the values from get_config
        han_serif_config = FontConfig.get_config(FontType.HAN_SERIF)
        assert han_serif_canvas == han_serif_config.pinyin_canvas

    @pytest.mark.unit
    def test_hanzi_canvas_helper_methods(self):
        """Test HanziCanvas helper methods."""
        han_serif_canvas = FontConfig.get_hanzi_canvas(FontType.HAN_SERIF)
        handwritten_canvas = FontConfig.get_hanzi_canvas(FontType.HANDWRITTEN)

        assert isinstance(han_serif_canvas, HanziCanvas)
        assert isinstance(handwritten_canvas, HanziCanvas)

        # Should match the values from get_config
        han_serif_config = FontConfig.get_config(FontType.HAN_SERIF)
        assert han_serif_canvas == han_serif_config.hanzi_canvas

    @pytest.mark.unit
    def test_configuration_consistency(self):
        """Test that configurations are consistent across calls."""
        # Multiple calls should return identical objects
        config1 = FontConfig.get_config(FontType.HAN_SERIF)
        config2 = FontConfig.get_config(FontType.HAN_SERIF)

        assert config1 == config2
        assert config1.pinyin_canvas == config2.pinyin_canvas
        assert config1.hanzi_canvas == config2.hanzi_canvas

    @pytest.mark.unit
    def test_font_type_enum_values(self):
        """Test that FontType enum has expected values."""
        assert FontType.HAN_SERIF == 1
        assert FontType.HANDWRITTEN == 2

        # Test that all enum values are supported
        for font_type in FontType:
            config = FontConfig.get_config(font_type)
            assert isinstance(config, FontMetadata)


class TestPinyinCanvas:
    """Test PinyinCanvas configuration."""

    @pytest.mark.unit
    def test_pinyin_canvas_creation(self):
        """Test PinyinCanvas creation and attributes."""
        canvas = PinyinCanvas(width=800.0, height=300.0, base_line=880.0, tracking=5.0)

        assert canvas.width == 800.0
        assert canvas.height == 300.0
        assert canvas.base_line == 880.0
        assert canvas.tracking == 5.0

    @pytest.mark.unit
    def test_pinyin_canvas_immutability(self):
        """Test that PinyinCanvas is immutable."""
        canvas = PinyinCanvas(width=800.0, height=300.0, base_line=880.0, tracking=5.0)

        # Should not be able to modify attributes
        with pytest.raises(AttributeError):
            canvas.width = 900.0

        with pytest.raises(AttributeError):
            canvas.height = 400.0

    @pytest.mark.unit
    def test_pinyin_canvas_equality(self):
        """Test PinyinCanvas equality comparison."""
        canvas1 = PinyinCanvas(800.0, 300.0, 880.0, 5.0)
        canvas2 = PinyinCanvas(800.0, 300.0, 880.0, 5.0)
        canvas3 = PinyinCanvas(850.0, 300.0, 880.0, 5.0)

        assert canvas1 == canvas2
        assert canvas1 != canvas3


class TestHanziCanvas:
    """Test HanziCanvas configuration."""

    @pytest.mark.unit
    def test_hanzi_canvas_creation(self):
        """Test HanziCanvas creation and attributes."""
        canvas = HanziCanvas(width=1000.0, height=1000.0)

        assert canvas.width == 1000.0
        assert canvas.height == 1000.0

    @pytest.mark.unit
    def test_hanzi_canvas_immutability(self):
        """Test that HanziCanvas is immutable."""
        canvas = HanziCanvas(width=1000.0, height=1000.0)

        # Should not be able to modify attributes
        with pytest.raises(AttributeError):
            canvas.width = 1200.0

        with pytest.raises(AttributeError):
            canvas.height = 1200.0

    @pytest.mark.unit
    def test_hanzi_canvas_equality(self):
        """Test HanziCanvas equality comparison."""
        canvas1 = HanziCanvas(1000.0, 1000.0)
        canvas2 = HanziCanvas(1000.0, 1000.0)
        canvas3 = HanziCanvas(1200.0, 1000.0)

        assert canvas1 == canvas2
        assert canvas1 != canvas3


class TestFontMetadata:
    """Test FontMetadata configuration."""

    @pytest.mark.unit
    def test_font_metadata_creation(self):
        """Test FontMetadata creation and attributes."""
        pinyin_canvas = PinyinCanvas(800.0, 300.0, 880.0, 5.0)
        hanzi_canvas = HanziCanvas(1000.0, 1000.0)

        metadata = FontMetadata(
            pinyin_canvas=pinyin_canvas,
            hanzi_canvas=hanzi_canvas,
            is_avoid_overlapping_mode=True,
            x_scale_reduction_for_avoid_overlapping=0.1,
        )

        assert metadata.pinyin_canvas == pinyin_canvas
        assert metadata.hanzi_canvas == hanzi_canvas
        assert metadata.is_avoid_overlapping_mode is True
        assert metadata.x_scale_reduction_for_avoid_overlapping == 0.1

    @pytest.mark.unit
    def test_font_metadata_immutability(self):
        """Test that FontMetadata is immutable."""
        pinyin_canvas = PinyinCanvas(800.0, 300.0, 880.0, 5.0)
        hanzi_canvas = HanziCanvas(1000.0, 1000.0)

        metadata = FontMetadata(
            pinyin_canvas=pinyin_canvas,
            hanzi_canvas=hanzi_canvas,
            is_avoid_overlapping_mode=True,
            x_scale_reduction_for_avoid_overlapping=0.1,
        )

        # Should not be able to modify attributes
        with pytest.raises(AttributeError):
            metadata.is_avoid_overlapping_mode = False

        with pytest.raises(AttributeError):
            metadata.x_scale_reduction_for_avoid_overlapping = 0.2

    @pytest.mark.unit
    def test_font_metadata_validation(self):
        """Test that FontMetadata validates input parameters."""
        pinyin_canvas = PinyinCanvas(800.0, 300.0, 880.0, 5.0)
        hanzi_canvas = HanziCanvas(1000.0, 1000.0)

        # Valid metadata should work
        metadata = FontMetadata(
            pinyin_canvas=pinyin_canvas,
            hanzi_canvas=hanzi_canvas,
            is_avoid_overlapping_mode=True,
            x_scale_reduction_for_avoid_overlapping=0.1,
        )

        assert metadata is not None

        # Test with edge case values
        metadata_edge = FontMetadata(
            pinyin_canvas=pinyin_canvas,
            hanzi_canvas=hanzi_canvas,
            is_avoid_overlapping_mode=False,
            x_scale_reduction_for_avoid_overlapping=0.0,
        )

        assert metadata_edge.x_scale_reduction_for_avoid_overlapping == 0.0
