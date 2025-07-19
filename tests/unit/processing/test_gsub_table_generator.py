# -*- coding: utf-8 -*-
"""
Tests for GSUBTableGenerator class.

These tests verify the OpenType GSUB table generation functionality including
contextual substitutions, pattern processing, and legacy compatibility.
Following TDD principles with comprehensive coverage of all generation phases.
"""

from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from refactored.config import FontConstants
from refactored.data import CharacterDataManager, MappingDataManager
from refactored.processing.gsub_table_generator import GSUBTableGenerator


class TestGSUBTableGeneratorInitialization:
    """Test GSUBTableGenerator initialization and setup."""

    def _create_mock_managers(self):
        """Create mock managers for testing."""
        character_manager = Mock(spec=CharacterDataManager)
        mapping_manager = Mock(spec=MappingDataManager)
        return character_manager, mapping_manager

    def _create_mock_cmap_table(self):
        """Create mock cmap table."""
        return {
            "19968": "uni4E00",  # 一
            "20013": "uni4E2D",  # 中
            "22269": "uni570D",  # 國
            "34892": "uni884C",  # 行
        }

    @pytest.mark.unit
    def test_initialization_basic(self):
        """Test basic GSUBTableGenerator initialization."""
        character_manager, mapping_manager = self._create_mock_managers()
        cmap_table = self._create_mock_cmap_table()

        generator = GSUBTableGenerator(
            pattern_one_path=Path("/mock/pattern_one.txt"),
            pattern_two_path=Path("/mock/pattern_two.json"),
            exception_pattern_path=Path("/mock/exception.json"),
            character_manager=character_manager,
            mapping_manager=mapping_manager,
            cmap_table=cmap_table,
        )

        # Verify initialization
        assert generator.pattern_one_path == Path("/mock/pattern_one.txt")
        assert generator.pattern_two_path == Path("/mock/pattern_two.json")
        assert generator.exception_pattern_path == Path("/mock/exception.json")
        assert generator.character_manager is character_manager
        assert generator.mapping_manager is mapping_manager
        assert generator.cmap_table is cmap_table
        assert generator.lookup_order == set()
        assert generator.pattern_one == [{}]
        assert generator.pattern_two == {}
        assert generator.exception_pattern == {}

    @pytest.mark.unit
    def test_initialization_gsub_structure(self):
        """Test that initial GSUB structure matches legacy format."""
        character_manager, mapping_manager = self._create_mock_managers()
        cmap_table = self._create_mock_cmap_table()

        generator = GSUBTableGenerator(
            pattern_one_path=Path("/mock/pattern_one.txt"),
            pattern_two_path=Path("/mock/pattern_two.json"),
            exception_pattern_path=Path("/mock/exception.json"),
            character_manager=character_manager,
            mapping_manager=mapping_manager,
            cmap_table=cmap_table,
        )

        gsub_data = generator.gsub_data

        # Verify language tables
        assert "languages" in gsub_data
        assert "DFLT_DFLT" in gsub_data["languages"]
        assert "hani_DFLT" in gsub_data["languages"]
        assert gsub_data["languages"]["DFLT_DFLT"]["features"] == [
            "aalt_00000",
            "rclt_00002",
        ]
        assert gsub_data["languages"]["hani_DFLT"]["features"] == [
            "aalt_00001",
            "rclt_00003",
        ]

        # Verify feature tables
        assert "features" in gsub_data
        assert gsub_data["features"]["aalt_00000"] == ["lookup_aalt_0", "lookup_aalt_1"]
        assert gsub_data["features"]["aalt_00001"] == ["lookup_aalt_0", "lookup_aalt_1"]
        assert gsub_data["features"]["rclt_00002"] == [
            "lookup_rclt_2",
            "lookup_rclt_3",
            "lookup_rclt_4",
        ]
        assert gsub_data["features"]["rclt_00003"] == [
            "lookup_rclt_2",
            "lookup_rclt_3",
            "lookup_rclt_4",
        ]

        # Verify initial lookup structure
        assert "lookups" in gsub_data
        lookups = gsub_data["lookups"]

        # Check aalt lookups
        assert "lookup_aalt_0" in lookups
        assert lookups["lookup_aalt_0"]["type"] == "gsub_single"
        assert lookups["lookup_aalt_0"]["subtables"] == [{}]

        assert "lookup_aalt_1" in lookups
        assert lookups["lookup_aalt_1"]["type"] == "gsub_alternate"

        # Check rclt lookups
        assert "lookup_rclt_2" in lookups
        assert lookups["lookup_rclt_2"]["type"] == "gsub_chaining"
        assert lookups["lookup_rclt_2"]["subtables"] == []

        # Verify initial lookup order
        assert gsub_data["lookupOrder"] == ["lookup_aalt_0"]


