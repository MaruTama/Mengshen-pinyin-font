# -*- coding: utf-8 -*-
"""
Tests for PinyinGlyph class.

These tests verify the core pinyin glyph generation functionality including
character-to-pinyin mapping, glyph scaling, positioning, and font metadata integration.
Following TDD principles with comprehensive coverage of edge cases.
"""

from unittest.mock import Mock, mock_open, patch

import pytest

from refactored.config.font_config import (
    METADATA_FOR_HAN_SERIF,
    METADATA_FOR_HANDWRITTEN,
    FontType,
)
from refactored.glyph.pinyin_glyph import (
    DELTA_4_REFLECTION,
    HEIGHT_RATE_OF_MONOSPACE,
    VERTICAL_ORIGIN_PER_HEIGHT,
    PinyinGlyph,
)


class TestPinyinGlyphInitialization:
    """Test PinyinGlyph initialization and setup."""

    @pytest.mark.unit
    def test_initialization_han_serif(self):
        """Test PinyinGlyph initialization with han serif font type."""
        # Mock data setup
        mock_template_main = {
            "cmap": {"19968": "uni4E00"},  # Unicode for "一"
            "glyf": {"uni4E00": {"advanceWidth": 1000, "advanceHeight": 1000}},
        }

        mock_alphabet = {
            "a": {"advanceWidth": 500, "advanceHeight": 700},
            "b": {"advanceWidth": 500, "advanceHeight": 700},
        }

        mock_pinyin_table = {"中": ["zhōng", "zhòng"]}

        with patch("builtins.open", mock_open()):
            with patch("orjson.loads", side_effect=[mock_template_main, mock_alphabet]):
                with patch(
                    "refactored.glyph.pinyin_glyph.get_pinyin_table_with_mapping_table",
                    return_value=mock_pinyin_table,
                ):
                    pinyin_glyph = PinyinGlyph(
                        template_main_json="/mock/template.json",
                        alphabet_for_pinyin_json="/mock/alphabet.json",
                        font_type=FontType.HAN_SERIF,
                    )

                    # Verify initialization
                    assert pinyin_glyph.font_main == mock_template_main
                    assert pinyin_glyph.cmap_table == mock_template_main["cmap"]
                    assert pinyin_glyph.PY_ALPHABET_GLYF == mock_alphabet
                    assert pinyin_glyph.METADATA_FOR_PINYIN == METADATA_FOR_HAN_SERIF
                    assert pinyin_glyph.PINYIN_MAPPING_TABLE == mock_pinyin_table
                    assert pinyin_glyph.pronunciations == {}

    @pytest.mark.unit
    def test_initialization_handwritten(self):
        """Test PinyinGlyph initialization with handwritten font type."""
        mock_template_main = {
            "cmap": {"19968": "uni4E00"},
            "glyf": {"uni4E00": {"advanceWidth": 800, "advanceHeight": 800}},
        }

        mock_alphabet = {"a": {"advanceWidth": 400}}
        mock_pinyin_table = {}

        with patch("builtins.open", mock_open()):
            with patch("orjson.loads", side_effect=[mock_template_main, mock_alphabet]):
                with patch(
                    "refactored.glyph.pinyin_glyph.get_pinyin_table_with_mapping_table",
                    return_value=mock_pinyin_table,
                ):

                    pinyin_glyph = PinyinGlyph(
                        template_main_json="/mock/template.json",
                        alphabet_for_pinyin_json="/mock/alphabet.json",
                        font_type=FontType.HANDWRITTEN,
                    )

                    assert pinyin_glyph.METADATA_FOR_PINYIN == METADATA_FOR_HANDWRITTEN

    @pytest.mark.unit
    def test_initialization_unsupported_font_type(self):
        """Test PinyinGlyph initialization with unsupported font type."""
        # Create minimal valid mock data structure
        mock_template_main = {
            "cmap": {"19968": "uni4E00"},
            "glyf": {"uni4E00": {"advanceWidth": 1000, "advanceHeight": 1000}},
        }
        mock_alphabet = {}

        with patch("builtins.open", mock_open()):
            with patch("orjson.loads", side_effect=[mock_template_main, mock_alphabet]):
                with patch(
                    "refactored.glyph.pinyin_glyph.get_pinyin_table_with_mapping_table",
                    return_value={},
                ):
                    with pytest.raises(ValueError, match="Unsupported font type"):
                        PinyinGlyph(
                            template_main_json="/mock/template.json",
                            alphabet_for_pinyin_json="/mock/alphabet.json",
                            font_type="invalid_type",  # Not a valid FontType enum
                        )

    @pytest.mark.unit
    def test_initialization_file_loading_error(self):
        """Test PinyinGlyph initialization with file loading errors."""
        with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
            with pytest.raises(FileNotFoundError):
                PinyinGlyph(
                    template_main_json="/nonexistent/template.json",
                    alphabet_for_pinyin_json="/nonexistent/alphabet.json",
                    font_type=FontType.HAN_SERIF,
                )

    @pytest.mark.unit
    def test_initialization_json_parsing_error(self):
        """Test PinyinGlyph initialization with JSON parsing errors."""
        with patch("builtins.open", mock_open(read_data=b"invalid json")):
            with patch("orjson.loads", side_effect=ValueError("Invalid JSON")):
                with patch(
                    "refactored.glyph.pinyin_glyph.get_pinyin_table_with_mapping_table",
                    return_value={},
                ):
                    with pytest.raises(ValueError):
                        PinyinGlyph(
                            template_main_json="/mock/template.json",
                            alphabet_for_pinyin_json="/mock/alphabet.json",
                            font_type=FontType.HAN_SERIF,
                        )


