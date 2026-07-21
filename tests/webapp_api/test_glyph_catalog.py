# -*- coding: utf-8 -*-
"""Glyph catalog: standard-table hanzi restriction."""

from __future__ import annotations

from webapp.backend.services.glyph_catalog import allowed_hanzi


class TestAllowedHanzi:
    def test_union_of_three_tables(self):
        allowed = allowed_hanzi()
        # From all three tables
        assert ord("中") in allowed
        # 常用漢字にしかない日本の新字体 (酌 is joyo; 塩 is JP-simplified)
        assert ord("塩") in allowed
        # Big5 繁体字 (traditional-only)
        assert ord("龜") in allowed
        # Reasonable size: TGSCC 8105 + Big5 + Joyo unions to ~15-20k
        assert 10000 < len(allowed) < 30000

    def test_non_standard_hanzi_excluded(self):
        allowed = allowed_hanzi()
        # CJK Ext-B character not in any of the three tables
        assert 0x20000 not in allowed

    def test_non_cjk_from_big5_excluded(self):
        # Big5 table contains symbols like § (0x00A7); they must not leak in
        assert 0x00A7 not in allowed_hanzi()


class TestTablesFor:
    def test_membership_per_table(self):
        from webapp.backend.services.glyph_catalog import tables_for

        # 中 is in all three tables
        assert tables_for([ord("中")]) == ["tgscc", "big5", "joyo"]
        # 塩 is a Japanese shinjitai — joyo only
        assert tables_for([ord("塩")]) == ["joyo"]
        # 龜 is traditional — Big5 (also joyo? 亀 is joyo, 龜 is not)
        assert "big5" in tables_for([ord("龜")])
        assert tables_for([0x00A7]) == []


class TestPronunciationEntries:
    def test_empty_before_build(self, store):
        from webapp.backend.services.glyph_catalog import _pronunciation_entries

        project = store.create("Test")
        assert project.tasks["build"].status == "idle"
        assert _pronunciation_entries(project) == []

    def test_empty_when_output_missing(self, store):
        from webapp.backend.services.glyph_catalog import _pronunciation_entries

        project = store.create("Test")
        project.tasks["build"] = project.tasks["build"].model_copy(
            update={"status": "done"}
        )
        # No output TTF on disk -> nothing to list
        assert _pronunciation_entries(project) == []