class TestGSUBTableGeneratorPatternLoading:
    """Test pattern file loading functionality."""

    def _create_test_generator(
        self, pattern_one_exists=True, pattern_two_exists=True, exception_exists=True
    ):
        """Create test generator with mock file existence."""
        character_manager = Mock(spec=CharacterDataManager)
        mapping_manager = Mock(spec=MappingDataManager)
        cmap_table = {"19968": "uni4E00", "20013": "uni4E2D"}

        pattern_one_path = Mock(spec=Path)
        pattern_one_path.exists.return_value = pattern_one_exists

        pattern_two_path = Mock(spec=Path)
        pattern_two_path.exists.return_value = pattern_two_exists

        exception_path = Mock(spec=Path)
        exception_path.exists.return_value = exception_exists

        return GSUBTableGenerator(
            pattern_one_path=pattern_one_path,
            pattern_two_path=pattern_two_path,
            exception_pattern_path=exception_path,
            character_manager=character_manager,
            mapping_manager=mapping_manager,
            cmap_table=cmap_table,
        )

    @pytest.mark.unit
    def test_load_pattern_one_file(self):
        """Test loading pattern one file."""
        generator = self._create_test_generator(
            pattern_one_exists=True, pattern_two_exists=False, exception_exists=False
        )

        # Mock pattern one file content
        pattern_one_content = [
            "1, 中, zhōng, [~的~之]\n",
            "2, 中, zhòng, [~心~央]\n",
            "3, 中, zhòng, [打~|中~意]\n",
        ]

        with patch("builtins.open", mock_open(read_data="".join(pattern_one_content))):
            generator._load_pattern_data()

        # Verify pattern one data (order 1 is skipped, order 2+ becomes index 0+)
        assert len(generator.pattern_one) == 2  # Orders 2 and 3 -> indices 0 and 1

        # Order 2 -> index 0
        assert "中" in generator.pattern_one[0]
        assert generator.pattern_one[0]["中"]["variational_pronunciation"] == "zhòng"
        assert generator.pattern_one[0]["中"]["patterns"] == "[~心~央]"

        # Order 3 -> index 1
        assert "中" in generator.pattern_one[1]
        assert generator.pattern_one[1]["中"]["variational_pronunciation"] == "zhòng"
        assert generator.pattern_one[1]["中"]["patterns"] == "[打~|中~意]"

    @pytest.mark.unit
    def test_load_pattern_one_skip_order_1(self):
        """Test that pattern one skips order 1 entries."""
        generator = self._create_test_generator(
            pattern_one_exists=True, pattern_two_exists=False, exception_exists=False
        )

        pattern_one_content = [
            "1, 行, xíng, [~走]\n",  # Should be skipped
            "2, 行, háng, [银~]\n",  # Should be loaded at index 0
        ]

        with patch("builtins.open", mock_open(read_data="".join(pattern_one_content))):
            generator._load_pattern_data()

        # Should only have 1 pattern (order 2 -> index 0)
        assert len(generator.pattern_one) == 1
        assert "行" in generator.pattern_one[0]
        assert generator.pattern_one[0]["行"]["variational_pronunciation"] == "háng"

    @pytest.mark.unit
    def test_load_pattern_two_file(self):
        """Test loading pattern two JSON file."""
        generator = self._create_test_generator()

        pattern_two_data = {
            "lookup_table": {
                "lookup_0": {"中": "中.ss02"},
                "lookup_1": {"国": "国.ss03"},
            },
            "patterns": {"中国": [{"中": "lookup_0"}, {"国": "lookup_1"}]},
        }

        with patch("builtins.open", mock_open()):
            with patch("orjson.loads", return_value=pattern_two_data):
                generator._load_pattern_data()

        assert generator.pattern_two == pattern_two_data
        assert "lookup_table" in generator.pattern_two
        assert "patterns" in generator.pattern_two

    @pytest.mark.unit
    def test_load_exception_pattern_file(self):
        """Test loading exception pattern JSON file."""
        generator = self._create_test_generator()

        exception_data = {
            "lookup_table": {"lookup_exception_0": {"特": "特.ss10"}},
            "patterns": {
                "特别": {"ignore": "特' 别", "pattern": [{"特": "lookup_exception_0"}]}
            },
        }

        with patch("builtins.open", mock_open()):
            with patch(
                "orjson.loads", side_effect=[{}, exception_data]
            ):  # pattern_two empty, exception has data
                generator._load_pattern_data()

        assert generator.exception_pattern == exception_data

    @pytest.mark.unit
    def test_load_pattern_data_nonexistent_files(self):
        """Test loading when pattern files don't exist."""
        generator = self._create_test_generator(
            pattern_one_exists=False, pattern_two_exists=False, exception_exists=False
        )

        generator._load_pattern_data()

        # Should have default empty structures
        assert generator.pattern_one == [{}]
        assert generator.pattern_two == {}
        assert generator.exception_pattern == {}

    @pytest.mark.unit
    def test_load_pattern_one_malformed_lines(self):
        """Test handling of malformed pattern one lines."""
        generator = self._create_test_generator(
            pattern_one_exists=True, pattern_two_exists=False, exception_exists=False
        )

        pattern_one_content = [
            "2, 中, zhòng\n",  # Missing patterns field
            "invalid line\n",  # Completely invalid
            "2, 行, háng, [银~]\n",  # Valid line
        ]

        with patch("builtins.open", mock_open(read_data="".join(pattern_one_content))):
            generator._load_pattern_data()

        # Should only load the valid line
        assert len(generator.pattern_one) == 1
        assert "行" in generator.pattern_one[0]
        assert "中" not in generator.pattern_one[0]  # Malformed line skipped


