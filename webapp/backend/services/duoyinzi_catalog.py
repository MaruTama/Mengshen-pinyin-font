# -*- coding: utf-8 -*-
"""Homograph (多音字) pattern index and GSUB (rclt) table viewer data.

The phrase pattern files under outputs/ are character-level data shared by
every project. The GSUB structure is produced by the production
GSUBTableGenerator against the project's prepared templates and cached
in memory per project.
"""

from __future__ import annotations

import json
import re
import threading
from typing import Dict, List, Optional

import orjson

from src.refactored.data import (
    CharacterDataManager,
    MappingDataManager,
    PinyinDataManager,
)
from src.refactored.data.mapping_data import JsonCmapDataSource
from src.refactored.tables.cmap_manager import CmapTableManager
from src.refactored.tables.gsub_table_generator import GSUBTableGenerator

from .. import settings
from ..schemas import Project
from .pipeline import template_paths_for

_PATTERN_ONE_LINE = re.compile(r"^\s*(\d+),\s*(\S+),\s*(\S+),\s*\[(.*)\]\s*$")

_lock = threading.Lock()
_duoyinzi_cache: Optional[List[dict]] = None
_gsub_cache: Dict[str, tuple[float, dict]] = {}


def _parse_pattern_one() -> Dict[str, List[dict]]:
    """char -> [{index, pinyin, phrases}] from duoyinzi_pattern_one.txt."""
    path = settings.PATHS.outputs_dir / "duoyinzi_pattern_one.txt"
    result: Dict[str, List[dict]] = {}
    if not path.exists():
        return result
    for line in path.read_text(encoding="utf-8").splitlines():
        match = _PATTERN_ONE_LINE.match(line)
        if not match:
            continue
        index, char, pinyin, phrases = match.groups()
        result.setdefault(char, []).append(
            {
                "index": int(index),
                "pinyin": pinyin,
                "phrases": [p for p in phrases.split("|") if p],
            }
        )
    return result


def _load_phrase_patterns(filename: str) -> Dict[str, dict]:
    path = settings.PATHS.outputs_dir / filename
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    patterns = data.get("patterns", {})
    return patterns if isinstance(patterns, dict) else {}


def build_duoyinzi_index() -> List[dict]:
    """One row per homograph character with readings and phrase contexts."""
    global _duoyinzi_cache
    with _lock:
        if _duoyinzi_cache is not None:
            return _duoyinzi_cache

        pattern_one = _parse_pattern_one()
        pattern_two = _load_phrase_patterns("duoyinzi_pattern_two.json")
        exceptional = _load_phrase_patterns("duoyinzi_exceptional_pattern.json")
        pinyin_data = PinyinDataManager()

        chars = set(pattern_one)
        for phrase in list(pattern_two) + list(exceptional):
            chars.update(c for c in phrase if not c.isascii())

        rows = []
        for char in sorted(chars):
            readings = pinyin_data.get_pinyin(char) or []
            if not readings and char not in pattern_one:
                continue
            rows.append(
                {
                    "char": char,
                    "readings": readings,
                    "pattern_one": pattern_one.get(char, []),
                    "pattern_two_phrases": [p for p in pattern_two if char in p],
                    "exceptional_phrases": [p for p in exceptional if char in p],
                }
            )
        _duoyinzi_cache = rows
        return rows


def search_duoyinzi(query: str = "", page: int = 1, size: int = 50) -> dict:
    rows = build_duoyinzi_index()
    if query:
        q = query.strip()
        rows = [
            r
            for r in rows
            if q == r["char"]
            or any(q in reading for reading in r["readings"])
            or any(
                q in phrase for entry in r["pattern_one"] for phrase in entry["phrases"]
            )
        ]
    total = len(rows)
    start = max(page - 1, 0) * size
    return {
        "total": total,
        "page": page,
        "size": size,
        "items": rows[start : start + size],
    }


def find_duoyinzi(char: str) -> Optional[dict]:
    for row in build_duoyinzi_index():
        if row["char"] == char:
            return row
    return None


