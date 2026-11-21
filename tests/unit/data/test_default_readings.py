# -*- coding: utf-8 -*-
"""Default (first) readings of common polyphones.

The first reading in merged-mapping-table.txt is the default glyph and the
n-th reading is selected by IVS U+E01E0+n, so the order is significant.
"""

# cspell:ignore gǎng kǎng zhèi Hanyu

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
OVERWRITE = ROOT / "res" / "phonics" / "unicode_mapping_table" / "overwrite.txt"
MERGED = ROOT / "outputs" / "merged-mapping-table.txt"
PATTERN_TWO = ROOT / "outputs" / "duoyinzi_pattern_two.json"

EXPECTED = {
    "离": ["lí", "chī"],
    "離": ["lí", "chī"],
    "这": ["zhè", "zhèi"],
    "這": ["zhè", "zhèi"],
    # gǎng is not attested in any pinyin-data source; kǎng is (kHanyuPinyin)
    "奋": ["fèn", "kǎng"],
    "奮": ["fèn"],
}


def _table(path: Path) -> dict[str, list[str]]:
    table = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("U+") or ":" not in line:
            continue
        code, rest = line.split(":", 1)
        readings = [p.strip() for p in rest.split("#")[0].split(",") if p.strip()]
        table[chr(int(code[2:], 16))] = readings
    return table


@pytest.mark.parametrize("path", [OVERWRITE, MERGED], ids=["overwrite", "merged"])
@pytest.mark.parametrize("char", list(EXPECTED))
def test_default_reading_order(path, char):
    assert _table(path)[char] == EXPECTED[char]


def test_pattern_two_leaves_default_li_alone():
    """间作离间 reads 离 as lí, which is now the default: no lookup for 离."""
    data = json.loads(PATTERN_TWO.read_text(encoding="utf-8"))
    for lookup in data["lookup_table"].values():
        assert "离" not in lookup
    assert {"离": None} in data["patterns"]["间作离间"]
