# -*- coding: utf-8 -*-
"""OverlayPinyinDataSource merge semantics."""

from __future__ import annotations

from webapp.backend.schemas import ReadingOverride
from webapp.backend.services.overlay_pinyin_source import OverlayPinyinDataSource


def _project_with(store, readings=None, excluded=None):
    project = store.create("Test")
    if readings:
        project.glyph_overrides.readings = {
            char: ReadingOverride(**override) for char, override in readings.items()
        }
    if excluded:
        project.glyph_overrides.excluded_characters = excluded
    return project


class TestOverlayPinyinDataSource:
    def test_no_override_passes_through(self, store):
        source = OverlayPinyinDataSource(_project_with(store))
        assert source.get_pinyin("中") == ["zhōng", "zhòng"]

    def test_replace_override(self, store):
        project = _project_with(
            store, {"中": {"mode": "replace", "pronunciations": ["zhòng"]}}
        )
        source = OverlayPinyinDataSource(project)
        assert source.get_pinyin("中") == ["zhòng"]
        assert source.get_all_mappings()["中"] == ["zhòng"]

    def test_append_override_deduplicates(self, store):
        project = _project_with(
            store, {"中": {"mode": "append", "pronunciations": ["zhōng", "zong1"]}}
        )
        source = OverlayPinyinDataSource(project)
        readings = source.get_pinyin("中")
        assert readings[0] == "zhōng"
        assert readings.count("zhōng") == 1
        assert "zong1" in readings

    def test_excluded_character(self, store):
        project = _project_with(store, excluded=["中"])
        source = OverlayPinyinDataSource(project)
        assert source.get_pinyin("中") is None
        assert "中" not in source.get_all_mappings()