class TestGSUBTableGeneratorAALTFeature:
    """Test AALT feature generation."""

    def _create_test_generator_with_characters(self):
        """Create generator with mock character data."""
        character_manager = Mock(spec=CharacterDataManager)
        mapping_manager = Mock(spec=MappingDataManager)
        cmap_table = {
            "19968": "uni4E00",  # 一 (single pronunciation)
            "20013": "uni4E2D",  # 中 (multiple pronunciations)
            "22283": "uni570B",  # 國 (multiple pronunciations)
        }

        # Mock single pronunciation characters
        single_char_info = Mock()
        single_char_info.character = "一"
        character_manager.get_single_pronunciation_characters.return_value = [
            single_char_info
        ]

        # Mock multiple pronunciation characters
        multi_char_info_1 = Mock()
        multi_char_info_1.character = "中"
        multi_char_info_1.pronunciations = ["zhōng", "zhòng"]

        multi_char_info_2 = Mock()
        multi_char_info_2.character = "國"
        multi_char_info_2.pronunciations = ["guó"]

        character_manager.get_multiple_pronunciation_characters.return_value = [
            multi_char_info_1,
            multi_char_info_2,
        ]

        return GSUBTableGenerator(
            pattern_one_path=Path("/mock/pattern_one.txt"),
            pattern_two_path=Path("/mock/pattern_two.json"),
            exception_pattern_path=Path("/mock/exception.json"),
            character_manager=character_manager,
            mapping_manager=mapping_manager,
            cmap_table=cmap_table,
        )

    @pytest.mark.unit
    def test_make_aalt_feature_single_pronunciation(self):
        """Test AALT feature for single pronunciation characters."""
        generator = self._create_test_generator_with_characters()

        generator._make_aalt_feature()

        # Check lookup_aalt_0 (single pronunciation)
        aalt_0_subtables = generator.gsub_data["lookups"]["lookup_aalt_0"]["subtables"][
            0
        ]
        assert "uni4E00" in aalt_0_subtables  # 一
        assert aalt_0_subtables["uni4E00"] == "uni4E00.ss00"

        # Verify lookup order tracking
        assert "lookup_aalt_0" in generator.lookup_order

    @pytest.mark.unit
    def test_make_aalt_feature_multiple_pronunciation(self):
        """Test AALT feature for multiple pronunciation characters."""
        generator = self._create_test_generator_with_characters()

        with patch("builtins.print"):  # Suppress debug output
            generator._make_aalt_feature()

        # Check lookup_aalt_1 (multiple pronunciation)
        aalt_1_subtables = generator.gsub_data["lookups"]["lookup_aalt_1"]["subtables"][
            0
        ]

        # 中 has 2 pronunciations -> alternates ss00, ss01, ss02
        assert "uni4E2D" in aalt_1_subtables
        assert aalt_1_subtables["uni4E2D"] == [
            "uni4E2D.ss00",
            "uni4E2D.ss01",
            "uni4E2D.ss02",
        ]

        # 國 has 1 pronunciation -> alternates ss00, ss01
        assert "uni570B" in aalt_1_subtables
        assert aalt_1_subtables["uni570B"] == ["uni570B.ss00", "uni570B.ss01"]

        # Verify lookup order tracking
        assert "lookup_aalt_1" in generator.lookup_order

    @pytest.mark.unit
    def test_make_aalt_feature_missing_cmap(self):
        """Test AALT feature when characters missing from cmap."""
        character_manager = Mock(spec=CharacterDataManager)
        mapping_manager = Mock(spec=MappingDataManager)
        cmap_table = {}  # Empty cmap

        # Mock character data
        single_char_info = Mock()
        single_char_info.character = "missing"
        character_manager.get_single_pronunciation_characters.return_value = [
            single_char_info
        ]
        character_manager.get_multiple_pronunciation_characters.return_value = []

        generator = GSUBTableGenerator(
            pattern_one_path=Path("/mock/pattern_one.txt"),
            pattern_two_path=Path("/mock/pattern_two.json"),
            exception_pattern_path=Path("/mock/exception.json"),
            character_manager=character_manager,
            mapping_manager=mapping_manager,
            cmap_table=cmap_table,
        )

        generator._make_aalt_feature()

        # Should not create entries for missing characters
        aalt_0_subtables = generator.gsub_data["lookups"]["lookup_aalt_0"]["subtables"][
            0
        ]
        assert len(aalt_0_subtables) == 0


