"""Small annotation fonts for the tests, built with fontTools.

`make_font` builds a pinyin font the way Mengshen does: each hanzi has a
glyph without annotation (`<base>.ss00`), one composite per reading
(`.ss01`, `.ss02`, ...) made of dedicated letter glyphs above the hanzi, and
a default glyph. Readings are switched by `rclt` rules, `aalt` alternates and
variation selectors. Each keyword of `make_font` breaks the font in one way,
so a test can show that a check notices it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables._g_l_y_f import Glyph

IVS_BASE = 0xE01E0
UNITS_PER_EM = 1000
ADVANCE = 1000
LETTER_SCALE = 0.3
LETTER_ADVANCE = 150
ANNOTATION_Y = 760

# Letter with a tone mark -> the name Mengshen gives its glyph.
TONE_NUMBER = {
    "ā": "a1",
    "á": "a2",
    "ǎ": "a3",
    "à": "a4",
    "ē": "e1",
    "é": "e2",
    "ě": "e3",
    "è": "e4",
    "ī": "i1",
    "í": "i2",
    "ǐ": "i3",
    "ì": "i4",
    "ō": "o1",
    "ó": "o2",
    "ǒ": "o3",
    "ò": "o4",
    "ū": "u1",
    "ú": "u2",
    "ǔ": "u3",
    "ù": "u4",
    "ü": "v",
    "ǖ": "v1",
    "ǘ": "v2",
    "ǚ": "v3",
    "ǜ": "v4",
}

# The readings of the test font, the first one the default.
READINGS: Dict[str, List[str]] = {
    "一": ["yī"],
    "手": ["shǒu"],
    "着": ["zhe", "zhuó"],
    "背": ["bèi", "bēi"],
}

# 着手 reads zhuó/shǒu, but not after 背: 背着手 is bèi/zhe/shǒu.
RCLT = """
lookup zhe_to_zhuo {{ sub {zhe} by {zhe}.ss02; }} zhe_to_zhuo;
feature rclt {{
  ignore sub {bei} {zhe}' {shou};
{ignores}  sub {zhe}' lookup zhe_to_zhuo {shou};
}} rclt;
"""


def base_name(char: str) -> str:
    return f"uni{ord(char):04X}"


def letter_glyph_name(letter: str) -> str:
    return f"py_alphabet_{TONE_NUMBER.get(letter, letter)}"


def _box(x0: int, y0: int, x1: int, y1: int) -> Glyph:
    pen = TTGlyphPen(None)
    pen.moveTo((x0, y0))
    pen.lineTo((x1, y0))
    pen.lineTo((x1, y1))
    pen.lineTo((x0, y1))
    pen.closePath()
    return pen.glyph()


def _composite(
    parts: Sequence[Tuple[str, Tuple[float, ...]]], glyphs: Dict[str, Glyph]
) -> Glyph:
    pen = TTGlyphPen(glyphs)
    for name, transform in parts:
        pen.addComponent(name, transform)
    return pen.glyph()


@dataclass
class FontPlan:
    """What `make_font` builds; the tests change one field to break it."""

    readings: Dict[str, List[str]] = field(
        default_factory=lambda: {char: list(r) for char, r in READINGS.items()}
    )
    # The reading the glyph of (char, ss index) really shows, when it is not
    # the one the dictionary gives.
    shown: Dict[Tuple[str, int], str] = field(default_factory=dict)
    with_rclt: bool = True
    with_aalt: bool = True
    with_selectors: bool = True
    # (char, selector offset) pairs to leave out of the variation sequences.
    missing_selectors: Sequence[Tuple[str, int]] = ()
    # Characters to leave out of the cmap.
    unmapped: Sequence[str] = ()
    # Characters after which the 着手 rule wrongly does not fire.
    ignore_after: Sequence[str] = ()
    # Where the annotation sits and how far apart its letters are.
    annotation_y: int = ANNOTATION_Y
    letter_advance: int = LETTER_ADVANCE
    # (char, ss index) -> how far its annotation is moved sideways, how far
    # it is raised, and by what factor its letters (and their spacing) are
    # shrunk. Each moves one glyph's annotation and nothing else.
    annotation_dx: Dict[Tuple[str, int], int] = field(default_factory=dict)
    baseline_shift: Dict[Tuple[str, int], int] = field(default_factory=dict)
    shrink: Dict[Tuple[str, int], float] = field(default_factory=dict)
    # hhea ascender: with the descender it sets the line spacing.
    hhea_ascent: int = 1000
    # Glyph name -> an advance width other than the font's.
    advances: Dict[str, int] = field(default_factory=dict)
    # Two composite glyphs that refer to each other.
    circular: bool = False
    # Other code points mapped to the glyph of a character, as a font maps
    # KANGXI RADICAL ONE (U+2F00) to the glyph of 一.
    aliases: Dict[str, str] = field(default_factory=dict)
    # Extra glyphs that do nothing, to reach a glyph count.
    padding_glyphs: int = 0


def _annotated(
    plan: FontPlan, char: str, index: int, glyphs: Dict[str, Glyph]
) -> Glyph:
    """The composite for reading `index` (1-based) of `char`."""
    reading = plan.shown.get((char, index), plan.readings[char][index - 1])
    factor = plan.shrink.get((char, index), 1.0)
    step = plan.letter_advance * factor
    scale = LETTER_SCALE * factor
    # The ink of the letters, not their advances, is what is centered.
    ink = step * (len(reading) - 1) + 400 * scale
    x = (ADVANCE - ink) / 2 - 50 * scale + plan.annotation_dx.get((char, index), 0)
    y = plan.annotation_y + plan.baseline_shift.get((char, index), 0)
    parts: List[Tuple[str, Tuple[float, ...]]] = []
    for letter in reading:
        parts.append(
            (
                letter_glyph_name(letter),
                (scale, 0, 0, scale, x, y),
            )
        )
        x += step
    parts.append((f"{base_name(char)}.ss00", (1, 0, 0, 1, 0, 0)))
    return _composite(parts, glyphs)


def _features(plan: FontPlan, alternates: Sequence[str]) -> str:
    """The feature file: the reading rules and the alternates."""
    features = ""
    if plan.with_rclt:
        zhe, shou = base_name("着"), base_name("手")
        ignores = "".join(
            f"  ignore sub {base_name(c)} {zhe}' {shou};\n" for c in plan.ignore_after
        )
        features += RCLT.format(
            zhe=zhe, bei=base_name("背"), shou=shou, ignores=ignores
        )
    if plan.with_aalt:
        features += "feature aalt {\n  " + "\n  ".join(alternates) + "\n} aalt;\n"
    return features


def _hanzi_glyphs(
    plan: FontPlan, char: str, glyphs: Dict[str, Glyph]
) -> Tuple[List[str], str]:
    """Adds the glyphs of `char`. Returns the glyphs its selectors choose,
    the bare one first, and its `aalt` rule."""
    base = base_name(char)
    count = len(plan.readings[char])
    glyphs[f"{base}.ss00"] = _box(100, 0, 900, 700)
    if count == 1:
        # One reading: the default glyph carries it, as in Mengshen.
        glyphs[base] = _annotated(plan, char, 1, glyphs)
        return [f"{base}.ss00"], f"sub {base} by {base}.ss00;"
    for index in range(1, count + 1):
        glyphs[f"{base}.ss{index:02d}"] = _annotated(plan, char, index, glyphs)
    glyphs[base] = _composite([(f"{base}.ss01", (1, 0, 0, 1, 0, 0))], glyphs)
    variants = [f"{base}.ss{i:02d}" for i in range(count + 1)]
    return variants, f"sub {base} from [{' '.join(variants)}];"


def make_font(path: Path, plan: Optional[FontPlan] = None) -> Path:
    plan = plan or FontPlan()
    glyphs: Dict[str, Glyph] = {".notdef": _box(100, 0, 900, 700)}
    letters = sorted({ch for rs in plan.readings.values() for r in rs for ch in r})
    letters = sorted(set(letters) | {ch for r in plan.shown.values() for ch in r})
    for letter in letters:
        glyphs[letter_glyph_name(letter)] = _box(50, 0, 450, 500)

    cmap: Dict[int, str] = {}
    uvs: List[Tuple[int, int, str]] = []
    alternates: List[str] = []
    for char in plan.readings:
        base = base_name(char)
        variants, alternate = _hanzi_glyphs(plan, char, glyphs)
        alternates.append(alternate)
        if char not in plan.unmapped:
            cmap[ord(char)] = base
        for offset, variant in enumerate(variants):
            if (char, offset) not in plan.missing_selectors:
                uvs.append((ord(char), IVS_BASE + offset, variant))
    for alias, char in plan.aliases.items():
        cmap[ord(alias)] = base_name(char)
    for n in range(plan.padding_glyphs):
        glyphs[f"pad{n:05d}"] = Glyph()
    if plan.circular:
        # Two composites of .notdef for now; `_tie_the_loop` makes them
        # refer to each other once the font is saved.
        for name in ("loop.a", "loop.b"):
            glyphs[name] = _composite([(".notdef", (1, 0, 0, 1, 0, 0))], glyphs)

    order = list(glyphs)
    builder = FontBuilder(UNITS_PER_EM, isTTF=True)
    builder.setupGlyphOrder(order)
    builder.setupCharacterMap(cmap, uvs=uvs if plan.with_selectors else None)
    builder.setupGlyf(glyphs)
    builder.setupHorizontalMetrics(
        {name: (plan.advances.get(name, ADVANCE), 0) for name in order}
    )
    builder.setupHorizontalHeader(ascent=plan.hhea_ascent, descent=-200)
    builder.setupNameTable({"familyName": "Yomilint Test", "styleName": "Regular"})
    builder.setupOS2(usWinAscent=1000, usWinDescent=200)
    builder.setupPost()
    features = _features(plan, alternates)
    if features:
        addOpenTypeFeaturesFromString(builder.font, features)
    builder.save(str(path))
    if plan.circular:
        _tie_the_loop(path, order.index("loop.a"), order.index("loop.b"))
    return path


def _tie_the_loop(path: Path, first: int, second: int) -> None:
    """Makes the composites `first` and `second` each other's component.
    fontTools refuses to build such a font, so the saved file is patched:
    a composite's first component index is 12 bytes into the glyph."""
    data = bytearray(path.read_bytes())
    tables = int.from_bytes(data[4:6], "big")
    offset = {}
    for record in range(12, 12 + 16 * tables, 16):
        tag = bytes(data[record : record + 4]).decode()
        offset[tag] = int.from_bytes(data[record + 8 : record + 12], "big")
    long_loca = int.from_bytes(data[offset["head"] + 50 : offset["head"] + 52], "big")

    def glyph_start(gid: int) -> int:
        at = offset["loca"] + gid * (4 if long_loca else 2)
        if long_loca:
            return offset["glyf"] + int.from_bytes(data[at : at + 4], "big")
        return offset["glyf"] + 2 * int.from_bytes(data[at : at + 2], "big")

    for gid, other in ((first, second), (second, first)):
        start = glyph_start(gid)
        data[start + 12 : start + 14] = other.to_bytes(2, "big")
    path.write_bytes(bytes(data))


def corrupt_gsub(path: Path) -> Path:
    """Points the GSUB script, feature and lookup lists past the table."""
    data = bytearray(path.read_bytes())
    tables = int.from_bytes(data[4:6], "big")
    for record in range(12, 12 + 16 * tables, 16):
        if data[record : record + 4] == b"GSUB":
            start = int.from_bytes(data[record + 8 : record + 12], "big")
            data[start + 4 : start + 10] = b"\xff\xf0" * 3
    path.write_bytes(bytes(data))
    return path


def write_dictionary(
    path: Path, readings: Optional[Dict[str, List[str]]] = None
) -> Path:
    """A dictionary in Mengshen's `merged-mapping-table.txt` format."""
    lines = [
        f"U+{ord(char):04X}: {','.join(rs)}  #{char}"
        for char, rs in (readings or READINGS).items()
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_phrases(path: Path, lines: Sequence[str]) -> Path:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
