"""Simple integration test for FontBuilder glyph count validation."""

import pytest


def test_glyph_count_validation_is_in_correct_location():
    """Test that the glyph count validation exists in the correct location."""
    import inspect

    from refactored.font.font_builder import FontBuilder

    # Get the _add_glyf method source code
    source = inspect.getsource(FontBuilder._add_glyf)

    # Verify the validation exists in the correct location
    assert "if len(new_glyf) > 65536:" in source
    assert "glyf table cannot contain more than 65536 glyphs" in source

    # Verify it happens after glyf table assembly
    lines = source.split("\n")
    validation_line = -1
    assignment_line = -1

    for i, line in enumerate(lines):
        if 'self._font_data["glyf"] = new_glyf' in line:
            assignment_line = i
        if "if len(new_glyf) > 65536:" in line:
            validation_line = i

    # Validation should come after the assignment
    assert assignment_line != -1, "Assignment line not found"
    assert validation_line != -1, "Validation line not found"
    assert (
        validation_line > assignment_line
    ), "Validation should come after glyf table assignment"


def test_glyph_validation_removed_from_glyph_manager():
    """Test that glyph validation was properly removed from GlyphManager."""
    import inspect

    from refactored.font.glyph_manager import GlyphManager

    # Get the generate_hanzi_glyphs method source code (where validation was)
    source = inspect.getsource(GlyphManager.generate_hanzi_glyphs)

    # Verify the validation is NOT present (should be removed)
    assert "if total_glyphs > FontConstants.MAX_GLYPHS:" not in source
    assert "RuntimeError" not in source or "Glyph count exceeds limit" not in source

    # Verify the note is present instead
    assert (
        "Note: Glyph count validation is performed in FontBuilder._add_glyf()" in source
    )


def test_validate_glyph_count_method_removed():
    """Test that validate_glyph_count method was removed from GlyphManager."""
    from refactored.font.glyph_manager import GlyphManager

    # The validate_glyph_count method should not exist
    assert not hasattr(GlyphManager, "validate_glyph_count")


def test_legacy_compatibility():
    """Test that the validation matches legacy behavior."""
    import inspect

    from refactored.font.font_builder import FontBuilder

    source = inspect.getsource(FontBuilder._add_glyf)

    # Should use the same 65536 limit as legacy
    assert "65536" in source
    # Should check len(glyf_table) like legacy
    assert "len(new_glyf)" in source
    # Should raise Exception like legacy (not RuntimeError)
    assert "raise Exception" in source  # Should check len(glyf_table) like legacy
    assert "len(new_glyf)" in source
    # Should raise Exception like legacy (not RuntimeError)
    assert "raise Exception" in source
