#!/usr/bin/env python3
"""
TDD tests for FontBuilder._add_glyf() implementation.
Red-Green-Refactor cycle for glyph addition functionality.
"""

import pytest
import json
from pathlib import Path
import sys

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from mengshen_font.font.font_builder import FontBuilder
from mengshen_font.config import FontType, ProjectPaths


class TestFontBuilderGlyfImplementation:
    """
    TDD tests for _add_glyf() method implementation.
    These tests drive the implementation of pinyin glyph generation.
    """
    
    @pytest.fixture
    def font_builder(self):
        """Create a FontBuilder instance for testing."""
        paths = ProjectPaths()
        
        # Use actual paths matching CLI structure
        return FontBuilder(
            font_type=FontType.HAN_SERIF,
            template_main_path=paths.get_temp_json_path("template_main.json"),
            template_glyf_path=paths.get_temp_json_path("template_glyf.json"),
            alphabet_pinyin_path=paths.get_temp_json_path("alphabet_for_pinyin.json"),
            pattern_one_path=paths.outputs_dir / "pattern_one.txt",
            pattern_two_path=paths.outputs_dir / "pattern_two.json",
            exception_pattern_path=paths.outputs_dir / "exception_pattern.json"
        )
    
    @pytest.fixture
    def initial_font_data(self, font_builder):
        """Get initial font data before _add_glyf()."""
        # Load template first to get baseline
        font_builder._load_templates()
        font_builder._initialize_managers()  # Initialize managers
        return dict(font_builder._font_data)  # Deep copy
    
    def test_add_glyf_increases_glyph_count(self, font_builder, initial_font_data):
        """_add_glyf() should significantly increase the number of glyphs."""
        initial_glyf_count = len(initial_font_data.get("glyf", {}))
        
        # Execute the method under test
        font_builder._add_glyf()
        
        final_glyf_count = len(font_builder._font_data.get("glyf", {}))
        
        # Should add thousands of pinyin glyphs
        added_glyphs = final_glyf_count - initial_glyf_count
        assert added_glyphs >= 30000, \
            f"Expected at least 30,000 new glyphs, got {added_glyphs}"
        
        # Total should be around 63,000 glyphs
        assert final_glyf_count >= 60000, \
            f"Expected at least 60,000 total glyphs, got {final_glyf_count}"
    
    def test_add_glyf_creates_pinyin_glyphs(self, font_builder):
        """_add_glyf() should create pinyin annotation glyphs."""
        font_builder._load_templates()
        font_builder._initialize_managers()
        font_builder._add_glyf()
        
        glyf_table = font_builder._font_data.get("glyf", {})
        
        # Check for specific pinyin glyphs
        pinyin_glyphs = [name for name in glyf_table.keys() if "pinyin" in name.lower()]
        assert len(pinyin_glyphs) >= 1000, \
            f"Expected at least 1,000 pinyin glyphs, found {len(pinyin_glyphs)}"
        
        # Check for specific examples we know should exist
        expected_pinyin_patterns = ["zhong", "yin", "han"]
        found_patterns = []
        
        for pattern in expected_pinyin_patterns:
            matching_glyphs = [name for name in pinyin_glyphs if pattern in name.lower()]
            if matching_glyphs:
                found_patterns.append(pattern)
        
        assert len(found_patterns) >= 2, \
            f"Expected to find at least 2 pinyin patterns {expected_pinyin_patterns}, found {found_patterns}"
    
    def test_add_glyf_creates_homograph_variants(self, font_builder):
        """_add_glyf() should create variant glyphs for homographs (多音字)."""
        font_builder._load_templates()
        font_builder._initialize_managers()
        font_builder._add_glyf()
        
        glyf_table = font_builder._font_data.get("glyf", {})
        
        # Look for variant glyphs (multiple pronunciations of same character)
        variant_glyphs = [name for name in glyf_table.keys() if "variant" in name.lower()]
        
        # Should have variants for common homographs like 中 (zhōng/zhòng)
        zhong_variants = [name for name in glyf_table.keys() if "zhong" in name.lower()]
        
        # At minimum, should have some variant handling
        assert len(variant_glyphs) > 0 or len(zhong_variants) >= 2, \
            f"Expected homograph variants, found {len(variant_glyphs)} variants, {len(zhong_variants)} zhong glyphs"
    
    def test_add_glyf_preserves_base_glyphs(self, font_builder, initial_font_data):
        """_add_glyf() should preserve existing base character glyphs."""
        initial_base_glyphs = {
            name: glyph for name, glyph in initial_font_data.get("glyf", {}).items()
            if not any(keyword in name.lower() for keyword in ["pinyin", "variant"])
        }
        
        font_builder._add_glyf()
        
        final_glyf_table = font_builder._font_data.get("glyf", {})
        
        # All original base glyphs should still exist
        for glyph_name, glyph_data in initial_base_glyphs.items():
            assert glyph_name in final_glyf_table, \
                f"Base glyph '{glyph_name}' was lost during _add_glyf()"
            
            # Glyph data should be unchanged (or reasonably similar)
            # Allow some modification but core structure should remain
            assert final_glyf_table[glyph_name] is not None, \
                f"Base glyph '{glyph_name}' data was corrupted"
    
    def test_add_glyf_uses_character_manager(self, font_builder):
        """_add_glyf() should utilize the character_manager for character data."""
        font_builder._load_templates()
        
        # Verify character manager is available
        assert font_builder.character_manager is not None, \
            "CharacterManager not initialized"
        
        # Check if character manager has data
        assert hasattr(font_builder.character_manager, 'get_all_characters'), \
            "CharacterManager missing get_all_characters method"
        
        # Execute and verify it used the character manager
        font_builder._add_glyf()
        
        # Verify the result shows signs of using character data
        glyf_table = font_builder._font_data.get("glyf", {})
        glyph_names = list(glyf_table.keys())
        
        # Should have more glyphs after processing character data
        assert len(glyph_names) > 30000, \
            f"Expected character manager to contribute significantly to glyph count, got {len(glyph_names)}"
    
    def test_add_glyf_placeholder_is_replaced(self, font_builder):
        """Verify the placeholder implementation has been replaced."""
        # This meta-test ensures we've actually implemented the method
        font_builder._load_templates()
        font_builder._initialize_managers()  # Initialize managers before glyf generation
        initial_glyf_count = len(font_builder._font_data.get("glyf", {}))
        
        font_builder._add_glyf()
        
        final_glyf_count = len(font_builder._font_data.get("glyf", {}))
        
        # If this is still a placeholder, glyph count won't change significantly
        assert final_glyf_count > initial_glyf_count + 1000, \
            f"_add_glyf() appears to still be a placeholder implementation. " \
            f"Only added {final_glyf_count - initial_glyf_count} glyphs."


