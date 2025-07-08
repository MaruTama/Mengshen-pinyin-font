# -*- coding: utf-8 -*-
"""Test for preserving basic glyphs (hiragana, katakana, alphabet) contours."""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from src.mengshen_font.font.font_builder import FontBuilder
from src.mengshen_font.config import FontType


class TestBasicGlyphsPreservation:
    """Test preservation of basic glyphs contours."""
    
    def setup_method(self):
        """Setup test fixtures."""
        # Mock dependencies
        self.mock_pinyin_manager = Mock()
        self.mock_character_manager = Mock()
        self.mock_mapping_manager = Mock()
        self.mock_external_tool = Mock()
        
        # Template glyf data with basic characters
        self.template_glyf_data = {
            "cid01460": {  # ひらがな「あ」
                "advanceWidth": 1000,
                "advanceHeight": 1000,
                "verticalOrigin": 880,
                "contours": [
                    [{"x": 100, "y": 100, "on": True}],  # Sample contour
                    [{"x": 200, "y": 200, "on": True}],
                    [{"x": 300, "y": 300, "on": True}]
                ]
            },
            "cid00034": {  # アルファベット「A」
                "advanceWidth": 600,
                "advanceHeight": 1000,
                "verticalOrigin": 880,
                "contours": [
                    [{"x": 50, "y": 0, "on": True}],   # Sample contour
                    [{"x": 550, "y": 700, "on": True}]
                ]
            },
            "cid02518": {  # 中国語文字（ピンイン処理対象）
                "advanceWidth": 1000,
                "advanceHeight": 1000,
                "verticalOrigin": 880,
                "contours": [
                    [{"x": 400, "y": 400, "on": True}]
                ]
            }
        }
        
        # Generated glyph data (only Chinese characters with pinyin)
        self.generated_glyph_data = {
            "cid02518": {  # Chinese character with pinyin
                "advanceWidth": 2048,
                "advanceHeight": 2628,
                "verticalOrigin": 2313,
                "references": [
                    {"glyph": "py_alphablet_z", "x": 375, "y": 1914, "a": 0.58, "b": 0, "c": 0, "d": 0.58},
                    {"glyph": "cid02518.ss00", "x": 0, "y": 0, "a": 1, "b": 0, "c": 0, "d": 1}
                ]
            },
            "cid02518.ss00": {  # Chinese character without pinyin
                "advanceWidth": 1000,
                "advanceHeight": 1000,
                "verticalOrigin": 880
            }
        }
    
    def test_basic_glyphs_contours_preserved(self):
        """🔴 RED: Test that basic glyphs (hiragana, alphabet) preserve contours."""
        # Create FontBuilder instance
        font_builder = FontBuilder(
            font_type=FontType.HAN_SERIF,
            template_main_path=Path("dummy.json"),
            template_glyf_path=Path("dummy.json"),
            alphabet_pinyin_path=Path("dummy.json"),
            pattern_one_path=Path("dummy"),
            pattern_two_path=Path("dummy"),
            exception_pattern_path=Path("dummy"),
            pinyin_manager=self.mock_pinyin_manager,
            character_manager=self.mock_character_manager,
            mapping_manager=self.mock_mapping_manager,
            external_tool=self.mock_external_tool
        )
        
        # Setup mock for glyph manager
        mock_glyph_manager = Mock()
        mock_glyph_manager.get_all_glyphs.return_value = self.generated_glyph_data
        font_builder.glyph_manager = mock_glyph_manager
        
        # Set template data
        font_builder._glyf_data = self.template_glyf_data
        font_builder._font_data = {"glyf": {}}
        
        # Execute _add_glyf() method
        font_builder._add_glyf()
        
        # Get the resulting glyf
        result_glyf = font_builder._font_data["glyf"]
        
        # Assert basic glyphs preserve their contours
        # ひらがな「あ」(cid01460) should keep its contours
        assert "cid01460" in result_glyf, "Hiragana 'あ' should be present in result"
        hiragana_glyph = result_glyf["cid01460"]
        assert "contours" in hiragana_glyph, "Hiragana 'あ' should have contours"
        assert len(hiragana_glyph["contours"]) == 3, f"Hiragana 'あ' should have 3 contours, got {len(hiragana_glyph['contours'])}"
        
        # アルファベット「A」(cid00034) should keep its contours
        assert "cid00034" in result_glyf, "Alphabet 'A' should be present in result"
        alphabet_glyph = result_glyf["cid00034"]
        assert "contours" in alphabet_glyph, "Alphabet 'A' should have contours"
        assert len(alphabet_glyph["contours"]) == 2, f"Alphabet 'A' should have 2 contours, got {len(alphabet_glyph['contours'])}"
    
    def test_chinese_characters_use_generated_data(self):
        """🔴 RED: Test that Chinese characters use generated pinyin data."""
        # Create FontBuilder instance
        font_builder = FontBuilder(
            font_type=FontType.HAN_SERIF,
            template_main_path=Path("dummy.json"),
            template_glyf_path=Path("dummy.json"),
            alphabet_pinyin_path=Path("dummy.json"),
            pattern_one_path=Path("dummy"),
            pattern_two_path=Path("dummy"),
            exception_pattern_path=Path("dummy"),
            pinyin_manager=self.mock_pinyin_manager,
            character_manager=self.mock_character_manager,
            mapping_manager=self.mock_mapping_manager,
            external_tool=self.mock_external_tool
        )
        
        # Setup mock for glyph manager
        mock_glyph_manager = Mock()
        mock_glyph_manager.get_all_glyphs.return_value = self.generated_glyph_data
        font_builder.glyph_manager = mock_glyph_manager
        
        # Set template data
        font_builder._glyf_data = self.template_glyf_data
        font_builder._font_data = {"glyf": {}}
        
        # Execute _add_glyf() method
        font_builder._add_glyf()
        
        # Get the resulting glyf
        result_glyf = font_builder._font_data["glyf"]
        
        # Assert Chinese character uses generated pinyin data
        assert "cid02518" in result_glyf, "Chinese character should be present in result"
        chinese_glyph = result_glyf["cid02518"]
        assert "references" in chinese_glyph, "Chinese character should have references (pinyin)"
        assert chinese_glyph["advanceHeight"] == 2628, "Chinese character should use generated metrics"
        
        # Assert .ss00 variant uses template contours
        assert "cid02518.ss00" in result_glyf, "Chinese character .ss00 should be present"
        ss00_glyph = result_glyf["cid02518.ss00"]
        assert "contours" in ss00_glyph, "Chinese character .ss00 should have template contours"


if __name__ == "__main__":
    pytest.main([__file__])