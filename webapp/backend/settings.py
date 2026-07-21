# -*- coding: utf-8 -*-
"""Webapp settings anchored on the existing project path conventions."""

from __future__ import annotations

import shutil
from pathlib import Path

from src.refactored.config.paths import ProjectPaths

PATHS = ProjectPaths()

# All intermediate webapp state lives under tmp/ (project convention)
PROJECTS_DIR = PATHS.temp_dir / "projects"
JSON_TEMP_DIR = PATHS.json_temp_dir
OUTPUTS_DIR = PATHS.outputs_dir / "webapp"

FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"

REQUIRED_TOOLS = ["otfccdump", "otfccbuild", "jq"]


def ensure_directories() -> None:
    for directory in (PROJECTS_DIR, JSON_TEMP_DIR, OUTPUTS_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def missing_tools() -> list[str]:
    return [tool for tool in REQUIRED_TOOLS if shutil.which(tool) is None]
