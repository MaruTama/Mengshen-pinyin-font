# -*- coding: utf-8 -*-
"""ProjectStore persistence tests."""

from __future__ import annotations

from webapp.backend.schemas import Project


class TestProjectStore:
    def test_create_seeds_han_serif_canvas_defaults(self, store):
        project = store.create("Test")
        assert project.canvas.pinyin.width == 850.0
        assert project.canvas.pinyin.base_line == 935.0
        assert project.tasks["prepare"].status == "idle"

    def test_roundtrip(self, store):
        project = store.create("Test")
        project.name = "Renamed"
        project.canvas.pinyin.tracking = 30.0
        store.save(project)

        loaded = store.get(project.id)
        assert isinstance(loaded, Project)
        assert loaded.name == "Renamed"
        assert loaded.canvas.pinyin.tracking == 30.0

    def test_atomic_write_leaves_no_tmp_file(self, store):
        project = store.create("Test")
        project_dir = store.project_dir(project.id)
        leftovers = list(project_dir.glob("*.tmp"))
        assert leftovers == []

    def test_delete_removes_directory(self, store):
        project = store.create("Test")
        assert store.delete(project.id) is True
        assert store.get(project.id) is None
        assert not store.project_dir(project.id).exists()

    def test_get_missing_returns_none(self, store):
        assert store.get("nonexistent") is None
