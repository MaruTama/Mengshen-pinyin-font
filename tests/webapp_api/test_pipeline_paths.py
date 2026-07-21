# -*- coding: utf-8 -*-
"""Per-project template path resolution and legacy fallback."""

from __future__ import annotations

import pytest

from webapp.backend.services import pipeline


@pytest.fixture
def scoped_settings(store, tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline.settings, "PROJECTS_DIR", store.projects_dir)
    monkeypatch.setattr(pipeline.settings, "JSON_TEMP_DIR", tmp_path / "shared_json")
    (tmp_path / "shared_json").mkdir()
    return store


class TestTemplatePaths:
    def test_defaults_to_project_scoped_paths(self, scoped_settings):
        project = scoped_settings.create("Test")
        paths = pipeline.template_paths_for(project)
        json_dir = scoped_settings.json_dir(project.id)
        assert paths["template_main"] == json_dir / "template_main.json"
        assert paths["template_glyf"] == json_dir / "template_glyf.json"
        assert paths["alphabet_pinyin"] == json_dir / "alphabet_for_pinyin.json"

    def test_falls_back_to_legacy_shared_files(self, scoped_settings):
        project = scoped_settings.create("Test")
        style = pipeline.style_for(project)
        legacy = pipeline.settings.JSON_TEMP_DIR / f"template_main_{style}.json"
        legacy.write_text("{}")

        paths = pipeline.template_paths_for(project)
        assert paths["template_main"] == legacy
        # Others have no legacy file -> project-scoped
        assert paths["template_glyf"].parent == scoped_settings.json_dir(project.id)

    def test_project_file_wins_over_legacy(self, scoped_settings):
        project = scoped_settings.create("Test")
        style = pipeline.style_for(project)
        (pipeline.settings.JSON_TEMP_DIR / f"template_main_{style}.json").write_text(
            "{}"
        )
        json_dir = scoped_settings.json_dir(project.id)
        json_dir.mkdir(parents=True)
        new_path = json_dir / "template_main.json"
        new_path.write_text("{}")

        assert pipeline.template_paths_for(project)["template_main"] == new_path

    def test_scoped_paths_redirect_temp_json(self, scoped_settings):
        project = scoped_settings.create("Test")
        paths = pipeline.ProjectScopedPaths(project)
        target = paths.get_temp_json_path("template_output.json")
        assert target.parent == scoped_settings.json_dir(project.id)
        # outputs_dir must stay at the repo root (GSUB pattern files)
        assert paths.outputs_dir == pipeline.settings.PATHS.outputs_dir