class TestPinyinGlyphSizeCalculations:
    """Test size calculation methods."""

    def _create_test_pinyin_glyph(self, font_data=None, alphabet_data=None):
        """Helper to create PinyinGlyph for testing."""
        if font_data is None:
            font_data = {
                "cmap": {"19968": "uni4E00"},
                "glyf": {"uni4E00": {"advanceWidth": 1000, "advanceHeight": 1000}},
            }

        if alphabet_data is None:
            alphabet_data = {
                "a": {"advanceWidth": 500, "advanceHeight": 700},
                "o": {"advanceWidth": 500, "advanceHeight": 700},
                "ā": {"advanceWidth": 500, "advanceHeight": 800},
            }

        with patch("builtins.open", mock_open()):
            with patch("orjson.loads", side_effect=[font_data, alphabet_data]):
                with patch(
                    "refactored.glyph.pinyin_glyph.get_pinyin_table_with_mapping_table",
                    return_value={},
                ):
                    return PinyinGlyph(
                        template_main_json="/mock/template.json",
                        alphabet_for_pinyin_json="/mock/alphabet.json",
                        font_type=FontType.HAN_SERIF,
                    )

    @pytest.mark.unit
    def test_get_advance_size_of_hanzi_with_height(self):
        """Test hanzi size calculation when advance height is present."""
        font_data = {
            "cmap": {"19968": "uni4E00"},
            "glyf": {"uni4E00": {"advanceWidth": 1000, "advanceHeight": 1200}},
        }

        pinyin_glyph = self._create_test_pinyin_glyph(font_data=font_data)
        width, height = pinyin_glyph._PinyinGlyph__get_advance_size_of_hanzi()

        assert width == 1000
        assert height == 1200

    @pytest.mark.unit
    def test_get_advance_size_of_hanzi_without_height(self):
        """Test hanzi size calculation when advance height is missing."""
        font_data = {
            "cmap": {"19968": "uni4E00"},
            "glyf": {
                "uni4E00": {
                    "advanceWidth": 1000
                    # No advanceHeight
                }
            },
        }

        pinyin_glyph = self._create_test_pinyin_glyph(font_data=font_data)
        width, height = pinyin_glyph._PinyinGlyph__get_advance_size_of_hanzi()

        assert width == 1000
        assert height == 1000 * HEIGHT_RATE_OF_MONOSPACE  # 1000 * 1.4 = 1400

    @pytest.mark.unit
    def test_get_advance_size_of_pinyin_single_char(self):
        """Test pinyin size calculation for single character."""
        alphabet_data = {"a": {"advanceWidth": 500, "advanceHeight": 700}}

        pinyin_glyph = self._create_test_pinyin_glyph(alphabet_data=alphabet_data)
        width, height = pinyin_glyph._PinyinGlyph__get_advance_size_of_pinyin("a")

        assert width == 500
        assert height == 700

    @pytest.mark.unit
    def test_get_advance_size_of_pinyin_multiple_chars(self):
        """Test pinyin size calculation for multiple characters."""
        alphabet_data = {
            "z": {"advanceWidth": 400, "advanceHeight": 700},
            "h": {"advanceWidth": 500, "advanceHeight": 700},
            "ō": {"advanceWidth": 500, "advanceHeight": 800},
            "n": {"advanceWidth": 500, "advanceHeight": 700},
            "g": {"advanceWidth": 450, "advanceHeight": 700},
        }

        pinyin_glyph = self._create_test_pinyin_glyph(alphabet_data=alphabet_data)
        width, height = pinyin_glyph._PinyinGlyph__get_advance_size_of_pinyin("zhōng")

        # Width should be sum of all character widths
        expected_width = 400 + 500 + 500 + 500 + 450  # 2350
        # Height should be maximum height among characters
        expected_height = 800  # Max of 700, 700, 800, 700, 700

        assert width == expected_width
        assert height == expected_height

    @pytest.mark.unit
    def test_get_advance_size_of_pinyin_missing_chars(self):
        """Test pinyin size calculation with missing characters in alphabet."""
        alphabet_data = {
            "a": {"advanceWidth": 500, "advanceHeight": 700}
            # Missing "b" and "c"
        }

        pinyin_glyph = self._create_test_pinyin_glyph(alphabet_data=alphabet_data)
        width, height = pinyin_glyph._PinyinGlyph__get_advance_size_of_pinyin("abc")

        # Only "a" should contribute to width, "b" and "c" are missing
        assert width == 500
        assert height == 700

    @pytest.mark.unit
    def test_get_advance_size_of_pinyin_empty_string(self):
        """Test pinyin size calculation with empty string."""
        pinyin_glyph = self._create_test_pinyin_glyph()
        width, height = pinyin_glyph._PinyinGlyph__get_advance_size_of_pinyin("")

        assert width == 0
        assert height == 0

    @pytest.mark.unit
    def test_get_advance_size_of_pinyin_chars_without_height(self):
        """Test pinyin size calculation with characters missing height info."""
        alphabet_data = {
            "a": {"advanceWidth": 500},  # Missing advanceHeight
            "b": {"advanceWidth": 400, "advanceHeight": 600},
        }

        pinyin_glyph = self._create_test_pinyin_glyph(alphabet_data=alphabet_data)
        width, height = pinyin_glyph._PinyinGlyph__get_advance_size_of_pinyin("ab")

        # Width: 500 + 400 = 900
        # Height: max(0, 600) = 600 (missing height defaults to 0)
        assert width == 900
        assert height == 600