class TestGSUBTableGeneratorRCLT0Feature:
    """Test RCLT0 feature generation (pattern one processing)."""

    def _create_test_generator_with_pattern_one(self):
        """Create generator with pattern one data."""
        character_manager = Mock(spec=CharacterDataManager)
        mapping_manager = Mock(spec=MappingDataManager)
        cmap_table = {
            "20013": "uni4E2D",  # 中
            "34892": "uni884C",  # 行
            "30340": "uni7684",  # 的
            "20043": "uni4E4B",  # 之
            "24515": "uni5FC3",  # 心
            "22830": "uni592E",  # 央
            "38134": "uni9280",  # 银
        }

        # Mock mapping manager
        mapping_manager.has_glyph_for_character.return_value = True

        generator = GSUBTableGenerator(
            pattern_one_path=Path("/mock/pattern_one.txt"),
            pattern_two_path=Path("/mock/pattern_two.json"),
            exception_pattern_path=Path("/mock/exception.json"),
            character_manager=character_manager,
            mapping_manager=mapping_manager,
            cmap_table=cmap_table,
        )

        # Set up pattern one data manually
        generator.pattern_one = [
            {  # Index 0 (order 2)
                "中": {"variational_pronunciation": "zhòng", "patterns": "[~心|~央]"}
            },
            {  # Index 1 (order 3)
                "行": {"variational_pronunciation": "háng", "patterns": "[银~]"}
            },
        ]

        return generator

    @pytest.mark.unit
    def test_make_rclt0_feature_creates_lookup_tables(self):
        """Test that RCLT0 creates lookup_11_* tables."""
        generator = self._create_test_generator_with_pattern_one()

        generator._make_rclt0_feature()

        lookups = generator.gsub_data["lookups"]

        # Should create lookup_11_2 and lookup_11_3 (for indices 0 and 1)
        assert "lookup_11_2" in lookups
        assert "lookup_11_3" in lookups

        # Verify structure
        assert lookups["lookup_11_2"]["type"] == "gsub_single"
        assert isinstance(lookups["lookup_11_2"]["subtables"], list)
        assert len(lookups["lookup_11_2"]["subtables"]) == 1

        # Verify lookup order tracking
        assert "lookup_11_2" in generator.lookup_order
        assert "lookup_11_3" in generator.lookup_order

    @pytest.mark.unit
    def test_make_rclt0_feature_substitution_rules(self):
        """Test RCLT0 substitution rules generation."""
        generator = self._create_test_generator_with_pattern_one()

        generator._make_rclt0_feature()

        lookups = generator.gsub_data["lookups"]

        # Check lookup_11_2 substitutions (index 0, SS index = SS_VARIATIONAL_PRONUNCIATION + 0)
        lookup_11_2_subtables = lookups["lookup_11_2"]["subtables"][0]
        ss_index_0 = FontConstants.SS_VARIATIONAL_PRONUNCIATION + 0
        assert "uni4E2D" in lookup_11_2_subtables
        assert lookup_11_2_subtables["uni4E2D"] == f"uni4E2D.ss{ss_index_0:02d}"

        # Check lookup_11_3 substitutions (index 1, SS index = SS_VARIATIONAL_PRONUNCIATION + 1)
        lookup_11_3_subtables = lookups["lookup_11_3"]["subtables"][0]
        ss_index_1 = FontConstants.SS_VARIATIONAL_PRONUNCIATION + 1
        assert "uni884C" in lookup_11_3_subtables
        assert lookup_11_3_subtables["uni884C"] == f"uni884C.ss{ss_index_1:02d}"

    @pytest.mark.unit
    def test_make_rclt0_feature_context_patterns(self):
        """Test RCLT0 contextual pattern generation."""
        generator = self._create_test_generator_with_pattern_one()

        generator._make_rclt0_feature()

        # Check rclt_2 subtables for contextual rules
        rclt_2_subtables = generator.gsub_data["lookups"]["lookup_rclt_2"]["subtables"]

        # Should have contextual rules for pattern "[~心|~央]" and "[银~]"
        assert len(rclt_2_subtables) > 0

        # Verify structure of contextual rules
        for subtable in rclt_2_subtables:
            assert "match" in subtable
            assert "apply" in subtable
            assert "inputBegins" in subtable
            assert "inputEnds" in subtable

    @pytest.mark.unit
    def test_make_rclt0_feature_max_patterns_limit(self):
        """Test RCLT0 maximum patterns limit."""
        character_manager = Mock(spec=CharacterDataManager)
        mapping_manager = Mock(spec=MappingDataManager)
        cmap_table = {}

        generator = GSUBTableGenerator(
            pattern_one_path=Path("/mock/pattern_one.txt"),
            pattern_two_path=Path("/mock/pattern_two.json"),
            exception_pattern_path=Path("/mock/exception.json"),
            character_manager=character_manager,
            mapping_manager=mapping_manager,
            cmap_table=cmap_table,
        )

        # Create 11 patterns (exceeds limit of 10)
        generator.pattern_one = [{} for _ in range(11)]

        with pytest.raises(
            ValueError, match="Maximum 10 pronunciation patterns supported"
        ):
            generator._make_rclt0_feature()

    @pytest.mark.unit
    def test_make_rclt0_feature_no_glyph_available(self):
        """Test RCLT0 when no glyph available for character."""
        generator = self._create_test_generator_with_pattern_one()

        # Mock mapping manager to return False
        generator.mapping_manager.has_glyph_for_character.return_value = False

        generator._make_rclt0_feature()

        # Should create lookup tables but no substitutions
        lookups = generator.gsub_data["lookups"]
        lookup_11_2_subtables = lookups["lookup_11_2"]["subtables"][0]
        lookup_11_3_subtables = lookups["lookup_11_3"]["subtables"][0]

        assert len(lookup_11_2_subtables) == 0
        assert len(lookup_11_3_subtables) == 0


