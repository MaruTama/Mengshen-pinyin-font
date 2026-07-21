# -*- coding: utf-8 -*-
"""Project CRUD, builtin font selection, and license acknowledgment."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import FileResponse

from src.refactored.scripts.retrieve_latin_alphabet import ALPHABET

from ..errors import FontValidationError, problem
from ..schemas import (
    BuiltinSelectRequest,
    FontRole,
    LicenseAcknowledgeRequest,
    LicenseInfo,
    Project,
    ProjectCreateRequest,
    ProjectPatchRequest,
    TaskState,
)
from ..services import font_inspector
from ..services.pipeline import BUILTIN_FONTS
from ..services.project_store import default_canvas
from .deps import get_project_or_404, store

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("", status_code=201)
def create_project(body: ProjectCreateRequest) -> Project:
    return store.create(body.name)


@router.get("")
def list_projects() -> list[Project]:
    return store.list()


@router.get("/{project_id}")
def get_project(project_id: str) -> Project:
    return get_project_or_404(project_id)


@router.patch("/{project_id}")
def patch_project(project_id: str, body: ProjectPatchRequest) -> Project:
    project = get_project_or_404(project_id)
    if body.name is not None:
        project.name = body.name
    if body.step is not None:
        project.step = body.step
    if body.canvas is not None and body.canvas != project.canvas:
        project.canvas = body.canvas
        invalidate_build(project)
    if body.output is not None and body.output != project.output:
        project.output = body.output
        invalidate_build(project)
    return store.save(project)


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: str) -> None:
    if not store.delete(project_id):
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")


@router.get("/{project_id}/storage")
def project_storage(project_id: str) -> dict:
    """Everything stored for this project, grouped for the UI."""
    from .. import settings

    get_project_or_404(project_id)
    root = settings.PATHS.project_root

    def entries(paths: list[Path]) -> list[dict]:
        rows = []
        for path in sorted(paths):
            if path.is_file():
                rows.append(
                    {
                        "name": path.name,
                        "path": str(path.relative_to(root)),
                        "size": path.stat().st_size,
                    }
                )
        return rows

    project_dir = store.project_dir(project_id)
    groups = {
        "state": entries([project_dir / "project.json"]),
        "fonts": entries(list(store.fonts_dir(project_id).glob("*"))),
        "intermediate": entries(
            list(store.json_dir(project_id).glob("*.json"))
            + [project_dir / "glyph_index.json"]
            # Templates from before per-project consolidation
            + list(settings.JSON_TEMP_DIR.glob(f"*_proj_{project_id}.json"))
        ),
        "output": entries(list((settings.OUTPUTS_DIR / project_id).glob("*"))),
    }
    total = sum(row["size"] for rows in groups.values() for row in rows)
    return {"groups": groups, "total": total}


def invalidate_build(project: Project) -> None:
    """A previously built TTF no longer reflects the project settings."""
    if project.tasks["build"].status != "idle":
        project.tasks["build"] = TaskState()


def _set_font(project: Project, role: FontRole, path: Path, source: str) -> Project:
    """Attach a font to the project and refresh its license state."""
    font_ref = font_inspector.inspect_font(path, source, path.name)
    entries = font_inspector.read_license_entries(path)

    if role == "base":
        project.base_font = font_ref
    else:
        project.pinyin_font = font_ref

    # Changing a font always invalidates its previous acknowledgment
    project.license[role] = LicenseInfo(
        entries=entries,
        acknowledged=False,
        font_sha256=font_ref.sha256,
    )

    # Templates prepared for the previous font are stale now, and so is
    # any TTF built from them
    project.tasks["prepare"] = project.tasks["prepare"].model_copy(
        update={"status": "idle", "stage": None, "progress": 0.0, "error": None}
    )
    invalidate_build(project)
    return project


@router.get("/{project_id}/fonts/{role}/file")
def font_file(project_id: str, role: FontRole) -> FileResponse:
    """Serve the selected font binary (for in-browser name preview)."""
    project = get_project_or_404(project_id)
    font_ref = project.base_font if role == "base" else project.pinyin_font
    if font_ref is None:
        raise HTTPException(status_code=404, detail=f"No {role} font selected")
    path = Path(font_ref.path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Font file missing")
    return FileResponse(
        path,
        media_type="font/ttf" if path.suffix == ".ttf" else "font/otf",
        headers={"Cache-Control": "max-age=3600", "ETag": f'"{font_ref.sha256}"'},
    )


@router.post("/{project_id}/fonts/{role}")
async def upload_font(project_id: str, role: FontRole, file: UploadFile) -> Project:
    project = get_project_or_404(project_id)

    filename = file.filename or "font.ttf"
    suffix = Path(filename).suffix.lower()
    if suffix not in (".ttf", ".otf"):
        raise problem(422, "only_ttf_otf", "Only .ttf / .otf are supported")

    fonts_dir = store.fonts_dir(project_id)
    fonts_dir.mkdir(parents=True, exist_ok=True)
    target = fonts_dir / f"{role}{suffix}"
    target.write_bytes(await file.read())

    try:
        font_inspector.validate_font_file(target)
        if role == "pinyin":
            missing = font_inspector.pinyin_coverage(target, ALPHABET)
            if missing:
                glyphs = " ".join(missing[:20]) + (" …" if len(missing) > 20 else "")
                raise FontValidationError(
                    "pinyin_missing_glyphs",
                    f"Pinyin font is missing required glyphs: {glyphs}",
                    glyphs=glyphs,
                )
            target = font_inspector.normalize_pinyin_font(target, ALPHABET)
    except FontValidationError as e:
        target.unlink(missing_ok=True)
        raise problem(422, e.code, e.message, **e.params)

    project = _set_font(project, role, target, "upload")
    font_ref = project.base_font if role == "base" else project.pinyin_font
    if font_ref is not None:
        font_ref.original_filename = filename
    return store.save(project)


@router.put("/{project_id}/fonts/{role}/builtin")
def select_builtin_font(
    project_id: str, role: FontRole, body: BuiltinSelectRequest
) -> Project:
    project = get_project_or_404(project_id)
    info = BUILTIN_FONTS[body.style]
    path_key = "base_path" if role == "base" else "pinyin_path"
    path = Path(str(info[path_key]))
    if not path.exists():
        raise HTTPException(status_code=500, detail=f"Bundled font missing: {path}")

    project = _set_font(project, role, path, f"builtin:{body.style}")

    # Selecting a builtin base font seeds its tuned canvas defaults
    if role == "base":
        project.canvas = default_canvas(body.style)

    return store.save(project)


@router.post("/{project_id}/license/acknowledge")
def acknowledge_license(project_id: str, body: LicenseAcknowledgeRequest) -> Project:
    project = get_project_or_404(project_id)
    font_ref = project.base_font if body.role == "base" else project.pinyin_font
    if font_ref is None:
        raise problem(
            409, "no_font_selected", f"No {body.role} font selected", role=body.role
        )

    info = project.license[body.role]
    info.acknowledged = body.acknowledged
    info.acknowledged_at = (
        datetime.now(timezone.utc).isoformat(timespec="seconds")
        if body.acknowledged
        else None
    )
    info.font_sha256 = font_ref.sha256
    return store.save(project)
