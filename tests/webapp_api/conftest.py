# -*- coding: utf-8 -*-
"""Fixtures for webapp tests: isolated project store in a temp directory."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# webapp modules import as `webapp.*` / `src.refactored.*` from the repo root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from webapp.backend.services.project_store import ProjectStore  # noqa: E402


@pytest.fixture
def store(tmp_path):
    return ProjectStore(projects_dir=tmp_path / "projects")