class TestGSUBTableGeneratorRCLT1Feature:
    """Test RCLT1 feature generation (pattern two processing)."""

    def _create_test_generator_with_pattern_two(self):
        """Create generator with pattern two data."""
        character_manager = Mock(spec=CharacterDataManager)
        mapping_manager = Mock(spec=MappingDataManager)
        cmap_table = {"20013": "uni4E2D", "22283": "uni570B"}  # 中  # 國

        generator = GSUBTableGenerator(
            pattern_one_path=Path("/mock/pattern_one.txt"),
            pattern_two_path=Path("/mock/pattern_two.json"),
            exception_pattern_path=Path("/mock/exception.json"),
            character_manager=character_manager,
            mapping_manager=mapping_manager,
            cmap_table=cmap_table,
        )

        # Set up pattern two data
        generator.pattern_two = {
            "lookup_table": {
                "lookup_pt2_0": {"中": "中.ss05"},
                "lookup_pt2_1": {"國": "國.ss06"},
            },
            "patterns": {"中國": [{"中": "lookup_pt2_0"}, {"國": "lookup_pt2_1"}]},
        }

        return generator

    @pytest.mark.unit
    def test_make_rclt1_feature_creates_lookup_tables(self):
        """Test RCLT1 creates lookup tables from pattern two."""
        generator = self._create_test_generator_with_pattern_two()

        generator._make_rclt1_feature()

        lookups = generator.gsub_data["lookups"]

        # Should create lookup tables from pattern_two
        assert "lookup_pt2_0" in lookups
        assert "lookup_pt2_1" in lookups

        # Verify structure
        assert lookups["lookup_pt2_0"]["type"] == "gsub_single"
        assert isinstance(lookups["lookup_pt2_0"]["subtables"], list)
        assert len(lookups["lookup_pt2_0"]["subtables"]) == 1

        # Verify lookup order tracking
        assert "lookup_pt2_0" in generator.lookup_order
        assert "lookup_pt2_1" in generator.lookup_order

    @pytest.mark.unit
    def test_make_rclt1_feature_substitution_rules(self):
        """Test RCLT1 substitution rules from lookup table."""
        generator = self._create_test_generator_with_pattern_two()

        generator._make_rclt1_feature()

        lookups = generator.gsub_data["lookups"]

        # Check lookup_pt2_0 substitutions
        lookup_pt2_0_subtables = lookups["lookup_pt2_0"]["subtables"][0]
        assert "uni4E2D" in lookup_pt2_0_subtables
        assert (
            lookup_pt2_0_subtables["uni4E2D"] == "uni4E2D.ss05"
        )  # 中 -> 中.ss05 (hanzi replaced with cid)

        # Check lookup_pt2_1 substitutions
        lookup_pt2_1_subtables = lookups["lookup_pt2_1"]["subtables"][0]
        assert "uni570B" in lookup_pt2_1_subtables
        assert lookup_pt2_1_subtables["uni570B"] == "uni570B.ss06"

    @pytest.mark.unit
    def test_make_rclt1_feature_contextual_patterns(self):
        """Test RCLT1 contextual patterns for lookup_rclt_3."""
        generator = self._create_test_generator_with_pattern_two()

        generator._make_rclt1_feature()

        # Check rclt_3 subtables
        rclt_3_subtables = generator.gsub_data["lookups"]["lookup_rclt_3"]["subtables"]

        assert len(rclt_3_subtables) == 1

        subtable = rclt_3_subtables[0]
        assert "match" in subtable
        assert "apply" in subtable

        # Should have 2 apply rules (for 中國 pattern)
        assert len(subtable["apply"]) == 2
        assert subtable["apply"][0]["at"] == 0
        assert subtable["apply"][0]["lookup"] == "lookup_pt2_0"
        assert subtable["apply"][1]["at"] == 1
        assert subtable["apply"][1]["lookup"] == "lookup_pt2_1"

    @pytest.mark.unit
    def test_make_rclt1_feature_empty_pattern_two(self):
        """Test RCLT1 with empty pattern two."""
        character_manager = Mock(spec=CharacterDataManager)
        mapping_manager = Mock(spec=MappingDataManager)
        cmap_table = {}

        generator = GSUBTableGenerator(
            pattern_one_path=Path("/mock/pattern_one.txt"),
            pattern_two_path=Path("/mock/pattern_two.json"),
            exception_pattern_path=Path("/mock/exception.json"),
            character_manager=character_manager,
            mapping_manager=mapping_manager,
            cmap_table=cmap_table,
        )

        # Empty pattern two
        generator.pattern_two = {}

        generator._make_rclt1_feature()

        # Should not create any new lookups
        lookups = generator.gsub_data["lookups"]

        # Only base lookups should exist
        expected_base_lookups = {
            "lookup_aalt_0",
            "lookup_aalt_1",
            "lookup_rclt_2",
            "lookup_rclt_3",
            "lookup_rclt_4",
        }
        actual_lookups = set(lookups.keys())
        assert actual_lookups == expected_base_lookups


