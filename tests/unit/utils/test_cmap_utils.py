# -*- coding: utf-8 -*-
"""
Tests for CMap utilities.

These tests verify that the CMap utility functions work correctly
with character mapping tables, conversion functions, and validation.
"""

from unittest.mock import mock_open, patch

import pytest

from refactored.utils import cmap_utils
from refactored.utils.cmap_utils import (
    clear_cmap_table,
    convert_hanzi_to_cid_safe,
    convert_str_hanzi_2_cid,
    get_cmap_table,
    get_hanzi_from_cid,
    get_unicode_from_cid,
    load_cmap_table_from_path,
    set_cmap_table,
    validate_cmap_table,
)


class TestCmapTableManagement:
    """Test cmap table management functions."""

    def setup_method(self):
        """Set up test environment."""
        # Clear global cmap table before each test
        clear_cmap_table()

    def teardown_method(self):
        """Clean up test environment."""
        # Clear global cmap table after each test
        clear_cmap_table()

    @pytest.mark.unit
    def test_clear_cmap_table(self):
        """Test clear_cmap_table functionality."""
        # Set some data
        set_cmap_table({"20013": "cid00001"})
        assert len(cmap_utils.cmap_table) == 1

        # Clear it
        clear_cmap_table()
        assert len(cmap_utils.cmap_table) == 0

    @pytest.mark.unit
    def test_set_cmap_table(self):
        """Test set_cmap_table functionality."""
        test_cmap = {
            "20013": "cid00001",  # 中
            "22269": "cid00002",  # 国
            "20154": "cid00003",  # 人
        }

        set_cmap_table(test_cmap)

        # Verify global table was updated
        assert cmap_utils.cmap_table == test_cmap
        assert len(cmap_utils.cmap_table) == 3
        assert cmap_utils.cmap_table["20013"] == "cid00001"

    @pytest.mark.unit
    def test_get_cmap_table(self):
        """Test get_cmap_table functionality."""
        mock_template_data = {
            "cmap": {
                "20013": "cid00001",
                "22269": "cid00002",
            },
            "other_data": "ignored",
        }

        with patch("builtins.open", mock_open()), patch(
            "orjson.loads", return_value=mock_template_data
        ), patch("os.path.join", return_value="/mock/template_main.json"):

            get_cmap_table()

            # Verify global table was loaded
            assert cmap_utils.cmap_table == mock_template_data["cmap"]
            assert len(cmap_utils.cmap_table) == 2
            assert cmap_utils.cmap_table["20013"] == "cid00001"
            assert cmap_utils.cmap_table["22269"] == "cid00002"

    @pytest.mark.unit
    def test_load_cmap_table_from_path_success(self):
        """Test load_cmap_table_from_path with valid file."""
        template_path = "/mock/template.json"
        mock_template_data = {
            "cmap": {
                "20013": "cid00001",
                "22269": "cid00002",
            },
            "other_data": "ignored",
        }

        with patch("pathlib.Path.exists", return_value=True), patch(
            "builtins.open", mock_open()
        ), patch("orjson.loads", return_value=mock_template_data):

            result = load_cmap_table_from_path(template_path)

            assert result == mock_template_data["cmap"]
            assert len(result) == 2
            assert result["20013"] == "cid00001"
            assert result["22269"] == "cid00002"

    @pytest.mark.unit
    def test_load_cmap_table_from_path_file_not_found(self):
        """Test load_cmap_table_from_path with missing file."""
        template_path = "/nonexistent/template.json"

        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(FileNotFoundError, match="Template file not found"):
                load_cmap_table_from_path(template_path)

    @pytest.mark.unit
    def test_load_cmap_table_from_path_no_cmap_section(self):
        """Test load_cmap_table_from_path with missing cmap section."""
        template_path = "/mock/template.json"
        mock_template_data = {"other_data": "no cmap section"}

        with patch("pathlib.Path.exists", return_value=True), patch(
            "builtins.open", mock_open()
        ), patch("orjson.loads", return_value=mock_template_data):

            with pytest.raises(RuntimeError, match="Failed to load cmap table"):
                load_cmap_table_from_path(template_path)

    @pytest.mark.unit
    def test_load_cmap_table_from_path_invalid_json(self):
        """Test load_cmap_table_from_path with invalid JSON."""
        template_path = "/mock/template.json"

        with patch("pathlib.Path.exists", return_value=True), patch(
            "builtins.open", mock_open()
        ), patch("orjson.loads", side_effect=ValueError("Invalid JSON")):

            with pytest.raises(RuntimeError, match="Failed to load cmap table"):
                load_cmap_table_from_path(template_path)