class TestPinyinGlyphGeneration:
    """Test core pinyin glyph generation functionality."""

    def _create_test_pinyin_glyph_with_data(self):
        """Helper to create PinyinGlyph with comprehensive test data."""
        font_data = {
            "cmap": {"19968": "uni4E00"},
            "glyf": {"uni4E00": {"advanceWidth": 1000, "advanceHeight": 1000}},
        }

        alphabet_data = {
            "z": {"advanceWidth": 400, "advanceHeight": 700},
            "h": {"advanceWidth": 500, "advanceHeight": 700},
            "ō": {"advanceWidth": 500, "advanceHeight": 800},
            "n": {"advanceWidth": 500, "advanceHeight": 700},
            "g": {"advanceWidth": 450, "advanceHeight": 700},
            "à": {"advanceWidth": 500, "advanceHeight": 800},
        }

        pinyin_table = {"中": ["zhōng", "zhòng"], "国": ["guó"], "好": ["hǎo", "hào"]}

        with patch("builtins.open", mock_open()):
            with patch("orjson.loads") as mock_json:
                with patch(
                    "refactored.glyph.pinyin_glyph.get_pinyin_table_with_mapping_table",
                    return_value=pinyin_table,
                ):
                    mock_json.side_effect = [font_data, alphabet_data]

                    return PinyinGlyph(
                        template_main_json="/mock/template.json",
                        alphabet_for_pinyin_json="/mock/alphabet.json",
                        font_type=FontType.HAN_SERIF,
                    )

    @pytest.mark.unit
    def test_get_pinyin_glyph_for_hanzi_valid_character(self):
        """Test pinyin glyph generation for valid hanzi character."""
        pinyin_glyph = self._create_test_pinyin_glyph_with_data()

        # Test getting glyph for "中" (should use first pronunciation "zhōng")
        glyph_data = pinyin_glyph.get_pinyin_glyph_for_hanzi("中")

        # Verify glyph structure
        assert isinstance(glyph_data, dict)
        assert "advanceWidth" in glyph_data
        assert "advanceHeight" in glyph_data
        assert "contours" in glyph_data
        assert "references" in glyph_data
        assert "instructions" in glyph_data

        # Verify hanzi dimensions are preserved
        assert glyph_data["advanceWidth"] == 1000
        assert glyph_data["advanceHeight"] == 1000

        # Verify references are created for each character in "zhōng"
        assert len(glyph_data["references"]) == 5  # z, h, ō, n, g

        # Verify first reference
        first_ref = glyph_data["references"][0]
        assert first_ref["glyph"] == "z"
        assert "x" in first_ref
        assert "y" in first_ref
        assert "scaleX" in first_ref
        assert "scaleY" in first_ref

    @pytest.mark.unit
    def test_get_pinyin_glyph_for_hanzi_unknown_character(self):
        """Test pinyin glyph generation for unknown hanzi character."""
        pinyin_glyph = self._create_test_pinyin_glyph_with_data()

        # Test getting glyph for character not in pinyin table
        glyph_data = pinyin_glyph.get_pinyin_glyph_for_hanzi("未")

        # Should return empty dict for unknown characters
        assert glyph_data == {}

    @pytest.mark.unit
    def test_get_pinyin_glyph_for_hanzi_caching(self):
        """Test that pinyin glyphs are cached after first generation."""
        pinyin_glyph = self._create_test_pinyin_glyph_with_data()

        # Get glyph first time
        glyph_data_1 = pinyin_glyph.get_pinyin_glyph_for_hanzi("中")

        # Verify it's cached
        assert "zhōng" in pinyin_glyph.pronunciations

        # Get glyph second time
        glyph_data_2 = pinyin_glyph.get_pinyin_glyph_for_hanzi("中")

        # Should return same cached object
        assert glyph_data_1 is glyph_data_2

    @pytest.mark.unit
    def test_get_pinyin_glyph_for_hanzi_multiple_pronunciations(self):
        """Test that first pronunciation is used for characters with multiple pronunciations."""
        pinyin_glyph = self._create_test_pinyin_glyph_with_data()

        # "中" has pronunciations ["zhōng", "zhòng"], should use first one
        glyph_data = pinyin_glyph.get_pinyin_glyph_for_hanzi("中")

        # Verify it uses first pronunciation "zhōng"
        assert len(glyph_data["references"]) == 5  # z, h, ō, n, g
        assert (
            glyph_data["references"][2]["glyph"] == "ō"
        )  # Third character should be "ō"

    @pytest.mark.unit
    def test_create_pinyin_glyph_basic_structure(self):
        """Test basic structure of created pinyin glyph."""
        pinyin_glyph = self._create_test_pinyin_glyph_with_data()

        # Test creating glyph for "zhōng"
        glyph_data = pinyin_glyph._create_pinyin_glyph("zhōng")

        # Verify basic structure
        assert isinstance(glyph_data, dict)
        assert glyph_data["advanceWidth"] == 1000  # Hanzi width
        assert glyph_data["advanceHeight"] == 1000  # Hanzi height
        assert glyph_data["contours"] == []
        assert isinstance(glyph_data["references"], list)
        assert glyph_data["instructions"] == []

    @pytest.mark.unit
    def test_create_pinyin_glyph_scaling_calculation(self):
        """Test scaling calculation in pinyin glyph creation."""
        pinyin_glyph = self._create_test_pinyin_glyph_with_data()

        # Mock metadata for predictable scaling
        mock_metadata = Mock()
        mock_metadata.pinyin_canvas.width = 800
        mock_metadata.pinyin_canvas.height = 600
        mock_metadata.pinyin_canvas.base_line = 100
        mock_metadata.is_avoid_overlapping_mode = False
        pinyin_glyph.METADATA_FOR_PINYIN = mock_metadata

        glyph_data = pinyin_glyph._create_pinyin_glyph("zhōng")

        # Calculate expected scaling
        # pinyin_width = 400+500+500+500+450 = 2350
        # pinyin_height = 800 (max height)
        # scale_x = 800 / 2350 ≈ 0.34
        # scale_y = 600 / 800 = 0.75

        expected_scale_x = 800 / 2350
        expected_scale_y = 600 / 800

        # Check first reference scaling
        first_ref = glyph_data["references"][0]
        assert abs(first_ref["scaleX"] - expected_scale_x) < 0.01
        assert abs(first_ref["scaleY"] - expected_scale_y) < 0.01

    @pytest.mark.unit
    def test_create_pinyin_glyph_overlapping_mode(self):
        """Test scaling adjustment for overlapping avoidance mode."""
        pinyin_glyph = self._create_test_pinyin_glyph_with_data()

        # Mock metadata with overlapping mode enabled
        mock_metadata = Mock()
        mock_metadata.pinyin_canvas.width = 800
        mock_metadata.pinyin_canvas.height = 600
        mock_metadata.pinyin_canvas.base_line = 100
        mock_metadata.is_avoid_overlapping_mode = True
        mock_metadata.x_scale_reduction_for_avoid_overlapping = 0.1
        pinyin_glyph.METADATA_FOR_PINYIN = mock_metadata

        # Test with long pronunciation (5+ characters)
        glyph_data = pinyin_glyph._create_pinyin_glyph("zhōng")  # 5 characters

        # Calculate expected scaling with reduction
        base_scale_x = 800 / 2350
        expected_scale_x = base_scale_x * (1.0 - 0.1)  # Reduced by 10%

        first_ref = glyph_data["references"][0]
        assert abs(first_ref["scaleX"] - expected_scale_x) < 0.01

    @pytest.mark.unit
    def test_create_pinyin_glyph_positioning(self):
        """Test character positioning in pinyin glyph."""
        pinyin_glyph = self._create_test_pinyin_glyph_with_data()

        # Mock metadata
        mock_metadata = Mock()
        mock_metadata.pinyin_canvas.width = 1000
        mock_metadata.pinyin_canvas.height = 800
        mock_metadata.pinyin_canvas.base_line = 150
        mock_metadata.is_avoid_overlapping_mode = False
        pinyin_glyph.METADATA_FOR_PINYIN = mock_metadata

        glyph_data = pinyin_glyph._create_pinyin_glyph("zhōng")

        # Check positioning - each character should be positioned sequentially
        references = glyph_data["references"]

        # All characters should have same y position (baseline)
        for ref in references:
            assert ref["y"] == 150

        # X positions should increase sequentially
        expected_x_positions = [
            0,
            400,
            900,
            1400,
            1900,
        ]  # Cumulative widths with scaling
        scale_x = 1000 / 2350  # Canvas width / total pinyin width

        for i, ref in enumerate(references):
            expected_x = expected_x_positions[i] * scale_x
            assert (
                abs(ref["x"] - expected_x) < 1.0
            )  # Allow small floating point differences

    @pytest.mark.unit
    def test_create_pinyin_glyph_missing_alphabet_chars(self):
        """Test pinyin glyph creation with missing alphabet characters."""
        # Create pinyin glyph with limited alphabet
        font_data = {
            "cmap": {"19968": "uni4E00"},
            "glyf": {"uni4E00": {"advanceWidth": 1000, "advanceHeight": 1000}},
        }

        alphabet_data = {
            "z": {"advanceWidth": 400, "advanceHeight": 700},
            "h": {"advanceWidth": 500, "advanceHeight": 700},
            # Missing "ō", "n", "g"
        }

        with patch("builtins.open", mock_open()):
            with patch("orjson.loads") as mock_json:
                with patch(
                    "refactored.glyph.pinyin_glyph.get_pinyin_table_with_mapping_table",
                    return_value={},
                ):
                    mock_json.side_effect = [font_data, alphabet_data]

                    pinyin_glyph = PinyinGlyph(
                        template_main_json="/mock/template.json",
                        alphabet_for_pinyin_json="/mock/alphabet.json",
                        font_type=FontType.HAN_SERIF,
                    )

        glyph_data = pinyin_glyph._create_pinyin_glyph("zhōng")

        # Should only create references for available characters (z, h)
        assert len(glyph_data["references"]) == 2
        assert glyph_data["references"][0]["glyph"] == "z"
        assert glyph_data["references"][1]["glyph"] == "h"