class TestGSUBTableGeneratorRCLT2Feature:
    """Test RCLT2 feature generation (exception pattern processing)."""

    def _create_test_generator_with_exception_pattern(self):
        """Create generator with exception pattern data."""
        character_manager = Mock(spec=CharacterDataManager)
        mapping_manager = Mock(spec=MappingDataManager)
        cmap_table = {"29305": "uni7279", "21035": "uni522B"}  # 特  # 别

        generator = GSUBTableGenerator(
            pattern_one_path=Path("/mock/pattern_one.txt"),
            pattern_two_path=Path("/mock/pattern_two.json"),
            exception_pattern_path=Path("/mock/exception.json"),
            character_manager=character_manager,
            mapping_manager=mapping_manager,
            cmap_table=cmap_table,
        )

        # Set up exception pattern data
        generator.exception_pattern = {
            "lookup_table": {"lookup_exception_0": {"特": "特.ss10"}},
            "patterns": {
                "特别": {"ignore": "特' 别", "pattern": [{"特": "lookup_exception_0"}]}
            },
        }

        return generator

    @pytest.mark.unit
    def test_make_rclt2_feature_creates_lookup_tables(self):
        """Test RCLT2 creates lookup tables from exception patterns."""
        generator = self._create_test_generator_with_exception_pattern()

        generator._make_rclt2_feature()

        lookups = generator.gsub_data["lookups"]

        # Should create lookup table from exception_pattern
        assert "lookup_exception_0" in lookups
        assert lookups["lookup_exception_0"]["type"] == "gsub_single"

        # Verify lookup order tracking
        assert "lookup_exception_0" in generator.lookup_order

    @pytest.mark.unit
    def test_make_rclt2_feature_substitution_rules(self):
        """Test RCLT2 substitution rules from exception lookup table."""
        generator = self._create_test_generator_with_exception_pattern()

        generator._make_rclt2_feature()

        lookups = generator.gsub_data["lookups"]

        # Check exception lookup substitutions
        exception_subtables = lookups["lookup_exception_0"]["subtables"][0]
        assert "uni7279" in exception_subtables
        assert exception_subtables["uni7279"] == "uni7279.ss10"  # 特 -> 特.ss10

    @pytest.mark.unit
    def test_make_rclt2_feature_ignore_patterns(self):
        """Test RCLT2 ignore pattern processing."""
        generator = self._create_test_generator_with_exception_pattern()

        generator._make_rclt2_feature()

        # Check rclt_4 subtables for ignore patterns
        rclt_4_subtables = generator.gsub_data["lookups"]["lookup_rclt_4"]["subtables"]

        # Should have at least one rule for ignore pattern
        ignore_rules = [rule for rule in rclt_4_subtables if not rule.get("apply")]
        assert len(ignore_rules) > 0

        # Verify ignore rule structure
        ignore_rule = ignore_rules[0]
        assert "match" in ignore_rule
        assert ignore_rule["apply"] == []  # Empty apply for ignore

    @pytest.mark.unit
    def test_make_rclt2_feature_normal_patterns(self):
        """Test RCLT2 normal pattern processing."""
        generator = self._create_test_generator_with_exception_pattern()

        generator._make_rclt2_feature()

        # Check rclt_4 subtables for normal patterns
        rclt_4_subtables = generator.gsub_data["lookups"]["lookup_rclt_4"]["subtables"]

        # Should have rules with apply
        normal_rules = [rule for rule in rclt_4_subtables if rule.get("apply")]
        assert len(normal_rules) > 0

        # Verify normal rule structure
        normal_rule = normal_rules[0]
        assert "match" in normal_rule
        assert "apply" in normal_rule
        assert len(normal_rule["apply"]) > 0

    @pytest.mark.unit
    def test_make_rclt2_feature_empty_exception_pattern(self):
        """Test RCLT2 with empty exception pattern."""
        character_manager = Mock(spec=CharacterDataManager)
        mapping_manager = Mock(spec=MappingDataManager)
        cmap_table = {}

        generator = GSUBTableGenerator(
            pattern_one_path=Path("/mock/pattern_one.txt"),
            pattern_two_path=Path("/mock/pattern_two.json"),
            exception_pattern_path=Path("/mock/exception.json"),
            character_manager=character_manager,
            mapping_manager=mapping_manager,
            cmap_table=cmap_table,
        )

        # Empty exception pattern
        generator.exception_pattern = {}

        generator._make_rclt2_feature()

        # Should not create any new lookups
        lookups = generator.gsub_data["lookups"]
        expected_base_lookups = {
            "lookup_aalt_0",
            "lookup_aalt_1",
            "lookup_rclt_2",
            "lookup_rclt_3",
            "lookup_rclt_4",
        }
        actual_lookups = set(lookups.keys())
        assert actual_lookups == expected_base_lookups