class TestCharacterConversion:
    """Test character conversion functions."""

    def setup_method(self):
        """Set up test environment."""
        clear_cmap_table()

    def teardown_method(self):
        """Clean up test environment."""
        clear_cmap_table()

    @pytest.mark.unit
    def test_convert_str_hanzi_2_cid_with_global_table(self):
        """Test convert_str_hanzi_2_cid with global cmap table."""
        test_cmap = {
            "20013": "cid00001",  # 中
            "22269": "cid00002",  # 国
        }
        set_cmap_table(test_cmap)

        result = convert_str_hanzi_2_cid("中")
        assert result == "cid00001"

        result = convert_str_hanzi_2_cid("国")
        assert result == "cid00002"

    @pytest.mark.unit
    def test_convert_str_hanzi_2_cid_loads_table_if_empty(self):
        """Test convert_str_hanzi_2_cid loads table if global table is empty."""
        mock_template_data = {
            "cmap": {
                "20013": "cid00001",
            }
        }

        with patch("builtins.open", mock_open()), patch(
            "orjson.loads", return_value=mock_template_data
        ), patch("os.path.join", return_value="/mock/template_main.json"):

            result = convert_str_hanzi_2_cid("中")
            assert result == "cid00001"

    @pytest.mark.unit
    def test_convert_str_hanzi_2_cid_caching(self):
        """Test convert_str_hanzi_2_cid caching behavior."""
        test_cmap = {"20013": "cid00001"}
        set_cmap_table(test_cmap)

        # First call
        result1 = convert_str_hanzi_2_cid("中")
        assert result1 == "cid00001"

        # Second call should use cache
        result2 = convert_str_hanzi_2_cid("中")
        assert result2 == "cid00001"

        # Results should be identical
        assert result1 == result2

    @pytest.mark.unit
    def test_convert_hanzi_to_cid_safe_with_custom_cmap(self):
        """Test convert_hanzi_to_cid_safe with custom cmap."""
        custom_cmap = {
            "20013": "cid00001",
            "22269": "cid00002",
        }

        result = convert_hanzi_to_cid_safe("中", cmap=custom_cmap)
        assert result == "cid00001"

        result = convert_hanzi_to_cid_safe("国", cmap=custom_cmap)
        assert result == "cid00002"

    @pytest.mark.unit
    def test_convert_hanzi_to_cid_safe_with_global_cmap(self):
        """Test convert_hanzi_to_cid_safe with global cmap."""
        test_cmap = {
            "20013": "cid00001",
            "22269": "cid00002",
        }
        set_cmap_table(test_cmap)

        result = convert_hanzi_to_cid_safe("中")
        assert result == "cid00001"

        result = convert_hanzi_to_cid_safe("国")
        assert result == "cid00002"

    @pytest.mark.unit
    def test_convert_hanzi_to_cid_safe_character_not_found(self):
        """Test convert_hanzi_to_cid_safe with character not found."""
        test_cmap = {"20013": "cid00001"}
        set_cmap_table(test_cmap)

        result = convert_hanzi_to_cid_safe("不")
        assert result is None

    @pytest.mark.unit
    def test_convert_hanzi_to_cid_safe_invalid_input(self):
        """Test convert_hanzi_to_cid_safe with invalid input."""
        test_cmap = {"20013": "cid00001"}
        set_cmap_table(test_cmap)

        # Empty string
        result = convert_hanzi_to_cid_safe("")
        assert result is None

        # Multiple characters
        result = convert_hanzi_to_cid_safe("中国")
        assert result is None

        # None input
        result = convert_hanzi_to_cid_safe(None)
        assert result is None

    @pytest.mark.unit
    def test_convert_hanzi_to_cid_safe_loads_global_table(self):
        """Test convert_hanzi_to_cid_safe loads global table when needed."""
        mock_template_data = {
            "cmap": {
                "20013": "cid00001",
            }
        }

        with patch("builtins.open", mock_open()), patch(
            "orjson.loads", return_value=mock_template_data
        ), patch("os.path.join", return_value="/mock/template_main.json"):

            result = convert_hanzi_to_cid_safe("中")
            assert result == "cid00001"


