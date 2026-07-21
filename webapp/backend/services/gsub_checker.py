# -*- coding: utf-8 -*-
"""GSUB (rclt) simulation and phrase verification.

Simulates how an OpenType shaper applies the generated rclt chaining
lookups to a hanzi string (first-match-wins per position, ``apply: []``
rules acting as *ignore* exceptions), then maps the resulting glyphs back
to pinyin readings via the ``.ssNN`` convention (ss01 = readings[0]).

The expected readings come from the hand-maintained phrase tables under
res/phonics/duo_yin_zi/ — the same sources scripts/validate_phrase.py
checks statically. This module goes one step further: it verifies that
the *generated GSUB table* actually produces those readings, catching
mismatches such as stale ss indices after the pinyin mapping table
changed (e.g. 着手 must substitute to the zhuó variant, and the ignore
rule must keep 背着手 from triggering it).
"""

from __future__ import annotations

import re
import threading
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from .. import settings
from ..schemas import Project

_SS_SUFFIX = re.compile(r"\.ss(\d{2})$")

_lock = threading.Lock()
_cmap_cache: Dict[str, tuple[float, Dict[str, str], Dict[str, str]]] = {}


# ---- glyph <-> char mapping (same cmap the GSUB generator used) ----


def char_glyph_maps(project: Project) -> Tuple[Dict[str, str], Dict[str, str]]:
    """(char -> glyph name, glyph name -> char) from the project template."""
    from src.refactored.tables.cmap_manager import CmapTableManager

    from .pipeline import template_paths_for

    template_main = template_paths_for(project)["template_main"]
    if not template_main.exists():
        raise FileNotFoundError(
            "Templates not prepared yet — run prepare before GSUB checks"
        )
    mtime = template_main.stat().st_mtime
    with _lock:
        cached = _cmap_cache.get(project.id)
        if cached is not None and cached[0] == mtime:
            return cached[1], cached[2]

    cmap = CmapTableManager.from_path(str(template_main)).get_cmap_table()
    char_to_glyph: Dict[str, str] = {}
    glyph_to_char: Dict[str, str] = {}
    for code, glyph in cmap.items():
        try:
            char = chr(int(code))
        except (ValueError, OverflowError):
            continue
        char_to_glyph[char] = glyph
        glyph_to_char.setdefault(glyph, char)
    with _lock:
        _cmap_cache[project.id] = (mtime, char_to_glyph, glyph_to_char)
    return char_to_glyph, glyph_to_char


# ---- shaper simulation ----


def _rclt_lookups(table: dict) -> List[str]:
    """rclt chaining lookups in application (LookupList) order."""
    lookups = table.get("lookups", {})
    order = table.get("lookupOrder") or sorted(lookups)
    return [
        name
        for name in order
        if name.startswith("lookup_rclt")
        and lookups.get(name, {}).get("type") == "gsub_chaining"
    ]


def _single_sub(table: dict, lookup_name: str) -> Dict[str, str]:
    lookup = table.get("lookups", {}).get(lookup_name, {})
    subtables = lookup.get("subtables") or [{}]
    return subtables[0] if isinstance(subtables[0], dict) else {}


def _rules_by_first_input(rules: List[dict]) -> Dict[str, List[tuple[int, dict]]]:
    """Index chaining rules by the first input glyph for fast matching."""
    indexed: Dict[str, List[tuple[int, dict]]] = {}
    for rule_index, rule in enumerate(rules):
        match = rule.get("match") or []
        input_begins = rule.get("inputBegins", 0)
        if input_begins >= len(match):
            continue
        for glyph in match[input_begins]:
            indexed.setdefault(glyph, []).append((rule_index, rule))
    return indexed


def _rule_matches(rule: dict, seq: List[Optional[str]], pos: int) -> bool:
    """Does the chaining rule match with its input sequence starting at pos?"""
    match = rule.get("match") or []
    input_begins = rule.get("inputBegins", 0)
    start = pos - input_begins  # sequence index of match[0]
    if start < 0 or start + len(match) > len(seq):
        return False
    for offset, group in enumerate(match):
        glyph = seq[start + offset]
        if glyph is None or glyph not in group:
            return False
    return True