class TestGSUBTableGeneratorLookupOrder:
    """Test lookup order generation."""

    @pytest.mark.unit
    def test_make_lookup_order_basic(self):
        """Test basic lookup order generation."""
        character_manager = Mock(spec=CharacterDataManager)
        mapping_manager = Mock(spec=MappingDataManager)
        cmap_table = {}

        generator = GSUBTableGenerator(
            pattern_one_path=Path("/mock/pattern_one.txt"),
            pattern_two_path=Path("/mock/pattern_two.json"),
            exception_pattern_path=Path("/mock/exception.json"),
            character_manager=character_manager,
            mapping_manager=mapping_manager,
            cmap_table=cmap_table,
        )

        # Add some lookups to track
        generator.lookup_order.add("lookup_aalt_1")
        generator.lookup_order.add("lookup_11_2")
        generator.lookup_order.add("lookup_11_3")

        with patch("builtins.print"):  # Suppress debug output
            generator._make_lookup_order()

        expected_order = [
            "lookup_aalt_0",
            "lookup_aalt_1",
            "lookup_11_2",
            "lookup_11_3",
            "lookup_rclt_2",
            "lookup_rclt_3",
            "lookup_rclt_4",
        ]

        assert generator.gsub_data["lookupOrder"] == expected_order

    @pytest.mark.unit
    def test_make_lookup_order_no_aalt_1(self):
        """Test lookup order when aalt_1 is not present."""
        character_manager = Mock(spec=CharacterDataManager)
        mapping_manager = Mock(spec=MappingDataManager)
        cmap_table = {}

        generator = GSUBTableGenerator(
            pattern_one_path=Path("/mock/pattern_one.txt"),
            pattern_two_path=Path("/mock/pattern_two.json"),
            exception_pattern_path=Path("/mock/exception.json"),
            character_manager=character_manager,
            mapping_manager=mapping_manager,
            cmap_table=cmap_table,
        )

        # Only add lookup_11_* lookups
        generator.lookup_order.add("lookup_11_2")

        with patch("builtins.print"):  # Suppress debug output
            generator._make_lookup_order()

        expected_order = [
            "lookup_aalt_0",
            "lookup_11_2",
            "lookup_rclt_2",
            "lookup_rclt_3",
            "lookup_rclt_4",
        ]

        assert generator.gsub_data["lookupOrder"] == expected_order

    @pytest.mark.unit
    def test_make_lookup_order_filters_non_strings(self):
        """Test that lookup order filters out non-string values."""
        character_manager = Mock(spec=CharacterDataManager)
        mapping_manager = Mock(spec=MappingDataManager)
        cmap_table = {}

        generator = GSUBTableGenerator(
            pattern_one_path=Path("/mock/pattern_one.txt"),
            pattern_two_path=Path("/mock/pattern_two.json"),
            exception_pattern_path=Path("/mock/exception.json"),
            character_manager=character_manager,
            mapping_manager=mapping_manager,
            cmap_table=cmap_table,
        )

        # Add mixed types to lookup_order
        generator.lookup_order.add("lookup_aalt_1")
        generator.lookup_order.add(123)  # Non-string
        generator.lookup_order.add("lookup_11_2")
        generator.lookup_order.add(None)  # Non-string

        with patch("builtins.print"):  # Suppress debug output
            generator._make_lookup_order()

        expected_order = [
            "lookup_aalt_0",
            "lookup_aalt_1",
            "lookup_11_2",
            "lookup_rclt_2",
            "lookup_rclt_3",
            "lookup_rclt_4",
        ]

        assert generator.gsub_data["lookupOrder"] == expected_order