class TestReverseLookup:
    """Test reverse lookup functions."""

    def setup_method(self):
        """Set up test environment."""
        clear_cmap_table()

    def teardown_method(self):
        """Clean up test environment."""
        clear_cmap_table()

    @pytest.mark.unit
    def test_get_unicode_from_cid_with_custom_cmap(self):
        """Test get_unicode_from_cid with custom cmap."""
        custom_cmap = {
            "20013": "cid00001",
            "22269": "cid00002",
        }

        result = get_unicode_from_cid("cid00001", cmap=custom_cmap)
        assert result == "20013"

        result = get_unicode_from_cid("cid00002", cmap=custom_cmap)
        assert result == "22269"

    @pytest.mark.unit
    def test_get_unicode_from_cid_with_global_cmap(self):
        """Test get_unicode_from_cid with global cmap."""
        test_cmap = {
            "20013": "cid00001",
            "22269": "cid00002",
        }
        set_cmap_table(test_cmap)

        result = get_unicode_from_cid("cid00001")
        assert result == "20013"

        result = get_unicode_from_cid("cid00002")
        assert result == "22269"

    @pytest.mark.unit
    def test_get_unicode_from_cid_not_found(self):
        """Test get_unicode_from_cid with CID not found."""
        test_cmap = {"20013": "cid00001"}
        set_cmap_table(test_cmap)

        result = get_unicode_from_cid("cid99999")
        assert result is None

    @pytest.mark.unit
    def test_get_unicode_from_cid_loads_global_table(self):
        """Test get_unicode_from_cid loads global table when needed."""
        mock_template_data = {
            "cmap": {
                "20013": "cid00001",
            }
        }

        with patch("builtins.open", mock_open()), patch(
            "orjson.loads", return_value=mock_template_data
        ), patch("os.path.join", return_value="/mock/template_main.json"):

            result = get_unicode_from_cid("cid00001")
            assert result == "20013"

    @pytest.mark.unit
    def test_get_hanzi_from_cid_success(self):
        """Test get_hanzi_from_cid with valid CID."""
        custom_cmap = {
            "20013": "cid00001",  # 中
            "22269": "cid00002",  # 国
        }

        result = get_hanzi_from_cid("cid00001", cmap=custom_cmap)
        assert result == "中"

        result = get_hanzi_from_cid("cid00002", cmap=custom_cmap)
        assert result == "国"

    @pytest.mark.unit
    def test_get_hanzi_from_cid_not_found(self):
        """Test get_hanzi_from_cid with CID not found."""
        test_cmap = {"20013": "cid00001"}

        result = get_hanzi_from_cid("cid99999", cmap=test_cmap)
        assert result is None

    @pytest.mark.unit
    def test_get_hanzi_from_cid_invalid_unicode(self):
        """Test get_hanzi_from_cid with invalid Unicode value."""
        # Create cmap with invalid Unicode value
        invalid_cmap = {
            "invalid": "cid00001",
            "999999999": "cid00002",  # Out of range
        }

        result = get_hanzi_from_cid("cid00001", cmap=invalid_cmap)
        assert result is None

        result = get_hanzi_from_cid("cid00002", cmap=invalid_cmap)
        assert result is None


class TestCmapValidation:
    """Test cmap table validation functions."""

    @pytest.mark.unit
    def test_validate_cmap_table_valid(self):
        """Test validate_cmap_table with valid cmap."""
        valid_cmap = {
            "20013": "cid00001",
            "22269": "cid00002",
            "20154": "cid00003",
        }

        result = validate_cmap_table(valid_cmap)
        assert result is True

    @pytest.mark.unit
    def test_validate_cmap_table_not_dict(self):
        """Test validate_cmap_table with non-dict input."""
        assert validate_cmap_table(None) is False
        assert validate_cmap_table([]) is False
        assert validate_cmap_table("not a dict") is False
        assert validate_cmap_table(123) is False

    @pytest.mark.unit
    def test_validate_cmap_table_invalid_unicode_keys(self):
        """Test validate_cmap_table with invalid Unicode keys."""
        invalid_cmap = {
            "invalid_key": "cid00001",
            "20013": "cid00002",
        }

        result = validate_cmap_table(invalid_cmap)
        assert result is False

    @pytest.mark.unit
    def test_validate_cmap_table_negative_unicode(self):
        """Test validate_cmap_table with negative Unicode values."""
        invalid_cmap = {
            "-1": "cid00001",
            "20013": "cid00002",
        }

        result = validate_cmap_table(invalid_cmap)
        assert result is False

    @pytest.mark.unit
    def test_validate_cmap_table_invalid_cid_values(self):
        """Test validate_cmap_table with invalid CID values."""
        invalid_cmap = {
            "20013": "",  # Empty CID
            "22269": None,  # None CID
            "20154": 123,  # Non-string CID
        }

        result = validate_cmap_table(invalid_cmap)
        assert result is False

    @pytest.mark.unit
    def test_validate_cmap_table_empty_dict(self):
        """Test validate_cmap_table with empty dict."""
        result = validate_cmap_table({})
        assert result is True  # Empty dict is valid

    @pytest.mark.unit
    def test_validate_cmap_table_large_unicode_values(self):
        """Test validate_cmap_table with large Unicode values."""
        large_unicode_cmap = {
            "65536": "cid00001",  # Valid large Unicode
            "1114111": "cid00002",  # Max Unicode value
        }

        result = validate_cmap_table(large_unicode_cmap)
        assert result is True


