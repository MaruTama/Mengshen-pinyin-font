# -*- coding: utf-8 -*-
"""API route tests with an isolated project store (pipeline not executed)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(store, monkeypatch):
    from webapp.backend.api import deps
    from webapp.backend.main import create_app
    from webapp.backend.services.task_manager import TaskManager

    monkeypatch.setattr(deps, "store", store)
    monkeypatch.setattr(deps, "tasks", TaskManager(store))
    # Routers capture `store`/`tasks` at import; patch those references too
    from webapp.backend.api import build, glyphs, projects, readings

    for module in (build, glyphs, projects, readings):
        monkeypatch.setattr(module, "store", store, raising=False)
    monkeypatch.setattr(build, "tasks", deps.tasks, raising=False)

    return TestClient(create_app())


class TestProjectRoutes:
    def test_create_and_get(self, client):
        created = client.post("/api/projects", json={"name": "Test"}).json()
        assert created["name"] == "Test"
        fetched = client.get(f"/api/projects/{created['id']}").json()
        assert fetched["id"] == created["id"]
        assert fetched["canvas"]["pinyin"]["width"] == 850.0

    def test_get_missing_returns_404(self, client):
        assert client.get("/api/projects/nope").status_code == 404

    def test_patch_canvas(self, client):
        project = client.post("/api/projects", json={"name": "Test"}).json()
        canvas = project["canvas"]
        canvas["pinyin"]["tracking"] = 42.0
        patched = client.patch(
            f"/api/projects/{project['id']}", json={"canvas": canvas}
        ).json()
        assert patched["canvas"]["pinyin"]["tracking"] == 42.0

    def test_select_builtin_seeds_canvas_and_license(self, client):
        project = client.post("/api/projects", json={"name": "Test"}).json()
        result = client.put(
            f"/api/projects/{project['id']}/fonts/base/builtin",
            json={"style": "handwritten"},
        )
        assert result.status_code == 200
        body = result.json()
        assert body["base_font"]["source"] == "builtin:handwritten"
        # handwritten preset canvas seeded
        assert body["canvas"]["pinyin"]["base_line"] == 880.0
        assert body["license"]["base"]["acknowledged"] is False
        assert len(body["license"]["base"]["entries"]) > 0

    def test_acknowledge_requires_font(self, client):
        project = client.post("/api/projects", json={"name": "Test"}).json()
        result = client.post(
            f"/api/projects/{project['id']}/license/acknowledge",
            json={"role": "base", "acknowledged": True},
        )
        assert result.status_code == 409

    def test_build_requires_acknowledgment(self, client):
        project = client.post("/api/projects", json={"name": "Test"}).json()
        client.put(
            f"/api/projects/{project['id']}/fonts/base/builtin",
            json={"style": "han_serif"},
        )
        client.put(
            f"/api/projects/{project['id']}/fonts/pinyin/builtin",
            json={"style": "han_serif"},
        )
        result = client.post(f"/api/projects/{project['id']}/build")
        assert result.status_code == 409
        assert result.json()["detail"]["code"] == "license_not_acknowledged"


class TestBuildInvalidation:
    """A stale TTF must never look downloadable."""

    @pytest.fixture
    def built_project(self, client, store):
        project = client.post("/api/projects", json={"name": "Test"}).json()
        client.put(
            f"/api/projects/{project['id']}/fonts/base/builtin",
            json={"style": "han_serif"},
        )
        # Simulate a completed build directly in the store
        saved = store.get(project["id"])
        saved.tasks["build"] = saved.tasks["build"].model_copy(
            update={"status": "done", "progress": 1.0}
        )
        store.save(saved)
        return project["id"]

    def test_download_requires_build_done(self, client):
        project = client.post("/api/projects", json={"name": "Test"}).json()
        result = client.get(f"/api/projects/{project['id']}/download")
        assert result.status_code == 409
        assert result.json()["detail"]["code"] == "build_not_current"

    def test_font_change_resets_build(self, client, built_project):
        body = client.put(
            f"/api/projects/{built_project}/fonts/base/builtin",
            json={"style": "handwritten"},
        ).json()
        assert body["tasks"]["build"]["status"] == "idle"
        assert client.get(f"/api/projects/{built_project}/download").status_code == 409

    def test_canvas_change_resets_build(self, client, built_project):
        canvas = client.get(f"/api/projects/{built_project}").json()["canvas"]
        canvas["pinyin"]["tracking"] = 99.0
        body = client.patch(
            f"/api/projects/{built_project}", json={"canvas": canvas}
        ).json()
        assert body["tasks"]["build"]["status"] == "idle"

    def test_identical_canvas_patch_keeps_build(self, client, built_project):
        canvas = client.get(f"/api/projects/{built_project}").json()["canvas"]
        body = client.patch(
            f"/api/projects/{built_project}", json={"canvas": canvas}
        ).json()
        assert body["tasks"]["build"]["status"] == "done"

    def test_reading_change_resets_build(self, client, built_project):
        client.put(
            f"/api/projects/{built_project}/readings/中",
            json={"mode": "replace", "pronunciations": ["zhòng"]},
        )
        project = client.get(f"/api/projects/{built_project}").json()
        assert project["tasks"]["build"]["status"] == "idle"


class TestReadingsRoutes:
    @pytest.fixture
    def project_id(self, client):
        return client.post("/api/projects", json={"name": "Test"}).json()["id"]

    def test_set_and_delete_override(self, client, project_id):
        result = client.put(
            f"/api/projects/{project_id}/readings/中",
            json={"mode": "replace", "pronunciations": ["zhòng"]},
        )
        assert result.status_code == 200
        assert result.json()["readings"] == ["zhòng"]

        result = client.delete(f"/api/projects/{project_id}/readings/中")
        assert result.status_code == 200
        assert result.json()["readings"][0] == "zhōng"

    def test_invalid_syllable_rejected(self, client, project_id):
        result = client.put(
            f"/api/projects/{project_id}/readings/中",
            json={"mode": "replace", "pronunciations": ["漢字"]},
        )
        assert result.status_code == 422

    def test_reordered_list_saved_and_base_order_clears_override(
        self, client, project_id
    ):
        # Reorder: zhòng first
        result = client.put(
            f"/api/projects/{project_id}/readings/中",
            json={"mode": "replace", "pronunciations": ["zhòng", "zhōng"]},
        )
        assert result.json()["readings"] == ["zhòng", "zhōng"]
        assert result.json()["override"] is not None

        # Restoring the base order removes the override entirely
        result = client.put(
            f"/api/projects/{project_id}/readings/中",
            json={"mode": "replace", "pronunciations": ["zhōng", "zhòng"]},
        )
        assert result.json()["override"] is None

    def test_append_mode(self, client, project_id):
        result = client.put(
            f"/api/projects/{project_id}/readings/中",
            json={"mode": "append", "pronunciations": ["zong1"]},
        )
        readings = result.json()["readings"]
        assert readings[0] == "zhōng"
        assert "zong1" in readings


class TestDuoyinziRoutes:
    def test_list_and_detail(self, client):
        project_id = client.post("/api/projects", json={"name": "T"}).json()["id"]
        listing = client.get(f"/api/projects/{project_id}/duoyinzi?size=5").json()
        assert listing["total"] > 100
        assert len(listing["items"]) == 5

        detail = client.get(f"/api/projects/{project_id}/duoyinzi/中").json()
        assert detail["char"] == "中"
        assert "zhōng" in detail["readings"]

    def test_gsub_requires_prepare(self, client):
        project_id = client.post("/api/projects", json={"name": "T"}).json()["id"]
        result = client.get(f"/api/projects/{project_id}/gsub")
        assert result.status_code == 409
