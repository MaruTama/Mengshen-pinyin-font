# -*- coding: utf-8 -*-
"""Shared singletons for API routers."""

from __future__ import annotations

from fastapi import HTTPException

from ..schemas import Project
from ..services.project_store import ProjectStore
from ..services.task_manager import TaskManager

store = ProjectStore()
tasks = TaskManager(store)


def get_project_or_404(project_id: str) -> Project:
    project = store.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")
    return project