class TestGSUBTableGeneratorIntegration:
    """Test complete GSUB table generation integration."""

    @pytest.mark.unit
    def test_generate_gsub_table_complete_flow(self):
        """Test complete GSUB table generation flow."""
        character_manager = Mock(spec=CharacterDataManager)
        mapping_manager = Mock(spec=MappingDataManager)
        cmap_table = {"20013": "uni4E2D"}  # 中

        # Mock character data
        single_char_info = Mock()
        single_char_info.character = "中"
        character_manager.get_single_pronunciation_characters.return_value = [
            single_char_info
        ]
        character_manager.get_multiple_pronunciation_characters.return_value = []

        # Mock mapping
        mapping_manager.has_glyph_for_character.return_value = True

        generator = GSUBTableGenerator(
            pattern_one_path=Mock(spec=Path),
            pattern_two_path=Mock(spec=Path),
            exception_pattern_path=Mock(spec=Path),
            character_manager=character_manager,
            mapping_manager=mapping_manager,
            cmap_table=cmap_table,
        )

        # Mock file existence
        generator.pattern_one_path.exists.return_value = False
        generator.pattern_two_path.exists.return_value = False
        generator.exception_pattern_path.exists.return_value = False

        with patch("builtins.print"):  # Suppress debug output
            result = generator.generate_gsub_table()

        # Verify complete structure
        assert "languages" in result
        assert "features" in result
        assert "lookups" in result
        assert "lookupOrder" in result

        # Verify AALT feature was processed
        aalt_0_subtables = result["lookups"]["lookup_aalt_0"]["subtables"][0]
        assert "uni4E2D" in aalt_0_subtables

        # Verify lookup order is set
        assert isinstance(result["lookupOrder"], list)
        assert "lookup_aalt_0" in result["lookupOrder"]

    @pytest.mark.unit
    def test_generate_gsub_table_with_all_patterns(self):
        """Test GSUB generation with all pattern types."""
        character_manager = Mock(spec=CharacterDataManager)
        mapping_manager = Mock(spec=MappingDataManager)
        cmap_table = {
            "20013": "uni4E2D",  # 中
            "22269": "uni570D",  # 國
            "24515": "uni5FC3",  # 心
        }

        # Mock character data
        character_manager.get_single_pronunciation_characters.return_value = []

        multi_char_info = Mock()
        multi_char_info.character = "中"
        multi_char_info.pronunciations = ["zhōng", "zhòng"]
        character_manager.get_multiple_pronunciation_characters.return_value = [
            multi_char_info
        ]

        mapping_manager.has_glyph_for_character.return_value = True

        generator = GSUBTableGenerator(
            pattern_one_path=Mock(spec=Path),
            pattern_two_path=Mock(spec=Path),
            exception_pattern_path=Mock(spec=Path),
            character_manager=character_manager,
            mapping_manager=mapping_manager,
            cmap_table=cmap_table,
        )

        # Set up all pattern data
        generator.pattern_one = [
            {"中": {"variational_pronunciation": "zhòng", "patterns": "[~心]"}}
        ]

        generator.pattern_two = {
            "lookup_table": {"lookup_pt2_0": {"中": "中.ss05"}},
            "patterns": {"中國": [{"中": "lookup_pt2_0"}]},
        }

        generator.exception_pattern = {
            "lookup_table": {"lookup_exc_0": {"中": "中.ss10"}},
            "patterns": {"中国": {"pattern": [{"中": "lookup_exc_0"}]}},
        }

        # Mock file existence
        generator.pattern_one_path.exists.return_value = False
        generator.pattern_two_path.exists.return_value = False
        generator.exception_pattern_path.exists.return_value = False

        with patch("builtins.print"):  # Suppress debug output
            result = generator.generate_gsub_table()

        # Verify all features were processed
        lookups = result["lookups"]

        # AALT features
        assert (
            len(lookups["lookup_aalt_1"]["subtables"][0]) > 0
        )  # Multiple pronunciation character

        # RCLT features
        assert "lookup_11_2" in lookups  # Pattern one
        assert "lookup_pt2_0" in lookups  # Pattern two
        assert "lookup_exc_0" in lookups  # Exception pattern

        # Contextual rules - rclt_2 initialized as empty, populated based on pattern complexity
        assert isinstance(
            lookups["lookup_rclt_2"]["subtables"], list
        )  # Pattern one context
        assert len(lookups["lookup_rclt_3"]["subtables"]) > 0  # Pattern two context
        assert len(lookups["lookup_rclt_4"]["subtables"]) > 0  # Exception context


class TestGSUBTableGeneratorErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.unit
    def test_pattern_loading_file_error(self):
        """Test handling of file reading errors."""
        character_manager = Mock(spec=CharacterDataManager)
        mapping_manager = Mock(spec=MappingDataManager)
        cmap_table = {}

        generator = GSUBTableGenerator(
            pattern_one_path=Mock(spec=Path),
            pattern_two_path=Mock(spec=Path),
            exception_pattern_path=Mock(spec=Path),
            character_manager=character_manager,
            mapping_manager=mapping_manager,
            cmap_table=cmap_table,
        )

        # Mock file existence but reading fails
        generator.pattern_one_path.exists.return_value = True

        with patch("builtins.open", side_effect=IOError("File read error")):
            with pytest.raises(IOError):
                generator._load_pattern_data()

    @pytest.mark.unit
    def test_json_parsing_error(self):
        """Test handling of JSON parsing errors."""
        character_manager = Mock(spec=CharacterDataManager)
        mapping_manager = Mock(spec=MappingDataManager)
        cmap_table = {}

        generator = GSUBTableGenerator(
            pattern_one_path=Mock(spec=Path),
            pattern_two_path=Mock(spec=Path),
            exception_pattern_path=Mock(spec=Path),
            character_manager=character_manager,
            mapping_manager=mapping_manager,
            cmap_table=cmap_table,
        )

        # Mock file existence
        generator.pattern_one_path.exists.return_value = False
        generator.pattern_two_path.exists.return_value = True
        generator.exception_pattern_path.exists.return_value = False

        with patch("builtins.open", mock_open()):
            with patch("orjson.loads", side_effect=ValueError("Invalid JSON")):
                with pytest.raises(ValueError):
                    generator._load_pattern_data()

    @pytest.mark.unit
    def test_empty_cmap_table_handling(self):
        """Test handling of empty cmap table."""
        character_manager = Mock(spec=CharacterDataManager)
        mapping_manager = Mock(spec=MappingDataManager)
        cmap_table = {}  # Empty cmap

        # Mock character data with characters not in cmap
        single_char_info = Mock()
        single_char_info.character = "missing"
        character_manager.get_single_pronunciation_characters.return_value = [
            single_char_info
        ]
        character_manager.get_multiple_pronunciation_characters.return_value = []

        generator = GSUBTableGenerator(
            pattern_one_path=Mock(spec=Path),
            pattern_two_path=Mock(spec=Path),
            exception_pattern_path=Mock(spec=Path),
            character_manager=character_manager,
            mapping_manager=mapping_manager,
            cmap_table=cmap_table,
        )

        # Should not raise errors, just skip missing characters
        generator._make_aalt_feature()

        # Verify no substitutions were created
        aalt_0_subtables = generator.gsub_data["lookups"]["lookup_aalt_0"]["subtables"][
            0
        ]
        assert len(aalt_0_subtables) == 0
