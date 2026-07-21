# -*- coding: utf-8 -*-
"""Homograph list and GSUB (rclt) table endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..errors import problem
from ..services import duoyinzi_catalog, glyph_catalog, gsub_checker
from ..services.preview_composer import get_pronunciations
from .deps import get_project_or_404, store

router = APIRouter(prefix="/api/projects/{project_id}", tags=["duoyinzi"])


@router.get("/duoyinzi")
def list_duoyinzi(
    project_id: str,
    q: str = "",
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=500),
) -> dict:
    get_project_or_404(project_id)
    return duoyinzi_catalog.search_duoyinzi(q, page, size)


@router.get("/duoyinzi/{char}")
def duoyinzi_detail(project_id: str, char: str) -> dict:
    get_project_or_404(project_id)
    row = duoyinzi_catalog.duoyinzi_detail(char)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Not a known homograph: {char}")
    return row


@router.get("/gsub")
def gsub_overview(project_id: str) -> dict:
    project = get_project_or_404(project_id)
    try:
        table = duoyinzi_catalog.get_gsub(project)
    except FileNotFoundError as e:
        raise problem(409, "prepare_incomplete", str(e))
    return duoyinzi_catalog.gsub_overview(table)


class SimulateRequest(BaseModel):
    text: str


# NOTE: these fixed /gsub/* routes must be declared before /gsub/{lookup_name}


@router.get("/gsub/verify")
def gsub_verify(project_id: str) -> dict:
    """Simulate every phrase from the res/phonics tables through the
    generated GSUB and report ok / fallback / wrong per character."""
    project = get_project_or_404(project_id)
    try:
        table = duoyinzi_catalog.get_gsub(project)
        char_to_glyph, glyph_to_char = gsub_checker.char_glyph_maps(project)
    except FileNotFoundError as e:
        raise problem(409, "prepare_incomplete", str(e))
    cases = gsub_checker.parse_expected_phrases()
    return gsub_checker.verify_phrases(
        table,
        cases,
        char_to_glyph,
        glyph_to_char,
        lambda c: get_pronunciations(project, c),
    )


@router.post("/gsub/simulate")
def gsub_simulate(project_id: str, body: SimulateRequest) -> dict:
    """Apply the rclt lookups to arbitrary text (e.g. 背着手) and show the
    resulting reading and fired rules per character."""
    project = get_project_or_404(project_id)
    text = body.text.strip()
    if not text or len(text) > 50:
        raise HTTPException(status_code=422, detail="Text must be 1-50 characters")
    try:
        table = duoyinzi_catalog.get_gsub(project)
        char_to_glyph, glyph_to_char = gsub_checker.char_glyph_maps(project)
    except FileNotFoundError as e:
        raise problem(409, "prepare_incomplete", str(e))
    rows = gsub_checker.simulate(
        table,
        text,
        char_to_glyph,
        glyph_to_char,
        lambda c: get_pronunciations(project, c),
    )
    return {"text": text, "chars": rows}


@router.get("/gsub/graph/{char}")
def gsub_graph(project_id: str, char: str) -> dict:
    """All rclt rules involving one character, shaped for the graph view."""
    project = get_project_or_404(project_id)
    if len(char) != 1:
        raise HTTPException(status_code=422, detail="Specify exactly one character")
    try:
        table = duoyinzi_catalog.get_gsub(project)
        char_to_glyph, glyph_to_char = gsub_checker.char_glyph_maps(project)
    except FileNotFoundError as e:
        raise problem(409, "prepare_incomplete", str(e))
    return gsub_checker.char_rule_graph(
        table, char, char_to_glyph, glyph_to_char, get_pronunciations(project, char)
    )


@router.get("/gsub/{lookup_name}")
def gsub_lookup_rules(
    project_id: str,
    lookup_name: str,
    q: str = "",
    page: int = Query(1, ge=1),
    size: int = Query(100, ge=1, le=500),
) -> dict:
    project = get_project_or_404(project_id)
    try:
        table = duoyinzi_catalog.get_gsub(project)

        # Allow searching by character: rules reference raw glyph names
        glyph_index = glyph_catalog.get_index(store, project)
        if q and len(q) == 1 and not q.isascii():
            names = [e["name"] for e in glyph_index if e["char"] == q]
            q = names[0] if names else q

        result = duoyinzi_catalog.lookup_rules(table, lookup_name, q, page, size)

        # name -> char map for the glyphs on this page (UI readability)
        page_names: set[str] = set()
        for rule in result["rules"]:
            for group in rule.get("match", []):
                page_names.update(group)
            if isinstance(rule.get("to"), list):
                page_names.update(str(g) for g in rule["to"])
        result["glyph_chars"] = {
            e["name"]: e["char"]
            for e in glyph_index
            if e["name"] in page_names and e["char"]
        }
        return result
    except FileNotFoundError as e:
        raise problem(409, "prepare_incomplete", str(e))
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
