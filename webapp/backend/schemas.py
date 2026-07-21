# -*- coding: utf-8 -*-
"""Pydantic models for the webapp project state (persisted as tmp/ JSON)."""

from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field

SCHEMA_VERSION = 1

Step = Literal["fonts", "license", "adjust", "glyphs", "duoyinzi", "readings", "build"]
FontRole = Literal["base", "pinyin"]
TaskKind = Literal["prepare", "build"]
TaskStatus = Literal["idle", "running", "done", "error"]


class PinyinCanvasModel(BaseModel):
    width: float
    height: float
    base_line: float
    tracking: float


class HanziCanvasModel(BaseModel):
    width: float = 1000.0
    height: float = 1000.0


class CanvasModel(BaseModel):
    pinyin: PinyinCanvasModel
    hanzi: HanziCanvasModel = HanziCanvasModel()
    is_avoid_overlapping_mode: bool = False
    x_scale_reduction_for_avoid_overlapping: float = 0.1


class FontRef(BaseModel):
    source: str  # "upload" | "builtin:han_serif" | "builtin:handwritten"
    path: str
    original_filename: str
    sha256: str
    family_name: str = ""
    units_per_em: int = 1000
    glyph_count: int = 0
    # False when the font lacks glyphs for some characters of its own
    # family name (e.g. lowercase-only pinyin subset fonts)
    name_renderable: bool = True


class LicenseEntry(BaseModel):
    name_id: int
    label: str = ""
    value: str


class LicenseInfo(BaseModel):
    entries: List[LicenseEntry] = Field(default_factory=list)
    acknowledged: bool = False
    acknowledged_at: Optional[str] = None
    font_sha256: Optional[str] = None


class ReadingOverride(BaseModel):
    mode: Literal["replace", "append"] = "replace"
    pronunciations: List[str]


class GlyphOverrides(BaseModel):
    readings: Dict[str, ReadingOverride] = Field(default_factory=dict)
    excluded_characters: List[str] = Field(default_factory=list)


class OutputSettings(BaseModel):
    family_name: str = "Mengshen-Custom"
    style_name: str = "Regular"
    version: str = "1.0"


class TaskState(BaseModel):
    status: TaskStatus = "idle"
    stage: Optional[str] = None
    progress: float = 0.0
    error: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None


class Project(BaseModel):
    schema_version: int = SCHEMA_VERSION
    id: str
    name: str
    created_at: str
    updated_at: str
    step: Step = "fonts"
    base_font: Optional[FontRef] = None
    pinyin_font: Optional[FontRef] = None
    license: Dict[str, LicenseInfo] = Field(
        default_factory=lambda: {"base": LicenseInfo(), "pinyin": LicenseInfo()}
    )
    canvas: CanvasModel
    glyph_overrides: GlyphOverrides = Field(default_factory=GlyphOverrides)
    output: OutputSettings = Field(default_factory=OutputSettings)
    artifacts: Dict[str, str] = Field(default_factory=dict)
    tasks: Dict[str, TaskState] = Field(
        default_factory=lambda: {"prepare": TaskState(), "build": TaskState()}
    )


# ---- request/response payloads ----


class ProjectCreateRequest(BaseModel):
    name: str = "Untitled Font"


class ProjectPatchRequest(BaseModel):
    name: Optional[str] = None
    step: Optional[Step] = None
    canvas: Optional[CanvasModel] = None
    output: Optional[OutputSettings] = None


class BuiltinSelectRequest(BaseModel):
    style: Literal["han_serif", "handwritten"]


class LicenseAcknowledgeRequest(BaseModel):
    role: FontRole
    acknowledged: bool


class PreviewRequest(BaseModel):
    text: str = "你好中国装"
    canvas: Optional[CanvasModel] = None


class PreviewItem(BaseModel):
    char: str
    pinyin: str
    svg: str


class PreviewResponse(BaseModel):
    items: List[PreviewItem]
    warnings: List[str] = Field(default_factory=list)


class PreviewDetailRequest(BaseModel):
    char: str
    canvas: Optional[CanvasModel] = None


class OutlineGlyph(BaseModel):
    glyph: str
    path: str
    advance_width: float
    # Placement transform relative to the hanzi origin; identity for the
    # hanzi glyph itself, real 2x2 scale+translate for pinyin letters.
    a: float = 1.0
    d: float = 1.0
    x: float = 0.0
    y: float = 0.0
    label: Optional[str] = None


class PreviewDetail(BaseModel):
    char: str
    pinyin: str
    hanzi: OutlineGlyph
    pinyin_glyphs: List[OutlineGlyph]
    upem: int
    hanzi_width: float
    hanzi_height: float
    total_height: float
    descent: float
    base_line: float
    pinyin_width: float
    pinyin_height: float
    tracking: float
