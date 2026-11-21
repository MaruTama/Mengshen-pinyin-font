# -*- coding: utf-8 -*-
"""Custom (composed) pinyin letter glyphs: service, API, readings, build."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from webapp.backend.schemas import CustomGlyphRecipe, ReadingOverride
from webapp.backend.services import custom_glyphs, glyph_composer
from webapp.backend.services.preview_composer import _FontOutlines

E_MACRON_CIRCUMFLEX = "ê̄"  # ê̄
E_CIRCUMFLEX = "ê"  # ê
M_MACRON = "m̄"  # m̄


@pytest.fixture(autouse=True)
def no_bundles(tmp_path, monkeypatch):
    """Most tests need builtin fonts to *lack* letters: hide the bundles."""
    from src.refactored.utils import bundled_glyphs

    empty = tmp_path / "no_bundles"
    empty.mkdir()
    monkeypatch.setattr(bundled_glyphs, "BUNDLED_GLYPHS_DIR", empty)


@pytest.fixture
def client(store, monkeypatch):
    from webapp.backend.api import deps
    from webapp.backend.main import create_app
    from webapp.backend.services.task_manager import TaskManager

    monkeypatch.setattr(deps, "store", store)
    monkeypatch.setattr(deps, "tasks", TaskManager(store))
    from webapp.backend.api import build, glyphs, pinyin_letters, projects, readings

    for module in (build, glyphs, pinyin_letters, projects, readings):
        monkeypatch.setattr(module, "store", store, raising=False)
    monkeypatch.setattr(build, "tasks", deps.tasks, raising=False)
    return TestClient(create_app())


def _project(client, style: str) -> str:
    project_id = client.post("/api/projects", json={"name": "T"}).json()["id"]
    result = client.put(
        f"/api/projects/{project_id}/fonts/pinyin/builtin", json={"style": style}
    )
    assert result.status_code == 200
    return project_id


def _letters(client, project_id) -> dict:
    body = client.get(f"/api/projects/{project_id}/pinyin-letters").json()
    return {row["letter"]: row for row in body["letters"]}


class TestFontGlyph:
    def test_extracts_quadratic_contours(self, store):
        from src.refactored.config.font_config import FontConstants

        outlines = _FontOutlines(str(FontConstants.HAN_SERIF_ALPHABET_FONT_PATH), "x")
        glyph = custom_glyphs.font_glyph(outlines, "ē")
        assert glyph is not None
        assert glyph["advanceWidth"] > 0
        assert len(glyph["contours"]) >= 3  # e outer + counter + macron
        assert custom_glyphs.font_glyph(outlines, E_MACRON_CIRCUMFLEX) is None

    def test_compose_e_circumflex_macron_from_mplus(self, store):
        from src.refactored.config.font_config import FontConstants

        outlines = _FontOutlines(str(FontConstants.HAN_SERIF_ALPHABET_FONT_PATH), "x")
        base = custom_glyphs.font_glyph(outlines, E_CIRCUMFLEX)
        result = custom_glyphs.compose_letter(
            None,
            outlines,
            CustomGlyphRecipe(base=E_CIRCUMFLEX, mark_source="ē"),
        )
        mark = result.glyph["contours"][result.base_contour_count :]
        assert len(mark) == len(result.mark_contours) >= 1
        base_top = glyph_composer.bbox(base["contours"])[3]
        assert glyph_composer.bbox(mark)[1] > base_top


class TestDefaults:
    def test_default_recipes(self):
        recipes = custom_glyphs.DEFAULT_RECIPES
        assert recipes[E_CIRCUMFLEX] == ("e", "ě", True)
        assert recipes[E_MACRON_CIRCUMFLEX] == (E_CIRCUMFLEX, "ē", False)
        assert recipes[M_MACRON] == ("m", "ē", False)
        for letter in ["ế", "ê̌", "ề", "m̀", "ḿ", "ń", "ň", "ǹ"]:
            assert letter in recipes


class TestLettersApi:
    def test_status_handwritten(self, client):
        project_id = _project(client, "handwritten")
        letters = _letters(client, project_id)
        assert letters["ē"]["status"] == "font"
        assert letters["ḿ"]["status"] == "font"
        for letter in [E_CIRCUMFLEX, E_MACRON_CIRCUMFLEX, "ế", M_MACRON, "m̀"]:
            assert letters[letter]["status"] == "missing", letter
        assert letters[E_MACRON_CIRCUMFLEX]["name"] == "eh1"
        assert letters[E_MACRON_CIRCUMFLEX]["default_recipe"]["base"] == E_CIRCUMFLEX

    def test_status_han_serif_has_precomposed_eh(self, client):
        project_id = _project(client, "han_serif")
        letters = _letters(client, project_id)
        assert letters[E_CIRCUMFLEX]["status"] == "font"
        assert letters["ế"]["status"] == "font"
        assert letters[E_MACRON_CIRCUMFLEX]["status"] == "missing"

    def test_requires_pinyin_font(self, client):
        project_id = client.post("/api/projects", json={"name": "T"}).json()["id"]
        result = client.get(f"/api/projects/{project_id}/pinyin-letters")
        assert result.status_code == 409

    def test_preview_does_not_save(self, client):
        project_id = _project(client, "handwritten")
        result = client.post(
            f"/api/projects/{project_id}/pinyin-letters/eh/preview",
            json={"base": "e", "mark_source": "ě", "flip_y": True},
        )
        assert result.status_code == 200, result.json()
        body = result.json()
        assert body["mark_path"].startswith("M")
        assert body["base_path"].startswith("M")
        assert body["glyph"]["contours"]
        assert _letters(client, project_id)[E_CIRCUMFLEX]["status"] == "missing"

    def test_save_chain_and_delete(self, client, store):
        project_id = _project(client, "handwritten")
        saved = store.get(project_id)
        saved.tasks["build"] = saved.tasks["build"].model_copy(
            update={"status": "done"}
        )
        store.save(saved)

        # ê̄ needs ê first
        result = client.put(
            f"/api/projects/{project_id}/pinyin-letters/eh1",
            json={"base": E_CIRCUMFLEX, "mark_source": "ē"},
        )
        assert result.status_code == 422
        assert result.json()["detail"]["code"] == "glyph_unavailable"

        result = client.put(
            f"/api/projects/{project_id}/pinyin-letters/eh",
            json={"base": "e", "mark_source": "ě", "flip_y": True, "dy": 5},
        )
        assert result.status_code == 200, result.json()
        assert result.json()["status"] == "custom"
        project = store.get(project_id)
        assert project.tasks["build"].status == "idle"
        stored = project.glyph_overrides.custom_glyphs["eh"]
        assert stored.letter == E_CIRCUMFLEX
        assert stored.recipe.dy == 5
        assert stored.font_sha256 == project.pinyin_font.sha256

        result = client.put(
            f"/api/projects/{project_id}/pinyin-letters/eh1",
            json={"base": E_CIRCUMFLEX, "mark_source": "ē"},
        )
        assert result.status_code == 200, result.json()
        letters = _letters(client, project_id)
        assert letters[E_MACRON_CIRCUMFLEX]["status"] == "custom"
        assert letters[E_MACRON_CIRCUMFLEX]["recipe"]["mark_source"] == "ē"

        result = client.delete(f"/api/projects/{project_id}/pinyin-letters/eh1")
        assert result.status_code == 200
        assert result.json()["status"] == "missing"
        result = client.delete(f"/api/projects/{project_id}/pinyin-letters/eh1")
        assert result.status_code == 404

    def test_letter_in_font_cannot_be_overridden(self, client):
        project_id = _project(client, "handwritten")
        result = client.put(
            f"/api/projects/{project_id}/pinyin-letters/e1",
            json={"base": "e", "mark_source": "ē"},
        )
        assert result.status_code == 409
        assert result.json()["detail"]["code"] == "letter_in_font"

    def test_unknown_letter(self, client):
        project_id = _project(client, "handwritten")
        result = client.post(
            f"/api/projects/{project_id}/pinyin-letters/zz9/preview",
            json={"base": "e", "mark_source": "ē"},
        )
        assert result.status_code == 404

    def test_mark_not_found(self, client):
        project_id = _project(client, "handwritten")
        result = client.post(
            f"/api/projects/{project_id}/pinyin-letters/m1/preview",
            json={"base": "m", "mark_source": "e"},
        )
        assert result.status_code == 422
        assert result.json()["detail"]["code"] == "mark_not_found"

    def test_stale_after_pinyin_font_change(self, client, store):
        project_id = _project(client, "handwritten")
        client.put(
            f"/api/projects/{project_id}/pinyin-letters/m1",
            json={"base": "m", "mark_source": "ē"},
        )
        client.put(
            f"/api/projects/{project_id}/fonts/pinyin/builtin",
            json={"style": "han_serif"},
        )
        row = _letters(client, project_id)[M_MACRON]
        assert row["status"] == "missing"
        assert row["stale"] is True


class TestReadingsValidation:
    def test_missing_glyph_rejected_then_accepted(self, client):
        project_id = _project(client, "handwritten")
        result = client.put(
            f"/api/projects/{project_id}/readings/欸",
            json={"mode": "replace", "pronunciations": [E_MACRON_CIRCUMFLEX]},
        )
        assert result.status_code == 422
        detail = result.json()["detail"]
        assert detail["code"] == "missing_glyph"
        assert detail["params"]["letter"] == E_MACRON_CIRCUMFLEX
        assert detail["params"]["name"] == "eh1"

        client.put(
            f"/api/projects/{project_id}/pinyin-letters/eh",
            json={"base": "e", "mark_source": "ě", "flip_y": True},
        )
        client.put(
            f"/api/projects/{project_id}/pinyin-letters/eh1",
            json={"base": E_CIRCUMFLEX, "mark_source": "ē"},
        )
        result = client.put(
            f"/api/projects/{project_id}/readings/欸",
            json={"mode": "replace", "pronunciations": [E_MACRON_CIRCUMFLEX]},
        )
        assert result.status_code == 200, result.json()

    def test_decomposed_input_is_normalized(self, client):
        project_id = _project(client, "handwritten")
        result = client.put(
            f"/api/projects/{project_id}/readings/呣",
            json={"mode": "replace", "pronunciations": ["m̀"]},
        )
        assert result.json()["detail"]["code"] == "missing_glyph"

    def test_letter_in_font_accepted(self, client):
        project_id = _project(client, "handwritten")
        result = client.put(
            f"/api/projects/{project_id}/readings/呣",
            json={"mode": "replace", "pronunciations": ["ḿ"]},
        )
        assert result.status_code == 200, result.json()

    def test_invalid_syllable_still_distinct(self, client):
        project_id = _project(client, "handwritten")
        result = client.put(
            f"/api/projects/{project_id}/readings/中",
            json={"mode": "replace", "pronunciations": ["漢字"]},
        )
        assert result.json()["detail"]["code"] == "invalid_syllable"


class TestCatalog:
    def test_custom_entries_and_thumbnail(self, client, store):
        from webapp.backend.services import glyph_catalog

        project_id = _project(client, "handwritten")
        client.put(
            f"/api/projects/{project_id}/pinyin-letters/m1",
            json={"base": "m", "mark_source": "ē"},
        )
        project = store.get(project_id)
        entries = glyph_catalog.custom_entries(project)
        assert [e["name"] for e in entries] == ["py_alphabet_m1"]
        entry = entries[0]
        assert entry["font"] == "custom"
        assert entry["category"] == "pinyin_alphabet"
        assert entry["char"] == M_MACRON
        assert "<path" in glyph_catalog.thumbnail_svg(project, entry)

    def test_index_key_tracks_custom_glyphs(self, client, store):
        from webapp.backend.services import glyph_catalog

        project_id = _project(client, "handwritten")
        before = glyph_catalog._fonts_key(store.get(project_id))
        client.put(
            f"/api/projects/{project_id}/pinyin-letters/m1",
            json={"base": "m", "mark_source": "ē"},
        )
        assert glyph_catalog._fonts_key(store.get(project_id)) != before


class TestMergeIntoAlphabet:
    @pytest.fixture
    def project(self, client, store, monkeypatch, tmp_path):
        from webapp.backend.services import pipeline

        monkeypatch.setattr(pipeline.settings, "PROJECTS_DIR", store.projects_dir)
        monkeypatch.setattr(pipeline.settings, "JSON_TEMP_DIR", tmp_path / "shared")
        project_id = _project(client, "handwritten")
        client.put(
            f"/api/projects/{project_id}/pinyin-letters/m1",
            json={"base": "m", "mark_source": "ē"},
        )
        return store.get(project_id)

    def test_merge_adds_and_removes(self, project, store):
        from webapp.backend.services import pipeline

        alphabet = pipeline.project_json_dir(project) / "alphabet_for_pinyin.json"
        alphabet.parent.mkdir(parents=True, exist_ok=True)
        alphabet.write_text(
            json.dumps({"m": {"advanceWidth": 1, "contours": []}}), encoding="utf-8"
        )

        pipeline.write_merged_alphabet(project)
        merged = json.loads(alphabet.read_text(encoding="utf-8"))
        assert set(merged) == {"m", M_MACRON}
        assert merged[M_MACRON]["contours"]

        # Deleting the custom glyph removes it on the next merge
        project.glyph_overrides.custom_glyphs.clear()
        pipeline.write_merged_alphabet(project)
        merged = json.loads(alphabet.read_text(encoding="utf-8"))
        assert set(merged) == {"m"}

    def test_preview_uses_custom_glyph(self, project, client, store):
        from webapp.backend.services import preview_composer

        client.put(
            f"/api/projects/{project.id}/fonts/base/builtin",
            json={"style": "handwritten"},
        )
        fresh = store.get(project.id)
        fresh.glyph_overrides.readings["呣"] = ReadingOverride(
            pronunciations=[M_MACRON]
        )
        detail = preview_composer.compose_detail(fresh, "呣", fresh.canvas)
        assert detail.pinyin == M_MACRON
        assert len(detail.pinyin_glyphs) == 1
        assert detail.pinyin_glyphs[0].label == M_MACRON
        assert detail.pinyin_glyphs[0].path.startswith("M")


class TestBundledGlyphs:
    """Builtin pinyin fonts ship composed letters (res/fonts/custom_pinyin_glyphs)."""

    @pytest.fixture
    def no_bundles(self):
        """Override the module-level fixture: use the real bundles."""

    def test_bundled_letters_count_as_available(self, client):
        project_id = _project(client, "handwritten")
        letters = _letters(client, project_id)
        for letter in [E_CIRCUMFLEX, E_MACRON_CIRCUMFLEX, "ế", M_MACRON, "m̀"]:
            assert letters[letter]["status"] == "bundled", letter
        assert letters["ē"]["status"] == "font"
        assert not [r for r in letters.values() if r["status"] == "missing"]

    def test_bundled_letter_cannot_be_overridden(self, client):
        project_id = _project(client, "handwritten")
        result = client.put(
            f"/api/projects/{project_id}/pinyin-letters/m1",
            json={"base": "m", "mark_source": "ē"},
        )
        assert result.status_code == 409
        assert result.json()["detail"]["code"] == "letter_in_font"

    def test_bundled_letters_usable_as_base(self, client):
        project_id = _project(client, "handwritten")
        result = client.post(
            f"/api/projects/{project_id}/pinyin-letters/eh1/preview",
            json={"base": E_CIRCUMFLEX, "mark_source": "ē"},
        )
        assert result.status_code == 200, result.json()

    def test_reading_with_bundled_letter_accepted(self, client):
        project_id = _project(client, "handwritten")
        result = client.put(
            f"/api/projects/{project_id}/readings/欸",
            json={"mode": "replace", "pronunciations": [E_MACRON_CIRCUMFLEX]},
        )
        assert result.status_code == 200, result.json()

    def test_preview_and_catalog_render_bundled(self, client, store):
        from webapp.backend.services import glyph_catalog, preview_composer

        project_id = _project(client, "handwritten")
        client.put(
            f"/api/projects/{project_id}/fonts/base/builtin",
            json={"style": "handwritten"},
        )
        project = store.get(project_id)
        project.glyph_overrides.readings["呣"] = ReadingOverride(
            pronunciations=[M_MACRON]
        )
        detail = preview_composer.compose_detail(project, "呣", project.canvas)
        assert [g.label for g in detail.pinyin_glyphs] == [M_MACRON]

        entries = {e["name"]: e for e in glyph_catalog.custom_entries(project)}
        assert entries["py_alphabet_m1"]["font"] == "bundled"
        assert "<path" in glyph_catalog.thumbnail_svg(
            project, entries["py_alphabet_m1"]
        )


class TestSingleStoryA:
    """Issue #15: pinyin a is the single-story ɑ in both builtin styles.

    The bundles' ``overrides`` replace letters the font does have.
    """

    A_FAMILY = ["a", "ā", "á", "ǎ", "à"]

    @pytest.fixture
    def no_bundles(self):
        """Override the module-level fixture: use the real bundles."""

    @staticmethod
    def _font_path(style):
        from src.refactored.config.font_config import FontConfig, FontType

        return FontConfig.get_alphabet_font_path(FontType(style))

    def _outlines(self, style):
        return _FontOutlines(str(self._font_path(style)), f"t:{style}")

    def _overrides(self, style):
        from src.refactored.utils import bundled_glyphs

        return bundled_glyphs.bundled_overrides_for_font(self._font_path(style))

    def test_han_serif_a_family_is_alpha_plus_mark(self):
        outlines = self._outlines("han_serif")
        alpha = custom_glyphs.font_glyph(outlines, "ɑ")
        plain = custom_glyphs.font_glyph(outlines, "a")
        overrides = self._overrides("han_serif")
        assert overrides["a"]["contours"] == alpha["contours"]
        alpha_box = glyph_composer.bbox(alpha["contours"])
        alpha_center = (alpha_box[0] + alpha_box[2]) / 2
        plain_box = glyph_composer.bbox(plain["contours"])
        plain_center = (plain_box[0] + plain_box[2]) / 2
        body_count = len(alpha["contours"])
        for letter in ["ā", "á", "ǎ", "à"]:
            glyph = overrides[letter]
            assert glyph["contours"][:body_count] == alpha["contours"], letter
            mark = glyph["contours"][body_count:]
            source = custom_glyphs.font_glyph(outlines, letter)
            source_mark = [
                source["contours"][i]
                for i in glyph_composer.detect_mark_contours(source, plain)
            ]
            assert len(mark) == len(source_mark) >= 1, letter
            mark_box = glyph_composer.bbox(mark)
            source_box = glyph_composer.bbox(source_mark)
            # same mark at the same height, re-centered over ɑ keeping its
            # designed offset from the body center (acute right, grave left)
            assert mark_box[1] == source_box[1], letter
            assert mark_box[3] == source_box[3], letter
            assert mark_box[2] - mark_box[0] == source_box[2] - source_box[0]
            mark_offset = (mark_box[0] + mark_box[2]) / 2 - alpha_center
            source_offset = (source_box[0] + source_box[2]) / 2 - plain_center
            assert abs(mark_offset - source_offset) <= 1, letter
            assert glyph["advanceWidth"] == alpha["advanceWidth"]

    def test_handwritten_a_family_is_caron_a_body(self):
        """Seto's only single-story a is ǎ: a = ǎ minus the caron, and
        ā á à = that body + their own tone marks (ǎ stays the font's)."""
        outlines = self._outlines("handwritten")
        caron = custom_glyphs.font_glyph(outlines, "ǎ")
        overrides = self._overrides("handwritten")
        assert "ǎ" not in overrides
        body = overrides["a"]
        assert len(body["contours"]) == len(caron["contours"]) - 1
        assert all(c in caron["contours"] for c in body["contours"])
        assert body["advanceWidth"] == caron["advanceWidth"]
        body_box = glyph_composer.bbox(body["contours"])
        caron_mark = [c for c in caron["contours"] if c not in body["contours"]]
        caron_gap = glyph_composer.bbox(caron_mark)[1] - body_box[3]
        for letter in ["ā", "á", "à"]:
            glyph = overrides[letter]
            count = len(body["contours"])
            assert glyph["contours"][:count] == body["contours"], letter
            mark_box = glyph_composer.bbox(glyph["contours"][count:])
            # every mark sits the same distance above the body as ǎ's caron
            assert abs(mark_box[1] - body_box[3] - caron_gap) <= 1, letter
            assert glyph["advanceWidth"] == caron["advanceWidth"]

    @pytest.mark.parametrize("style", ["han_serif", "handwritten"])
    def test_status_is_bundled(self, client, style):
        project_id = _project(client, style)
        letters = _letters(client, project_id)
        for letter in self._overrides(style):
            assert letters[letter]["status"] == "bundled", letter
        assert letters["e"]["status"] == "font"
        assert not [r for r in letters.values() if r["status"] == "missing"]

    def test_lookup_preview_and_catalog_use_override(self, client, store):
        from webapp.backend.services import glyph_catalog, preview_composer

        project_id = _project(client, "han_serif")
        client.put(
            f"/api/projects/{project_id}/fonts/base/builtin",
            json={"style": "han_serif"},
        )
        project = store.get(project_id)
        overrides = self._overrides("han_serif")
        outlines = self._outlines("han_serif")
        looked_up = custom_glyphs.lookup_glyph(project, outlines, "ǎ")
        assert looked_up["contours"] == overrides["ǎ"]["contours"]

        project.glyph_overrides.readings["啊"] = ReadingOverride(
            mode="replace", pronunciations=["ā"]
        )
        detail = preview_composer.compose_detail(project, "啊", project.canvas)
        assert [g.label for g in detail.pinyin_glyphs] == ["ā"]
        assert detail.pinyin_glyphs[0].path == glyph_composer.contours_to_svg_path(
            overrides["ā"]["contours"]
        )

        pinyin_a = [
            e
            for e in glyph_catalog._build_index(project)
            if e["category"] == "pinyin_alphabet" and e["char"] in self.A_FAMILY
        ]
        assert sorted(e["name"] for e in pinyin_a) == sorted(
            f"py_alphabet_{name}" for name in ["a", "a1", "a2", "a3", "a4"]
        )
        assert {e["font"] for e in pinyin_a} == {"bundled"}
        entry = next(e for e in pinyin_a if e["char"] == "a")
        assert "<path" in glyph_catalog.thumbnail_svg(project, entry)