def simulate(
    table: dict,
    text: str,
    char_to_glyph: Dict[str, str],
    glyph_to_char: Dict[str, str],
    readings_for: Callable[[str], List[str]],
) -> List[dict]:
    """Apply the rclt lookups to `text` and resolve final readings.

    Returns one row per character: original/final glyph, the reading the
    final glyph displays, the default reading, and which rules fired
    (ignore matches included, flagged with ``ignored: True``).
    """
    seq: List[Optional[str]] = [char_to_glyph.get(c) for c in text]
    applied: List[List[dict]] = [[] for _ in text]

    for lookup_name in _rclt_lookups(table):
        rules = table["lookups"][lookup_name].get("subtables") or []
        indexed = _rules_by_first_input(rules)
        pos = 0
        while pos < len(seq):
            glyph = seq[pos]
            candidates = indexed.get(glyph, []) if glyph is not None else []
            matched = None
            for rule_index, rule in candidates:
                if _rule_matches(rule, seq, pos):
                    matched = (rule_index, rule)
                    break
            if matched is None:
                pos += 1
                continue

            rule_index, rule = matched
            input_begins = rule.get("inputBegins", 0)
            input_ends = rule.get("inputEnds", input_begins + 1)
            input_len = max(input_ends - input_begins, 1)
            applications = rule.get("apply") or []

            if not applications:  # ignore rule: consume input, substitute nothing
                applied[pos].append(
                    {"lookup": lookup_name, "rule": rule_index, "ignored": True}
                )
            for application in applications:
                at = application.get("at", input_begins)
                target_pos = pos + (at - input_begins)
                if not 0 <= target_pos < len(seq):
                    continue
                sub = _single_sub(table, application.get("lookup", ""))
                before = seq[target_pos]
                after = sub.get(before or "")
                if after:
                    seq[target_pos] = after
                    applied[target_pos].append(
                        {
                            "lookup": lookup_name,
                            "rule": rule_index,
                            "sub_lookup": application.get("lookup"),
                            "from": before,
                            "to": after,
                        }
                    )
            pos += input_len

    rows = []
    for index, char in enumerate(text):
        original = char_to_glyph.get(char)
        final = seq[index]
        readings = readings_for(char)
        default = readings[0] if readings else None
        rows.append(
            {
                "char": char,
                "glyph": original,
                "final_glyph": final,
                "reading": _glyph_reading(final, readings),
                "default_reading": default,
                "applied": applied[index],
            }
        )
    return rows


def _glyph_reading(glyph: Optional[str], readings: List[str]) -> Optional[str]:
    """Reading displayed by a glyph: base = readings[0], .ssNN = readings[NN-1]."""
    if glyph is None:
        return None
    suffix = _SS_SUFFIX.search(glyph)
    if suffix is None:
        return readings[0] if readings else None
    number = int(suffix.group(1))
    if number == 0:
        return None  # ss00 = pinyin-less
    return readings[number - 1] if number - 1 < len(readings) else None


# ---- expected phrase readings from res/phonics sources ----


def _phrase_dir() -> Path:
    return settings.PATHS.resources_dir / "phonics" / "duo_yin_zi"


def parse_expected_phrases() -> List[dict]:
    """[{phrase, expected: [pinyin, ...], source}] from the phrase tables."""
    cases: List[dict] = []
    seen: set[str] = set()

    def add(phrase: str, pinyin: str, source: str) -> None:
        phrase = phrase.strip()
        expected = [p for p in pinyin.strip().split("/") if p]
        if not phrase or len(expected) != len(phrase) or phrase in seen:
            return
        seen.add(phrase)
        cases.append({"phrase": phrase, "expected": expected, "source": source})

    for source in ("pattern_one", "pattern_two"):
        path = _phrase_dir() / f"phrase_of_{source}.txt"
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if ": " not in line:
                continue
            phrase, _, pinyin = line.partition(": ")
            add(phrase, pinyin, source)

    exceptional = _phrase_dir() / "phrase_of_exceptional_pattern.txt"
    if exceptional.exists():
        # One line per family: "着手: zhuó/shǒu, 背着手: bèi/zhe/shǒu"
        for line in exceptional.read_text(encoding="utf-8").splitlines():
            for entry in line.split(","):
                if ": " not in entry:
                    continue
                phrase, _, pinyin = entry.partition(": ")
                add(phrase, pinyin, "exceptional")

    return cases


