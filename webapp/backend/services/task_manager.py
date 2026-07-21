# -*- coding: utf-8 -*-
"""Background task execution for prepare/build with state in project.json."""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Callable, Optional

from ..schemas import Project, TaskKind, TaskState
from .project_store import ProjectStore


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class TaskManager:
    """Serializes heavy pipeline jobs on a single worker thread.

    otfccdump/otfccbuild jobs are memory- and CPU-heavy, and
    TemplateJsonMaker uses a shared temp file in tmp/json, so concurrent
    runs must not overlap.
    """

    def __init__(self, store: ProjectStore):
        self.store = store
        self.executor = ThreadPoolExecutor(max_workers=1)
        self._lock = threading.Lock()

    def _update_task(
        self,
        project_id: str,
        kind: TaskKind,
        **fields: object,
    ) -> Optional[Project]:
        with self._lock:
            project = self.store.get(project_id)
            if project is None:
                return None
            task = project.tasks.get(kind, TaskState())
            project.tasks[kind] = task.model_copy(update=fields)
            self.store.save(project)
            return project

    def submit(
        self,
        project_id: str,
        kind: TaskKind,
        job: Callable[[Project, Callable[[str, float], None]], None],
    ) -> TaskState:
        """Queue a job. `job(project, on_progress)` runs on the worker."""
        project = self._update_task(
            project_id,
            kind,
            status="running",
            stage="queued",
            progress=0.0,
            error=None,
            started_at=_now(),
            finished_at=None,
        )
        if project is None:
            raise KeyError(f"Project not found: {project_id}")

        def on_progress(stage: str, progress: float) -> None:
            self._update_task(project_id, kind, stage=stage, progress=progress)

        def run() -> None:
            # Re-read the project on the worker so queued jobs see fresh state
            current = self.store.get(project_id)
            if current is None:
                return
            try:
                job(current, on_progress)
                self._update_task(
                    project_id,
                    kind,
                    status="done",
                    stage="done",
                    progress=1.0,
                    finished_at=_now(),
                )
            except Exception as e:  # noqa: BLE001 - surfaced via task state
                self._update_task(
                    project_id,
                    kind,
                    status="error",
                    error=f"{type(e).__name__}: {e}",
                    finished_at=_now(),
                )

        self.executor.submit(run)
        return project.tasks[kind]

    def recover_stale_tasks(self) -> None:
        """Mark tasks left 'running' by a previous server process as errors."""
        for project in self.store.list():
            changed = False
            for kind, task in project.tasks.items():
                if task.status == "running":
                    project.tasks[kind] = task.model_copy(
                        update={
                            "status": "error",
                            "error": "server restarted",
                            "finished_at": _now(),
                        }
                    )
                    changed = True
            if changed:
                self.store.save(project)
