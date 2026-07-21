# -*- coding: utf-8 -*-
"""Health check and builtin font listing."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from fontTools.ttLib import TTFont

from .. import settings
from ..services.pipeline import BUILTIN_FONTS
from ..services.project_store import default_canvas


@lru_cache(maxsize=8)
def _family_info(path: str) -> tuple[Optional[str], bool]:
    """(family name, whether the font can render that whole name)."""
    from ..services.font_inspector import name_is_renderable

    font = TTFont(path, lazy=True)
    try:
        name = font["name"].getDebugName(1) or font["name"].getDebugName(4)
        renderable = bool(name) and name_is_renderable(font, name)
        return name, renderable
    finally:
        font.close()


router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/health")
def health() -> dict:
    missing = settings.missing_tools()
    return {
        "status": "ok" if not missing else "degraded",
        "missing_tools": missing,
    }


@router.get("/builtin-fonts")
def builtin_fonts() -> dict:
    fonts = {}
    for style, info in BUILTIN_FONTS.items():
        base_family, base_renderable = _family_info(str(info["base_path"]))
        pinyin_family, pinyin_renderable = _family_info(str(info["pinyin_path"]))
        fonts[style] = {
            "style": style,
            "label": info["label"],
            "base_path": str(info["base_path"]),
            "pinyin_path": str(info["pinyin_path"]),
            # Actual family names per role (the pinyin font is a
            # different typeface than the preset's base font)
            "base_family": base_family,
            "pinyin_family": pinyin_family,
            # Whether each font can render its own name (pinyin subsets
            # often cannot — uppercase/punctuation missing)
            "base_name_renderable": base_renderable,
            "pinyin_name_renderable": pinyin_renderable,
            "default_canvas": default_canvas(style).model_dump(),
        }
    return {"fonts": fonts}


@router.get("/builtin-fonts/{style}/{role}/file")
def builtin_font_file(style: str, role: Literal["base", "pinyin"]) -> FileResponse:
    """Serve a bundled font binary (for in-browser name preview)."""
    if style not in BUILTIN_FONTS:
        raise HTTPException(status_code=404, detail=f"Unknown style: {style}")
    key = "base_path" if role == "base" else "pinyin_path"
    path = Path(str(BUILTIN_FONTS[style][key]))
    if not path.exists():
        raise HTTPException(status_code=404, detail="Bundled font missing")
    return FileResponse(
        path,
        media_type="font/ttf",
        headers={"Cache-Control": "max-age=86400"},
    )
