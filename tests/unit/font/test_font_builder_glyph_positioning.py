# -*- coding: utf-8 -*-
"""Test for correct glyph positioning in font builder."""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from src.mengshen_font.font.font_builder import FontBuilder
from src.mengshen_font.config import FontType


class TestFontBuilderGlyphPositioning:
    """Test correct glyph positioning in FontBuilder._add_glyf()."""
    
    def setup_method(self):
        """Setup test fixtures."""
        # Mock dependencies
        self.mock_pinyin_manager = Mock()
        self.mock_character_manager = Mock()
        self.mock_mapping_manager = Mock()
        self.mock_external_tool = Mock()
        
        # Sample glyf template data matching legacy format
        self.template_glyf_data = {
            "cid02518": {
                "advanceHeight": 1000,
                "advanceWidth": 1000,
                "references": [
                    {
                        "glyph": "py_alphablet_z",
                        "x": 375,        # Legacy correct position
                        "y": 1914,
                        "a": 0.58001708984375,    # Legacy correct positive scale
                        "b": 0,
                        "c": 0,
                        "d": 0.58099365234375
                    }
                ],
                "verticalOrigin": 880
            }
        }
        
        # Generated glyph data with different positioning
        self.generated_glyph_data = {
            "cid02518": {
                "advanceHeight": 1000,
                "advanceWidth": 1000,
                "references": [
                    {
                        "glyph": "py_alphablet_z", 
                        "x": 0,          # Wrong position
                        "y": 1945,
                        "a": -1.3790283203125,   # Wrong negative scale
                        "b": 0,
                        "c": 0,
                        "d": -1.37799072265625
                    }
                ],
                "verticalOrigin": 880
            }
        }
    
    def test_glyph_references_positioning_preserved_from_template(self):
        """🔴 RED: Test that glyph references maintain correct positioning from template."""
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
        result_glyf = font_builder._font_data["glyf"]["cid02518"]
        
        # Assert correct positioning is preserved from template (FAILING TEST)
        reference = result_glyf["references"][0]
        
        # These assertions should pass with corrected implementation
        assert reference["x"] == 375, f"X position should be 375 (from template), got {reference['x']}"
        assert reference["y"] == 1914, f"Y position should be 1914 (from template), got {reference['y']}"
        assert reference["a"] == 0.58001708984375, f"X scale should be positive (from template), got {reference['a']}"
        assert reference["d"] == 0.58099365234375, f"Y scale should be positive (from template), got {reference['d']}"
    
    def test_glyph_metrics_updated_from_generated_data(self):
        """🔴 RED: Test that glyph metrics are updated from generated data while preserving positioning."""
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
        
        # Modify generated data to have different metrics
        modified_generated_data = self.generated_glyph_data.copy()
        modified_generated_data["cid02518"]["advanceWidth"] = 1200  # New width
        modified_generated_data["cid02518"]["advanceHeight"] = 1400  # New height
        
        mock_glyph_manager.get_all_glyphs.return_value = modified_generated_data
        font_builder.glyph_manager = mock_glyph_manager
        
        # Set template data
        font_builder._glyf_data = self.template_glyf_data
        font_builder._font_data = {"glyf": {}}
        
        # Execute _add_glyf() method
        font_builder._add_glyf()
        
        # Get the resulting glyf
        result_glyf = font_builder._font_data["glyf"]["cid02518"]
        
        # Assert metrics are updated while positioning is preserved
        assert result_glyf["advanceWidth"] == 1200, "Advance width should be updated from generated data"
        assert result_glyf["advanceHeight"] == 1400, "Advance height should be updated from generated data"
        
        # But positioning should still come from template
        reference = result_glyf["references"][0]
        assert reference["x"] == 375, "X position should be preserved from template"
        assert reference["a"] == 0.58001708984375, "X scale should be preserved from template"
    
    def test_font_bbox_calculation_with_correct_positioning(self):
        """🔴 RED: Test that font bounding box is calculated correctly with proper positioning."""
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
        
        # Set template data with more glyphs for better bbox testing
        extended_template = self.template_glyf_data.copy()
        extended_template["cid02519"] = {
            "advanceHeight": 1000,
            "advanceWidth": 1000,
            "references": [
                {
                    "glyph": "py_alphablet_a",
                    "x": 5999,       # Max X coordinate from legacy
                    "y": 3705,       # Max Y coordinate from legacy
                    "a": 0.5,
                    "b": 0,
                    "c": 0,
                    "d": 0.5
                }
            ],
            "verticalOrigin": 880
        }
        
        font_builder._glyf_data = extended_template
        font_builder._font_data = {"glyf": {}, "head": {"xMax": 0, "yMax": 0}}
        
        # Mock coordinate calculation
        with patch('src.mengshen_font.font.font_builder.FontBuilder._calculate_font_bbox') as mock_bbox:
            mock_bbox.return_value = {"xMax": 5999, "yMax": 3705}
            
            font_builder._add_glyf()
            
            # Assert that bbox calculation considers the extended coordinates
            # With correct positioning, xMax should be ~6000 (legacy value)
            # NOT ~2000 (current broken value)
            font_bbox = font_builder._font_data["head"]
            assert font_bbox["xMax"] >= 5000, f"Font xMax should be >= 5000 with correct positioning, got {font_bbox['xMax']}"


if __name__ == "__main__":
    pytest.main([__file__])