class TestPinyinGlyphBulkOperations:
    """Test bulk operations and edge cases."""

    @pytest.mark.unit
    def test_get_all_pinyin_glyphs(self):
        """Test getting all pinyin glyphs from mapping table."""
        font_data = {
            "cmap": {"19968": "uni4E00"},
            "glyf": {"uni4E00": {"advanceWidth": 1000, "advanceHeight": 1000}},
        }

        alphabet_data = {
            "g": {"advanceWidth": 400, "advanceHeight": 700},
            "u": {"advanceWidth": 500, "advanceHeight": 700},
            "ó": {"advanceWidth": 500, "advanceHeight": 800},
            "h": {"advanceWidth": 500, "advanceHeight": 700},
            "ǎ": {"advanceWidth": 500, "advanceHeight": 800},
            "o": {"advanceWidth": 500, "advanceHeight": 700},
        }

        pinyin_table = {"国": ["guó"], "好": ["hǎo", "hào"]}

        with patch("builtins.open", mock_open()):
            with patch("orjson.loads") as mock_json:
                with patch(
                    "refactored.glyph.pinyin_glyph.get_pinyin_table_with_mapping_table",
                    return_value=pinyin_table,
                ):
                    mock_json.side_effect = [font_data, alphabet_data]

                    pinyin_glyph = PinyinGlyph(
                        template_main_json="/mock/template.json",
                        alphabet_for_pinyin_json="/mock/alphabet.json",
                        font_type=FontType.HAN_SERIF,
                    )

        all_glyphs = pinyin_glyph.get_all_pinyin_glyphs()

        # Should have glyphs for all unique pronunciations
        expected_pronunciations = {"guó", "hǎo", "hào"}
        assert set(all_glyphs.keys()) == expected_pronunciations

        # Each glyph should have proper structure
        for pronunciation, glyph_data in all_glyphs.items():
            assert isinstance(glyph_data, dict)
            assert "advanceWidth" in glyph_data
            assert "advanceHeight" in glyph_data
            assert "references" in glyph_data

    @pytest.mark.unit
    def test_get_all_pinyin_glyphs_empty_table(self):
        """Test getting all pinyin glyphs with empty mapping table."""
        font_data = {
            "cmap": {"19968": "uni4E00"},
            "glyf": {"uni4E00": {"advanceWidth": 1000, "advanceHeight": 1000}},
        }

        with patch("builtins.open", mock_open()):
            with patch("orjson.loads") as mock_json:
                with patch(
                    "refactored.glyph.pinyin_glyph.get_pinyin_table_with_mapping_table",
                    return_value={},
                ):
                    mock_json.side_effect = [font_data, {}]

                    pinyin_glyph = PinyinGlyph(
                        template_main_json="/mock/template.json",
                        alphabet_for_pinyin_json="/mock/alphabet.json",
                        font_type=FontType.HAN_SERIF,
                    )

        all_glyphs = pinyin_glyph.get_all_pinyin_glyphs()

        # Should return empty dict for empty mapping table
        assert all_glyphs == {}

    @pytest.mark.unit
    def test_get_all_pinyin_glyphs_deduplication(self):
        """Test that duplicate pronunciations are not duplicated in output."""
        font_data = {
            "cmap": {"19968": "uni4E00"},
            "glyf": {"uni4E00": {"advanceWidth": 1000, "advanceHeight": 1000}},
        }

        alphabet_data = {
            "h": {"advanceWidth": 400, "advanceHeight": 700},
            "a": {"advanceWidth": 500, "advanceHeight": 700},
            "o": {"advanceWidth": 500, "advanceHeight": 700},
        }

        pinyin_table = {
            "好": ["hao"],
            "号": ["hao"],  # Same pronunciation as "好"
            "毫": ["hao"],  # Same pronunciation as well
        }

        with patch("builtins.open", mock_open()):
            with patch("orjson.loads") as mock_json:
                with patch(
                    "refactored.glyph.pinyin_glyph.get_pinyin_table_with_mapping_table",
                    return_value=pinyin_table,
                ):
                    mock_json.side_effect = [font_data, alphabet_data]

                    pinyin_glyph = PinyinGlyph(
                        template_main_json="/mock/template.json",
                        alphabet_for_pinyin_json="/mock/alphabet.json",
                        font_type=FontType.HAN_SERIF,
                    )

        all_glyphs = pinyin_glyph.get_all_pinyin_glyphs()

        # Should only have one entry for "hao" despite multiple characters having it
        assert len(all_glyphs) == 1
        assert "hao" in all_glyphs


