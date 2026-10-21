"""Data tests for res/phonics/unicode_mapping_table/overwrite.txt."""

from pathlib import Path

OVERWRITE = (
    Path(__file__).resolve().parents[3]
    / "res"
    / "phonics"
    / "unicode_mapping_table"
    / "overwrite.txt"
)


def _load_overwrite():
    entries = {}
    for line in OVERWRITE.read_text(encoding="utf-8").splitlines():
        if not line.startswith("U+"):
            continue
        code, rest = line.split(":", 1)
        pinyins, _, hanzi = rest.partition("#")
        entries[int(code[2:], 16)] = (pinyins.strip().split(","), hanzi.strip())
    return entries


def test_ei_interjection_has_pinyin():
    """Issue #30: 诶 (U+8BF6) must have pinyin (ēi/éi/ěi/èi)."""
    entries = _load_overwrite()

    assert 0x8BF6 in entries
    pinyins, hanzi = entries[0x8BF6]
    assert hanzi == "诶"
    assert set(pinyins) == {"ēi", "éi", "ěi", "èi"}
    assert pinyins[0] == "éi"