class TestFontBuilderGlyfIntegration:
    """
    Integration tests for _add_glyf() with other components.
    These test the interaction with managers and data sources.
    """
    
    @pytest.fixture
    def font_builder(self):
        """Create a FontBuilder instance for integration testing."""
        paths = ProjectPaths()
        return FontBuilder(
            font_type=FontType.HAN_SERIF,
            template_main_path=paths.get_temp_json_path("template_main.json"),
            template_glyf_path=paths.get_temp_json_path("template_glyf.json"),
            alphabet_pinyin_path=paths.get_temp_json_path("alphabet_for_pinyin.json"),
            pattern_one_path=paths.outputs_dir / "pattern_one.txt",
            pattern_two_path=paths.outputs_dir / "pattern_two.json",
            exception_pattern_path=paths.outputs_dir / "exception_pattern.json"
        )
    
    def test_glyf_integration_with_pipeline(self, font_builder):
        """_add_glyf() should work as part of the complete font generation pipeline."""
        # This test verifies the method works in the context of the full build
        font_builder._load_templates()
        font_builder._add_cmap_uvs()  # Dependencies
        font_builder._add_glyph_order()  # Dependencies
        
        # The main method under test
        font_builder._add_glyf()
        
        # Should be able to continue with GSUB
        font_builder._add_gsub()
        
        # Verify the font_data is in a valid state
        assert "glyf" in font_builder._font_data
        assert "GSUB" in font_builder._font_data
        assert len(font_builder._font_data["glyf"]) >= 60000
    
    def test_glyf_performance_reasonable(self, font_builder):
        """_add_glyf() should complete in reasonable time."""
        import time
        
        font_builder._load_templates()
        
        start_time = time.time()
        font_builder._add_glyf()
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Should complete within 60 seconds (adjust based on performance requirements)
        assert execution_time < 60, \
            f"_add_glyf() took {execution_time:.2f} seconds, expected < 60 seconds"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])