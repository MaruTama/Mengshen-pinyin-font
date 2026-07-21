# -*- coding: utf-8 -*-
"""Wrappers around the existing font pipeline for webapp projects."""

from __future__ import annotations

import logging
import re
import shutil
from pathlib import Path
from typing import Callable, Optional

from src.refactored.config.font_config import (
    FontConstants,
    FontMetadata,
    FontType,
    HanziCanvas,
    PinyinCanvas,
)
from src.refactored.config.paths import ProjectPaths
from src.refactored.data import PinyinDataManager
from src.refactored.generation.font_builder import FontBuilder
from src.refactored.scripts.make_template_jsons import TemplateJsonMaker
from src.refactored.scripts.retrieve_latin_alphabet import LatinAlphabetRetriever

from .. import settings
from ..schemas import Project

ProgressCallback = Callable[[str, float], None]

BUILTIN_FONTS = {
    "han_serif": {
        "label": "Source Han Serif (宋体)",
        "font_type": FontType.HAN_SERIF,
        "base_path": FontConstants.HAN_SERIF_FONT_PATH,
        "pinyin_path": FontConstants.HAN_SERIF_ALPHABET_FONT_PATH,
    },
    "handwritten": {
        "label": "Xiaolai (手写体)",
        "font_type": FontType.HANDWRITTEN,
        "base_path": FontConstants.HANDWRITTEN_FONT_PATH,
        "pinyin_path": FontConstants.HANDWRITTEN_ALPHABET_FONT_PATH,
    },
}

# Build progress mapped from FontBuilder's INFO log messages
_BUILD_STAGES = [
    ("Loading font templates", "load_templates", 0.05),
    ("Initializing managers", "init_managers", 0.15),
    ("Adding cmap_uvs table", "cmap_uvs", 0.25),
    ("Adding glyph_order table", "glyph_order", 0.30),
    ("Adding glyf table", "glyf", 0.35),
    ("Adding GSUB table", "gsub", 0.70),
    ("Setting font metadata", "metadata", 0.80),
    ("Saving and converting font", "otfccbuild", 0.85),
    ("Font build completed successfully", "done", 1.0),
]


def style_for(project: Project) -> str:
    return f"proj_{project.id}"


def font_metadata_from_project(project: Project) -> FontMetadata:
    canvas = project.canvas
    return FontMetadata(
        pinyin_canvas=PinyinCanvas(
            width=canvas.pinyin.width,
            height=canvas.pinyin.height,
            base_line=canvas.pinyin.base_line,
            tracking=canvas.pinyin.tracking,
        ),
        hanzi_canvas=HanziCanvas(
            width=canvas.hanzi.width,
            height=canvas.hanzi.height,
        ),
        is_avoid_overlapping_mode=canvas.is_avoid_overlapping_mode,
        x_scale_reduction_for_avoid_overlapping=(
            canvas.x_scale_reduction_for_avoid_overlapping
        ),
    )


def font_type_for(project: Project) -> FontType:
    if project.base_font and project.base_font.source.startswith("builtin:"):
        return FontType(project.base_font.source.split(":", 1)[1])
    return FontType.CUSTOM


def project_json_dir(project: Project) -> Path:
    return settings.PROJECTS_DIR / project.id / "json"


def _legacy_template_paths(project: Project) -> dict[str, Path]:
    """Pre-consolidation locations in the shared tmp/json/ directory."""
    style = style_for(project)
    json_dir = settings.JSON_TEMP_DIR
    return {
        "template_main": json_dir / f"template_main_{style}.json",
        "template_glyf": json_dir / f"template_glyf_{style}.json",
        "alphabet_pinyin": json_dir / f"alphabet_for_pinyin_{style}.json",
    }


def template_paths_for(project: Project) -> dict[str, Path]:
    """Per-project template locations, falling back to legacy files."""
    json_dir = project_json_dir(project)
    paths = {
        "template_main": json_dir / "template_main.json",
        "template_glyf": json_dir / "template_glyf.json",
        "alphabet_pinyin": json_dir / "alphabet_for_pinyin.json",
    }
    legacy = _legacy_template_paths(project)
    return {
        name: path if path.exists() or not legacy[name].exists() else legacy[name]
        for name, path in paths.items()
    }