def duoyinzi_detail(char: str) -> Optional[dict]:
    """Index row plus expanded phrase-pattern structure for visualization."""
    row = find_duoyinzi(char)
    if row is None:
        return None

    def expand(patterns: Dict[str, dict]) -> List[dict]:
        expanded = []
        for phrase, spec in patterns.items():
            if char not in phrase or not isinstance(spec, dict):
                continue
            sequence = []
            for step in spec.get("pattern", []):
                for step_char, lookup in step.items():
                    sequence.append({"char": step_char, "lookup": lookup})
            expanded.append(
                {
                    "phrase": phrase,
                    "ignore": spec.get("ignore"),
                    "sequence": sequence,
                }
            )
        return expanded

    return {
        **row,
        "pattern_two_detail": expand(
            _load_phrase_patterns("duoyinzi_pattern_two.json")
        ),
        "exceptional_detail": expand(
            _load_phrase_patterns("duoyinzi_exceptional_pattern.json")
        ),
    }


def _generate_gsub(project: Project) -> dict:
    templates = template_paths_for(project)
    template_main = templates["template_main"]
    if not template_main.exists():
        raise FileNotFoundError(
            "Templates not prepared yet — run prepare before viewing GSUB"
        )

    outputs_dir = settings.PATHS.outputs_dir
    cmap_manager = CmapTableManager.from_path(str(template_main))
    pinyin_manager = PinyinDataManager()
    character_manager = CharacterDataManager(pinyin_manager)
    mapping_manager = MappingDataManager(
        cmap_source=JsonCmapDataSource(template_main), paths=settings.PATHS
    )
    generator = GSUBTableGenerator(
        pattern_one_path=outputs_dir / "duoyinzi_pattern_one.txt",
        pattern_two_path=outputs_dir / "duoyinzi_pattern_two.json",
        exception_pattern_path=outputs_dir / "duoyinzi_exceptional_pattern.json",
        character_manager=character_manager,
        mapping_manager=mapping_manager,
        cmap_table=cmap_manager.get_cmap_table(),
    )
    table = generator.generate_gsub_table()
    # orjson round-trip drops any non-JSON types up front
    return orjson.loads(orjson.dumps(table))


def get_gsub(project: Project) -> dict:
    """Generate (or reuse) the GSUB table for the project's templates."""
    template_main = template_paths_for(project)["template_main"]
    mtime = template_main.stat().st_mtime if template_main.exists() else 0.0
    with _lock:
        cached = _gsub_cache.get(project.id)
        if cached is not None and cached[0] == mtime:
            return cached[1]
    table = _generate_gsub(project)
    with _lock:
        _gsub_cache[project.id] = (mtime, table)
    return table


def gsub_overview(table: dict) -> dict:
    """Structure summary: languages -> features -> lookups with rule counts."""
    lookups = table.get("lookups", {})
    lookup_meta = {
        name: {
            "type": lookup.get("type"),
            "rule_count": len(lookup.get("subtables", [])),
        }
        for name, lookup in lookups.items()
    }
    return {
        "languages": table.get("languages", {}),
        "features": table.get("features", {}),
        "lookups": lookup_meta,
        "lookup_order": table.get("lookupOrder", []),
    }


def lookup_rules(
    table: dict, lookup_name: str, query: str = "", page: int = 1, size: int = 100
) -> dict:
    lookups = table.get("lookups", {})
    if lookup_name not in lookups:
        raise KeyError(f"Lookup not found: {lookup_name}")
    lookup = lookups[lookup_name]
    subtables = lookup.get("subtables", [])
    if query:
        q = query.strip()
        subtables = [s for s in subtables if q in json.dumps(s, ensure_ascii=False)]
    total = len(subtables)
    start = max(page - 1, 0) * size
    return {
        "lookup": lookup_name,
        "type": lookup.get("type"),
        "total": total,
        "page": page,
        "size": size,
        "rules": subtables[start : start + size],
    }