# ---- verification ----


def _classify(expected: str, actual: Optional[str], default: Optional[str]) -> str:
    """ok = matches expectation; fallback = default reading shown instead
    (no rule fired / intentionally ignored); wrong = a rule produced a
    different reading than expected."""
    if actual == expected:
        return "ok"
    if actual == default:
        return "fallback"
    return "wrong"


def verify_phrases(
    table: dict,
    cases: List[dict],
    char_to_glyph: Dict[str, str],
    glyph_to_char: Dict[str, str],
    readings_for: Callable[[str], List[str]],
) -> dict:
    """Simulate every expected phrase and classify each character."""
    results = []
    counts = {"ok": 0, "fallback": 0, "wrong": 0}
    for case in cases:
        rows = simulate(
            table, case["phrase"], char_to_glyph, glyph_to_char, readings_for
        )
        chars = []
        worst = "ok"
        for row, expected in zip(rows, case["expected"]):
            status = _classify(expected, row["reading"], row["default_reading"])
            chars.append(
                {
                    "char": row["char"],
                    "expected": expected,
                    "actual": row["reading"],
                    "default": row["default_reading"],
                    "status": status,
                    "final_glyph": row["final_glyph"],
                }
            )
            if status == "wrong":
                worst = "wrong"
            elif status == "fallback" and worst == "ok":
                worst = "fallback"
        counts[worst] += 1
        results.append(
            {
                "phrase": case["phrase"],
                "source": case["source"],
                "status": worst,
                "chars": chars,
            }
        )
    return {
        "total": len(results),
        "counts": counts,
        "results": results,
    }


# ---- per-character rule graph ----


def char_rule_graph(
    table: dict,
    char: str,
    char_to_glyph: Dict[str, str],
    glyph_to_char: Dict[str, str],
    readings: List[str],
) -> dict:
    """Every rclt rule involving `char` as substitution target, shaped for
    a context -> lookup -> reading graph."""
    glyph = char_to_glyph.get(char)
    rules_out: List[dict] = []
    if glyph is None:
        return {"char": char, "glyph": None, "readings": readings, "rules": []}

    def to_chars(group: List[str]) -> List[str]:
        return [glyph_to_char.get(g, g) for g in group]

    for lookup_name in _rclt_lookups(table):
        for rule_index, rule in enumerate(
            table["lookups"][lookup_name].get("subtables") or []
        ):
            match = rule.get("match") or []
            positions = [i for i, group in enumerate(match) if glyph in group]
            if not positions:
                continue
            applications = rule.get("apply") or []
            entry = {
                "lookup": lookup_name,
                "rule": rule_index,
                "context": [to_chars(group) for group in match],
                "target_at": None,
                "sub_lookup": None,
                "output_glyph": None,
                "output_reading": None,
                "ignore": not applications,
            }
            for application in applications:
                at = application.get("at")
                if at in positions:
                    sub = _single_sub(table, application.get("lookup", ""))
                    output = sub.get(glyph)
                    entry.update(
                        {
                            "target_at": at,
                            "sub_lookup": application.get("lookup"),
                            "output_glyph": output,
                            "output_reading": _glyph_reading(output, readings),
                        }
                    )
                    break
            if entry["ignore"]:
                input_begins = rule.get("inputBegins", 0)
                entry["target_at"] = (
                    input_begins if input_begins in positions else (positions[0])
                )
            if entry["target_at"] is None:
                # char appears only as context for another target; still useful
                entry["target_at"] = positions[0]
            rules_out.append(entry)

    return {"char": char, "glyph": glyph, "readings": readings, "rules": rules_out}
