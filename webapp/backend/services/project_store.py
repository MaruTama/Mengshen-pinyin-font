# -*- coding: utf-8 -*-
"""Atomic JSON persistence for webapp projects under tmp/projects/<id>/."""

from __future__ import annotations

import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from src.refactored.config.font_config import FontConfig, FontType

from .. import settings
from ..schemas import (
    CanvasModel,
    HanziCanvasModel,
    PinyinCanvasModel,
    Project,
)

PROJECT_FILENAME = "project.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_canvas(style: str = "han_serif") -> CanvasModel:
    """Seed canvas values from the bundled preset configs."""
    font_type = FontType(style)
    config = FontConfig.get_config(font_type)
    return CanvasModel(
        pinyin=PinyinCanvasModel(
            width=config.pinyin_canvas.width,
            height=config.pinyin_canvas.height,
            base_line=config.pinyin_canvas.base_line,
            tracking=config.pinyin_canvas.tracking,
        ),
        hanzi=HanziCanvasModel(
            width=config.hanzi_canvas.width,
            height=config.hanzi_canvas.height,
        ),
        is_avoid_overlapping_mode=config.is_avoid_overlapping_mode,
        x_scale_reduction_for_avoid_overlapping=(
            config.x_scale_reduction_for_avoid_overlapping
        ),
    )


class ProjectStore:
    """CRUD for project.json files with atomic writes."""

    def __init__(self, projects_dir: Optional[Path] = None):
        self.projects_dir = projects_dir or settings.PROJECTS_DIR
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def project_dir(self, project_id: str) -> Path:
        return self.projects_dir / project_id

    def fonts_dir(self, project_id: str) -> Path:
        return self.project_dir(project_id) / "fonts"

    def json_dir(self, project_id: str) -> Path:
        """Per-project intermediate JSONs (templates, build output)."""
        return self.project_dir(project_id) / "json"

    def _project_path(self, project_id: str) -> Path:
        return self.project_dir(project_id) / PROJECT_FILENAME

    def create(self, name: str) -> Project:
        project_id = uuid.uuid4().hex[:8]
        now = _now()
        project = Project(
            id=project_id,
            name=name,
            created_at=now,
            updated_at=now,
            canvas=default_canvas(),
        )
        self.fonts_dir(project_id).mkdir(parents=True, exist_ok=True)
        self.save(project)
        return project

    def get(self, project_id: str) -> Optional[Project]:
        path = self._project_path(project_id)
        if not path.exists():
            return None
        return Project.model_validate_json(path.read_text(encoding="utf-8"))

    def list(self) -> List[Project]:
        projects = []
        for entry in sorted(self.projects_dir.iterdir()):
            if (entry / PROJECT_FILENAME).exists():
                project = self.get(entry.name)
                if project is not None:
                    projects.append(project)
        return projects

    def save(self, project: Project) -> Project:
        project.updated_at = _now()
        path = self._project_path(project.id)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(".json.tmp")
        tmp_path.write_text(project.model_dump_json(indent=2), encoding="utf-8")
        os.replace(tmp_path, path)
        return project

    def delete(self, project_id: str) -> bool:
        """Delete the project directory and its generated artifacts."""
        project = self.get(project_id)
        if project is None:
            return False

        # GC per-project template JSONs and outputs referenced by the project
        for artifact in project.artifacts.values():
            artifact_path = Path(artifact)
            if not artifact_path.is_absolute():
                artifact_path = settings.PATHS.project_root / artifact_path
            if artifact_path.exists() and artifact_path.is_file():
                artifact_path.unlink()

        output_dir = settings.OUTPUTS_DIR / project_id
        if output_dir.exists():
            shutil.rmtree(output_dir)

        shutil.rmtree(self.project_dir(project_id))
        return True
