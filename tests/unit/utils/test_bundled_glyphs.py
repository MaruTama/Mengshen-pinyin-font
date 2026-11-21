# -*- coding: utf-8 -*-
"""Bundled (pre-composed) pinyin letter glyphs for builtin pinyin fonts."""

from __future__ import annotations

import hashlib
import json

import pytest

from src.refactored.utils import bundled_glyphs as bg

E_MACRON_CIRCUMFLEX = "ê̄"


def _glyph(width=500):
    return {"advanceWidth": width, "contours": [[{"x": 0, "y": 0, "on": True}]]}


@pytest.fixture
def font_and_bundle(tmp_path):
    font = tmp_path / "font.ttf"
    font.write_bytes(b"fake font bytes")
    bundle_dir = tmp_path / "bundles"
    bundle_dir.mkdir()
    bundle = {
        "font": "font.ttf",
        "font_sha256": hashlib.sha256(b"fake font bytes").hexdigest(),
        "glyphs": {
            "eh1": {
                "letter": E_MACRON_CIRCUMFLEX,
                "recipe": {"base": "ê", "mark_source": "ē"},
                "glyph": _glyph(510),
            },
            "e1": {"letter": "ē", "recipe": {}, "glyph": _glyph(999)},
        },
        "overrides": {
            "a": {"letter": "a", "recipe": {"base": "ɑ"}, "glyph": _glyph(480)},
        },
    }
    (bundle_dir / "style.json").write_text(
        json.dumps(bundle, ensure_ascii=False), encoding="utf-8"
    )
    return font, bundle_dir


class TestBundledGlyphsForFont:
    def test_matches_by_sha256(self, font_and_bundle):
        font, bundle_dir = font_and_bundle
        glyphs = bg.bundled_glyphs_for_font(font, bundle_dir)
        assert set(glyphs) == {E_MACRON_CIRCUMFLEX, "ē"}
        assert glyphs[E_MACRON_CIRCUMFLEX]["advanceWidth"] == 510

    def test_other_font_gets_nothing(self, font_and_bundle, tmp_path):
        _, bundle_dir = font_and_bundle
        other = tmp_path / "other.ttf"
        other.write_bytes(b"different")
        assert bg.bundled_glyphs_for_font(other, bundle_dir) == {}

    def test_missing_dir(self, font_and_bundle, tmp_path):
        font, _ = font_and_bundle
        assert bg.bundled_glyphs_for_font(font, tmp_path / "nope") == {}


class TestBundledOverridesForFont:
    def test_matches_by_sha256(self, font_and_bundle):
        font, bundle_dir = font_and_bundle
        overrides = bg.bundled_overrides_for_font(font, bundle_dir)
        assert set(overrides) == {"a"}
        assert overrides["a"]["advanceWidth"] == 480

    def test_other_font_gets_nothing(self, font_and_bundle, tmp_path):
        _, bundle_dir = font_and_bundle
        other = tmp_path / "other.ttf"
        other.write_bytes(b"different")
        assert bg.bundled_overrides_for_font(other, bundle_dir) == {}

    def test_section_is_optional(self, font_and_bundle):
        font, bundle_dir = font_and_bundle
        path = bundle_dir / "style.json"
        bundle = json.loads(path.read_text(encoding="utf-8"))
        del bundle["overrides"]
        path.write_text(json.dumps(bundle, ensure_ascii=False), encoding="utf-8")
        assert bg.bundled_overrides_for_font(font, bundle_dir) == {}

    def test_fill_glyphs_exclude_overrides(self, font_and_bundle):
        font, bundle_dir = font_and_bundle
        assert "a" not in bg.bundled_glyphs_for_font(font, bundle_dir)


class TestMerge:
    def test_only_fills_missing_letters(self):
        alphabet = {"ē": _glyph(1), "e": _glyph(2)}
        merged = bg.merge_bundled_glyphs(
            alphabet, {"ē": _glyph(999), E_MACRON_CIRCUMFLEX: _glyph(510)}
        )
        assert merged["ē"]["advanceWidth"] == 1  # font glyph wins
        assert merged[E_MACRON_CIRCUMFLEX]["advanceWidth"] == 510
        assert list(merged)[:2] == ["ē", "e"]
        assert alphabet == {"ē": _glyph(1), "e": _glyph(2)}  # not mutated

    def test_overrides_replace_font_letters(self):
        alphabet = {"a": _glyph(1), "e": _glyph(2)}
        merged = bg.merge_bundled_glyphs(
            alphabet, {E_MACRON_CIRCUMFLEX: _glyph(510)}, {"a": _glyph(480)}
        )
        assert merged["a"]["advanceWidth"] == 480  # override wins
        assert merged["e"]["advanceWidth"] == 2
        assert merged[E_MACRON_CIRCUMFLEX]["advanceWidth"] == 510
        assert list(merged)[:2] == ["a", "e"]  # order kept
        assert alphabet["a"]["advanceWidth"] == 1  # not mutated


class TestRetrieverIntegration:
    def test_filter_then_bundle(self, font_and_bundle, monkeypatch):
        from src.refactored.scripts.retrieve_latin_alphabet import (
            LatinAlphabetRetriever,
        )

        font, bundle_dir = font_and_bundle
        monkeypatch.setattr(bg, "BUNDLED_GLYPHS_DIR", bundle_dir)
        retriever = LatinAlphabetRetriever()
        alphabet = retriever.add_bundled_glyphs(
            {"ē": _glyph(1), "a": _glyph(2)}, str(font)
        )
        assert set(alphabet) == {"ē", "a", E_MACRON_CIRCUMFLEX}
        assert alphabet["ē"]["advanceWidth"] == 1
        assert alphabet["a"]["advanceWidth"] == 480


class TestRealBundles:
    """The bundles shipped in res/fonts/custom_pinyin_glyphs."""

    @pytest.mark.parametrize(
        "style,letters",
        [
            ("han_serif", {"ê̄", "ê̌", "m̄", "m̀"}),
            (
                "handwritten",
                {
                    "ê",
                    "ê̄",
                    "ế",
                    "ê̌",
                    "ề",
                    "m̄",
                    "m̀",
                },
            ),
        ],
    )
    def test_builtin_bundle_letters(self, style, letters):
        from src.refactored.config.font_config import FontConfig, FontType

        font_path = FontConfig.get_alphabet_font_path(FontType(style))
        glyphs = bg.bundled_glyphs_for_font(font_path)
        assert set(glyphs) == letters
        for letter, glyph in glyphs.items():
            assert glyph["advanceWidth"] > 0, letter
            assert len(glyph["contours"]) >= 2, letter

    @pytest.mark.parametrize(
        "style,letters",
        [
            # mplus: every a-family glyph is double-story -> ɑ (+ tone mark)
            ("han_serif", {"a", "ā", "á", "ǎ", "à"}),
            # Seto: only ǎ is single-story; a ā á à are rebuilt on its body
            ("handwritten", {"a", "ā", "á", "à"}),
        ],
    )
    def test_builtin_single_story_a_overrides(self, style, letters):
        """Issue #15: pinyin a is the single-story ɑ, consistently."""
        from src.refactored.config.font_config import FontConfig, FontType

        font_path = FontConfig.get_alphabet_font_path(FontType(style))
        overrides = bg.bundled_overrides_for_font(font_path)
        assert set(overrides) == letters
        for letter, glyph in overrides.items():
            assert glyph["advanceWidth"] > 0, letter
            assert glyph["contours"], letter
