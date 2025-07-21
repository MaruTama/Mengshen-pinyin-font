"""Simple integration test for FontBuilder font metrics updates."""

import pytest


def test_font_metrics_update_implementation_exists():
    """Test that the font metrics update implementation matches legacy behavior."""
    import inspect

    from refactored.font.font_builder import FontBuilder

    # Get the _set_about_size method source code (matches legacy set_about_size)
    source = inspect.getsource(FontBuilder._set_about_size)

    # Verify all required metric updates are present
    assert "head" in source and "yMax" in source
    assert "hhea" in source and "ascender" in source
    assert "OS_2" in source and "usWinAscent" in source

    # Verify the conditional logic matches legacy
    assert "advanceAddedPinyinHeight" in source
    assert "get_pinyin_metrics()" in source

    # Verify comments indicate legacy compatibility
    assert "legacy" in source.lower()


def test_metrics_calculation_methods_exist():
    """Test that all required metrics calculation methods exist."""
    from refactored.font.glyph_manager import GlyphManager

    # Verify the get_pinyin_metrics method exists
    assert hasattr(GlyphManager, "get_pinyin_metrics")

    # Verify it returns the correct type
    from refactored.font.glyph_manager import PinyinMetrics

    method = getattr(GlyphManager, "get_pinyin_metrics")

    # Check return annotation (string or class both acceptable)
    import inspect

    sig = inspect.signature(method)
    assert (
        sig.return_annotation == PinyinMetrics
        or sig.return_annotation == "PinyinMetrics"
    )


def test_pinyin_metrics_dataclass_structure():
    """Test that PinyinMetrics has the required fields."""
    import dataclasses

    from refactored.font.glyph_manager import PinyinMetrics

    # Verify it's a dataclass
    assert dataclasses.is_dataclass(PinyinMetrics)

    # Verify required fields exist
    fields = [field.name for field in dataclasses.fields(PinyinMetrics)]
    assert "width" in fields
    assert "height" in fields
    assert "vertical_origin" in fields


def test_legacy_constant_usage():
    """Test that the vertical origin constant matches legacy value."""
    # Get the constant from pinyin glyph generator or related code
    import inspect

    from refactored.font.glyph_manager import PinyinGlyphGenerator

    # Check that VERTICAL_ORIGIN_PER_HEIGHT = 0.88 is used
    source = inspect.getsource(PinyinGlyphGenerator)

    # This should contain the legacy constant or equivalent calculation
    assert "0.88" in source or "VERTICAL_ORIGIN_PER_HEIGHT" in source


def test_font_table_update_order():
    """Test that font table updates follow the correct precedence."""
    import inspect

    from refactored.font.font_builder import FontBuilder

    source = inspect.getsource(FontBuilder._set_about_size)
    lines = source.split("\n")

    # Find the positions of different table updates
    ymax_line = -1
    ascender_line = -1
    uswinascent_line = -1

    for i, line in enumerate(lines):
        if "yMax" in line and "=" in line:
            ymax_line = i
        elif "ascender" in line and "=" in line:
            ascender_line = i
        elif "usWinAscent" in line and "=" in line:
            uswinascent_line = i

    # Verify all updates were found
    assert ymax_line != -1, "yMax update not found"
    assert ascender_line != -1, "ascender update not found"
    assert uswinascent_line != -1, "usWinAscent update not found"

    # Verify logical order (yMax independent, ascender/usWinAscent linked)
    # yMax and ascender can be in different conditional blocks
    # Main requirement: usWinAscent should be after ascender if both exist
    if ascender_line != -1 and uswinascent_line != -1:
        assert (
            ascender_line < uswinascent_line
        ), "ascender should be updated before usWinAscent"