class TestPinyinGlyphConstants:
    """Test module-level constants and their usage."""

    @pytest.mark.unit
    def test_constants_values(self):
        """Test that module constants have expected values."""
        # These constants should be stable and not change unexpectedly
        assert VERTICAL_ORIGIN_PER_HEIGHT == 0.88
        assert HEIGHT_RATE_OF_MONOSPACE == 1.4
        assert DELTA_4_REFLECTION == 0.001

    @pytest.mark.unit
    def test_constants_usage_in_height_calculation(self):
        """Test that HEIGHT_RATE_OF_MONOSPACE is used correctly."""
        font_data = {
            "cmap": {"19968": "uni4E00"},
            "glyf": {
                "uni4E00": {
                    "advanceWidth": 1000
                    # No advanceHeight - should use calculated value
                }
            },
        }

        with patch("builtins.open", mock_open()):
            with patch("orjson.loads") as mock_json:
                with patch(
                    "refactored.glyph.pinyin_glyph.get_pinyin_table_with_mapping_table",
                    return_value={},
                ):
                    mock_json.side_effect = [font_data, {}]

                    pinyin_glyph = PinyinGlyph(
                        template_main_json="/mock/template.json",
                        alphabet_for_pinyin_json="/mock/alphabet.json",
                        font_type=FontType.HAN_SERIF,
                    )

        width, height = pinyin_glyph._PinyinGlyph__get_advance_size_of_hanzi()

        # Height should be width * HEIGHT_RATE_OF_MONOSPACE
        expected_height = 1000 * HEIGHT_RATE_OF_MONOSPACE
        assert height == expected_height


class TestPinyinGlyphErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.unit
    def test_zero_dimensions_handling(self):
        """Test handling of zero dimensions in scaling calculations."""
        font_data = {
            "cmap": {"19968": "uni4E00"},
            "glyf": {"uni4E00": {"advanceWidth": 1000, "advanceHeight": 1000}},
        }

        alphabet_data = {
            "a": {"advanceWidth": 0, "advanceHeight": 0}  # Zero dimensions
        }

        with patch("builtins.open", mock_open()):
            with patch("orjson.loads") as mock_json:
                with patch(
                    "refactored.glyph.pinyin_glyph.get_pinyin_table_with_mapping_table",
                    return_value={},
                ):
                    mock_json.side_effect = [font_data, alphabet_data]

                    pinyin_glyph = PinyinGlyph(
                        template_main_json="/mock/template.json",
                        alphabet_for_pinyin_json="/mock/alphabet.json",
                        font_type=FontType.HAN_SERIF,
                    )

        # Should handle zero dimensions gracefully
        glyph_data = pinyin_glyph._create_pinyin_glyph("a")

        # Should not raise division by zero error
        assert isinstance(glyph_data, dict)
        assert len(glyph_data["references"]) == 1

        # Scale factors should default to 1.0 for zero dimensions
        ref = glyph_data["references"][0]
        assert ref["scaleX"] == 1.0  # canvas_width / 0 -> defaults to 1.0
        assert ref["scaleY"] == 1.0  # canvas_height / 0 -> defaults to 1.0

    @pytest.mark.unit
    def test_empty_pronunciation_handling(self):
        """Test handling of empty pronunciation string."""
        font_data = {
            "cmap": {"19968": "uni4E00"},
            "glyf": {"uni4E00": {"advanceWidth": 1000, "advanceHeight": 1000}},
        }

        with patch("builtins.open", mock_open()):
            with patch("orjson.loads") as mock_json:
                with patch(
                    "refactored.glyph.pinyin_glyph.get_pinyin_table_with_mapping_table",
                    return_value={},
                ):
                    mock_json.side_effect = [font_data, {}]

                    pinyin_glyph = PinyinGlyph(
                        template_main_json="/mock/template.json",
                        alphabet_for_pinyin_json="/mock/alphabet.json",
                        font_type=FontType.HAN_SERIF,
                    )

        # Should handle empty pronunciation gracefully
        glyph_data = pinyin_glyph._create_pinyin_glyph("")

        assert isinstance(glyph_data, dict)
        assert glyph_data["references"] == []  # No characters to reference
        assert glyph_data["advanceWidth"] == 1000
        assert glyph_data["advanceHeight"] == 1000

    @pytest.mark.unit
    def test_malformed_font_data_handling(self):
        """Test handling of malformed font data."""
        malformed_font_data = {
            "cmap": {"19968": "uni4E00"},
            "glyf": {
                "uni4E00": {
                    # Missing required advanceWidth
                    "advanceHeight": 1000
                }
            },
        }

        with patch("builtins.open", mock_open()):
            with patch("orjson.loads") as mock_json:
                with patch(
                    "refactored.glyph.pinyin_glyph.get_pinyin_table_with_mapping_table",
                    return_value={},
                ):
                    mock_json.side_effect = [malformed_font_data, {}]

                    pinyin_glyph = PinyinGlyph(
                        template_main_json="/mock/template.json",
                        alphabet_for_pinyin_json="/mock/alphabet.json",
                        font_type=FontType.HAN_SERIF,
                    )

        # Should raise KeyError for missing advanceWidth
        with pytest.raises(KeyError):
            pinyin_glyph._PinyinGlyph__get_advance_size_of_hanzi()

    @pytest.mark.unit
    def test_missing_hanzi_reference_handling(self):
        """Test handling when reference hanzi is missing from font."""
        font_data = {"cmap": {}, "glyf": {}}  # Empty cmap - no hanzi mapping

        with patch("builtins.open", mock_open()):
            with patch("orjson.loads") as mock_json:
                with patch(
                    "refactored.glyph.pinyin_glyph.get_pinyin_table_with_mapping_table",
                    return_value={},
                ):
                    mock_json.side_effect = [font_data, {}]

                    pinyin_glyph = PinyinGlyph(
                        template_main_json="/mock/template.json",
                        alphabet_for_pinyin_json="/mock/alphabet.json",
                        font_type=FontType.HAN_SERIF,
                    )

        # Should raise KeyError when trying to get size of missing hanzi "一"
        with pytest.raises(KeyError):
            pinyin_glyph._PinyinGlyph__get_advance_size_of_hanzi()