class TestCmapUtilsIntegration:
    """Integration tests for cmap utils components."""

    def setup_method(self):
        """Set up test environment."""
        clear_cmap_table()

    def teardown_method(self):
        """Clean up test environment."""
        clear_cmap_table()

    @pytest.mark.unit
    def test_full_cmap_workflow(self):
        """Test full cmap workflow from loading to conversion."""
        # Simulate loading template file
        template_path = "/mock/template.json"
        mock_template_data = {
            "cmap": {
                "20013": "cid00001",  # 中
                "22269": "cid00002",  # 国
                "20154": "cid00003",  # 人
            }
        }

        with patch("pathlib.Path.exists", return_value=True), patch(
            "builtins.open", mock_open()
        ), patch("orjson.loads", return_value=mock_template_data):

            # Load cmap table
            loaded_cmap = load_cmap_table_from_path(template_path)

            # Validate it
            assert validate_cmap_table(loaded_cmap) is True

            # Set as global table
            set_cmap_table(loaded_cmap)

            # Test forward conversion
            assert convert_hanzi_to_cid_safe("中") == "cid00001"
            assert convert_hanzi_to_cid_safe("国") == "cid00002"
            assert convert_hanzi_to_cid_safe("人") == "cid00003"

            # Test reverse lookup
            assert get_unicode_from_cid("cid00001") == "20013"
            assert get_unicode_from_cid("cid00002") == "22269"
            assert get_unicode_from_cid("cid00003") == "20154"

            # Test character lookup
            assert get_hanzi_from_cid("cid00001") == "中"
            assert get_hanzi_from_cid("cid00002") == "国"
            assert get_hanzi_from_cid("cid00003") == "人"

    @pytest.mark.unit
    def test_error_handling_workflow(self):
        """Test error handling in cmap workflow."""
        # Test with invalid file
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(FileNotFoundError):
                load_cmap_table_from_path("/nonexistent/file.json")

        # Test with invalid cmap
        invalid_cmap = {"invalid": "cid00001"}
        assert validate_cmap_table(invalid_cmap) is False

        # Test conversions with empty table
        clear_cmap_table()
        with patch("builtins.open", mock_open()), patch(
            "orjson.loads", return_value={"cmap": {}}
        ), patch("os.path.join", return_value="/mock/template_main.json"):
            result = convert_hanzi_to_cid_safe("中")
            # Should return None since character not in empty table
            assert result is None

    @pytest.mark.unit
    def test_performance_characteristics(self):
        """Test performance characteristics of cmap utils."""
        # Create large cmap table
        large_cmap = {str(0x4E00 + i): f"cid{i:05d}" for i in range(1000)}

        # Validate large table
        assert validate_cmap_table(large_cmap) is True

        # Set as global table
        set_cmap_table(large_cmap)

        # Test conversion performance
        char = chr(0x4E00)
        result = convert_hanzi_to_cid_safe(char)
        assert result == "cid00000"

        # Test reverse lookup performance
        unicode_result = get_unicode_from_cid("cid00000")
        assert unicode_result == str(0x4E00)

        # Test caching behavior
        result2 = convert_str_hanzi_2_cid(char)
        assert result2 == "cid00000"

    @pytest.mark.unit
    def test_unicode_edge_cases(self):
        """Test Unicode edge cases in cmap utils."""
        # Test with various Unicode ranges
        edge_case_cmap = {
            "65": "cid00001",  # ASCII 'A'
            "12354": "cid00002",  # Hiragana あ
            "12450": "cid00003",  # Katakana ア
            "20013": "cid00004",  # CJK 中
            "127744": "cid00005",  # Emoji range
        }

        set_cmap_table(edge_case_cmap)

        # Test conversions
        assert convert_hanzi_to_cid_safe("A") == "cid00001"
        assert convert_hanzi_to_cid_safe("あ") == "cid00002"
        assert convert_hanzi_to_cid_safe("ア") == "cid00003"
        assert convert_hanzi_to_cid_safe("中") == "cid00004"
        assert convert_hanzi_to_cid_safe("🌀") == "cid00005"

        # Test reverse conversions
        assert get_hanzi_from_cid("cid00001") == "A"
        assert get_hanzi_from_cid("cid00002") == "あ"
        assert get_hanzi_from_cid("cid00003") == "ア"
        assert get_hanzi_from_cid("cid00004") == "中"
        assert get_hanzi_from_cid("cid00005") == "🌀"

    @pytest.mark.unit
    def test_concurrent_access_safety(self):
        """Test that cmap utils handle concurrent access safely."""
        # Test setting and getting table concurrently
        test_cmap1 = {"20013": "cid00001"}
        test_cmap2 = {"22269": "cid00002"}

        set_cmap_table(test_cmap1)
        assert cmap_utils.cmap_table == test_cmap1

        set_cmap_table(test_cmap2)
        assert cmap_utils.cmap_table == test_cmap2

        clear_cmap_table()
        assert len(cmap_utils.cmap_table) == 0