class ProjectScopedPaths(ProjectPaths):
    """ProjectPaths whose temp JSONs live inside the project directory.

    Keeps FontBuilder's intermediate template_output.json (hundreds of
    MB) per project instead of a shared tmp/json file.
    """

    def __init__(self, project: Project):
        super().__init__()
        self._project_json_dir = project_json_dir(project)

    @property
    def json_temp_dir(self) -> Path:
        return self._project_json_dir

    def get_temp_json_path(self, filename: str) -> Path:
        self._project_json_dir.mkdir(parents=True, exist_ok=True)
        return self._project_json_dir / filename


def output_path_for(project: Project) -> Path:
    filename = f"{sanitize_family_name(project.output.family_name)}.ttf"
    return settings.OUTPUTS_DIR / project.id / filename


class _ProgressLogHandler(logging.Handler):
    """Maps FontBuilder INFO messages to coarse progress fractions."""

    def __init__(self, on_progress: ProgressCallback):
        super().__init__(level=logging.INFO)
        self.on_progress = on_progress

    def emit(self, record: logging.LogRecord) -> None:
        message = record.getMessage()
        for prefix, stage, fraction in _BUILD_STAGES:
            if message.startswith(prefix):
                self.on_progress(stage, fraction)
                return


def run_prepare(project: Project, on_progress: ProgressCallback) -> dict[str, str]:
    """Extract alphabet glyphs and build template JSONs for the project.

    Returns the artifact paths (relative to the project root).
    """
    if project.base_font is None or project.pinyin_font is None:
        raise ValueError("Both base and pinyin fonts must be selected")

    style = style_for(project)
    settings.ensure_directories()

    on_progress("alphabet", 0.05)
    LatinAlphabetRetriever().retrieve_alphabet(project.pinyin_font.path, style)

    # otfccdump of the base font dominates prepare time
    on_progress("otfccdump", 0.25)
    TemplateJsonMaker().make_template(project.base_font.path, style)

    # The generator scripts write into the shared tmp/json/; consolidate
    # everything under tmp/projects/<id>/json/ so a project is
    # self-contained (deleting it removes all its intermediates)
    on_progress("consolidate", 0.95)
    json_dir = project_json_dir(project)
    json_dir.mkdir(parents=True, exist_ok=True)
    legacy = _legacy_template_paths(project)
    targets = {
        "template_main": json_dir / "template_main.json",
        "template_glyf": json_dir / "template_glyf.json",
        "alphabet_pinyin": json_dir / "alphabet_for_pinyin.json",
    }
    for name, source in legacy.items():
        if source.exists():
            shutil.move(str(source), str(targets[name]))

    on_progress("done", 1.0)
    root = settings.PATHS.project_root
    return {name: str(path.relative_to(root)) for name, path in targets.items()}


def run_build(
    project: Project,
    on_progress: ProgressCallback,
    pinyin_manager: Optional[PinyinDataManager] = None,
) -> Path:
    """Run the full font build for the project. Returns the output TTF path."""
    font_type = font_type_for(project)
    font_config = font_metadata_from_project(project)
    templates = template_paths_for(project)

    missing = [str(p) for p in templates.values() if not p.exists()]
    if missing:
        raise FileNotFoundError(
            f"Templates not prepared (run prepare first): {missing}"
        )

    name_table = None
    if font_type == FontType.CUSTOM:
        from .name_table_builder import build_name_table

        name_table = build_name_table(project)

    output_path = output_path_for(project)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    outputs_dir = settings.PATHS.outputs_dir
    builder_paths = ProjectScopedPaths(project)
    builder = FontBuilder(
        font_type=font_type,
        template_main_path=templates["template_main"],
        template_glyf_path=templates["template_glyf"],
        alphabet_pinyin_path=templates["alphabet_pinyin"],
        pattern_one_path=outputs_dir / "duoyinzi_pattern_one.txt",
        pattern_two_path=outputs_dir / "duoyinzi_pattern_two.json",
        exception_pattern_path=outputs_dir / "duoyinzi_exceptional_pattern.json",
        pinyin_manager=pinyin_manager,
        paths=builder_paths,
        font_config=font_config,
        name_table=name_table,
    )

    handler = _ProgressLogHandler(on_progress)
    builder_logger = logging.getLogger("mengshen.font_builder")
    builder_logger.addHandler(handler)
    try:
        builder.build(output_path)
    finally:
        builder_logger.removeHandler(handler)

    return output_path


def sanitize_family_name(name: str) -> str:
    """PostScript-safe family name for filenames and name table."""
    return re.sub(r"[^A-Za-z0-9-]", "", name.replace(" ", "-")) or "Mengshen-Custom"
