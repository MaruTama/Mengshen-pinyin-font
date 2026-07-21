# -*- coding: utf-8 -*-
"""Glyph browser endpoints: paged listing, detail, thumbnail SVG."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Response

from ..services import glyph_catalog
from ..services.preview_composer import get_pronunciations
from .deps import get_project_or_404, store

router = APIRouter(prefix="/api/projects/{project_id}", tags=["glyphs"])


@router.get("/glyphs")
def list_glyphs(
    project_id: str,
    q: str = "",
    category: str = "",
    page: int = Query(1, ge=1),
    size: int = Query(200, ge=1, le=1000),
) -> dict:
    project = get_project_or_404(project_id)
    if project.base_font is None:
        raise HTTPException(status_code=409, detail="No base font selected")
    entries = glyph_catalog.get_index(store, project)
    return glyph_catalog.search(entries, q, category, page, size)


@router.get("/glyphs/{name}")
def glyph_detail(project_id: str, name: str) -> dict:
    project = get_project_or_404(project_id)
    entries = glyph_catalog.get_index(store, project)
    entry = glyph_catalog.find_glyph(entries, name)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Glyph not found: {name}")

    readings = get_pronunciations(project, entry["char"]) if entry["char"] else []
    codepoints = [int(cp[2:], 16) for cp in entry["codepoints"]]
    tables = [
        {"id": table_id, "label": glyph_catalog.STANDARD_TABLE_LABELS[table_id]}
        for table_id in glyph_catalog.tables_for(codepoints)
    ]
    ivs = glyph_catalog.ivs_sequences(readings) if entry["category"] == "hanzi" else []
    return {**entry, "readings": readings, "tables": tables, "ivs": ivs}


@router.get("/ivs")
def list_ivs(
    project_id: str,
    q: str = "",
    homographs_only: bool = False,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=500),
) -> dict:
    """Planned IVS (cmap_uvs) assignments for the built font."""
    project = get_project_or_404(project_id)
    if project.base_font is None:
        raise HTTPException(status_code=409, detail="No base font selected")
    rows = glyph_catalog.ivs_index(store, project)
    return glyph_catalog.search_ivs(rows, q, homographs_only, page, size)


@router.get("/glyphs/{name}/svg")
def glyph_svg(project_id: str, name: str) -> Response:
    project = get_project_or_404(project_id)
    entries = glyph_catalog.get_index(store, project)
    entry = glyph_catalog.find_glyph(entries, name)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Glyph not found: {name}")

    svg = glyph_catalog.thumbnail_svg(project, entry)
    if svg is None:
        raise HTTPException(status_code=404, detail="No outline available")
    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={"Cache-Control": "max-age=3600"},
    )
