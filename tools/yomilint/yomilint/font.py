"""The font under test: what it maps, what it shapes to, what a glyph is
made of. Everything the checks know about the font comes through here."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import uharfbuzz as hb
from fontTools.ttLib import TTFont

# Composite glyphs nest a few levels; deeper than this is a reference cycle.
MAX_COMPONENT_DEPTH = 16

Matrix = Tuple[float, float, float, float]
IDENTITY: Matrix = (1.0, 0.0, 0.0, 1.0)
# xMin, yMin, xMax, yMax
Box = Tuple[float, float, float, float]


@dataclass(frozen=True)
class Part:
    """A simple glyph a composite draws, where it is drawn, and the box it
    covers there."""

    glyph: str
    x: float
    y: float
    box: Box


def union(boxes: Sequence[Box]) -> Optional[Box]:
    """The box around `boxes`, or None when there is none."""
    if not boxes:
        return None
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


class CircularReference(ValueError):
    """A composite glyph refers to itself through its components."""


class FontUnderTest:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.tt = TTFont(str(self.path), lazy=False)
        self.glyph_order: List[str] = self.tt.getGlyphOrder()
        self.cmap: Dict[int, str] = dict(self.tt.getBestCmap() or {})
        # A glyph may be mapped from several characters: a font maps both
        # KANGXI RADICAL ONE and 一 to one glyph.
        self.chars_of: Dict[str, List[str]] = {}
        for code in sorted(self.cmap):
            self.chars_of.setdefault(self.cmap[code], []).append(chr(code))
        self._hb_font = hb.Font(hb.Face(self.path.read_bytes()))
        self._parts: Dict[str, List[Part]] = {}

    # ---- mapping -------------------------------------------------------

    def glyph_for(self, char: str) -> Optional[str]:
        return self.cmap.get(ord(char))

    def variation_sequences(self) -> Dict[Tuple[str, int], str]:
        """(character, selector) -> glyph, from the cmap format 14 subtable."""
        sequences: Dict[Tuple[str, int], str] = {}
        for table in self.tt["cmap"].tables:
            if table.format != 14:
                continue
            for selector, mappings in table.uvsDict.items():
                for code, glyph in mappings:
                    # None means "the default glyph of the character".
                    name = glyph if glyph is not None else self.cmap.get(code)
                    if name is not None:
                        sequences[(chr(code), selector)] = name
        return sequences

    def alternates(self) -> Dict[str, List[str]]:
        """Glyph -> the glyphs the `aalt` feature offers in its place."""
        if "GSUB" not in self.tt:
            return {}
        gsub = self.tt["GSUB"].table
        if not gsub.FeatureList or not gsub.LookupList:
            return {}
        lookups = {
            index
            for record in gsub.FeatureList.FeatureRecord
            if record.FeatureTag == "aalt"
            for index in record.Feature.LookupListIndex
        }
        offered: Dict[str, List[str]] = {}
        for index in sorted(lookups):
            for subtable in gsub.LookupList.Lookup[index].SubTable:
                if subtable.LookupType == 7:  # extension
                    subtable = subtable.ExtSubTable
                if subtable.LookupType == 1:  # single
                    for glyph, other in subtable.mapping.items():
                        offered.setdefault(glyph, []).append(other)
                elif subtable.LookupType == 3:  # alternate
                    for glyph, others in subtable.alternates.items():
                        offered.setdefault(glyph, []).extend(others)
        return offered

    # ---- metrics -------------------------------------------------------

    def advance(self, glyph: str) -> int:
        return int(self.tt["hmtx"][glyph][0])

    def window(self) -> Optional[Tuple[int, int]]:
        """The lowest and highest y Windows draws: outside usWinDescent and
        usWinAscent a glyph is cut off. None without an OS/2 table."""
        if "OS/2" not in self.tt:
            return None
        os2 = self.tt["OS/2"]
        return -os2.usWinDescent, os2.usWinAscent

    # ---- shaping -------------------------------------------------------

    def shape(self, text: str) -> List[str]:
        """The glyphs HarfBuzz gives for `text`, with its default features."""
        buffer = hb.Buffer()
        buffer.add_str(text)
        buffer.guess_segment_properties()
        hb.shape(self._hb_font, buffer)
        return [self.glyph_order[info.codepoint] for info in buffer.glyph_infos]

    # ---- glyph structure -----------------------------------------------

    def parts(self, glyph: str) -> List[Part]:
        """The simple glyphs `glyph` draws, composites followed to the end.
        A font without a `glyf` table has no composites: the glyph itself."""
        if glyph not in self._parts:
            if "glyf" not in self.tt:
                self._parts[glyph] = [Part(glyph, 0.0, 0.0, (0.0, 0.0, 0.0, 0.0))]
            else:
                found: List[Part] = []
                self._collect(glyph, IDENTITY, (0.0, 0.0), 0, found)
                self._parts[glyph] = found
        return self._parts[glyph]

    def _collect(
        self,
        name: str,
        matrix: Matrix,
        offset: Tuple[float, float],
        depth: int,
        found: List[Part],
    ) -> None:
        if depth > MAX_COMPONENT_DEPTH:
            raise CircularReference(name)
        glyph = self.tt["glyf"][name]
        a, b, c, d = matrix
        if not glyph.isComposite():
            if glyph.numberOfContours > 0:
                corners = [
                    (offset[0] + a * x + c * y, offset[1] + b * x + d * y)
                    for x in (glyph.xMin, glyph.xMax)
                    for y in (glyph.yMin, glyph.yMax)
                ]
                box = (
                    min(x for x, _ in corners),
                    min(y for _, y in corners),
                    max(x for x, _ in corners),
                    max(y for _, y in corners),
                )
                found.append(Part(name, offset[0], offset[1], box))
            return
        for component in glyph.components:
            # An anchored component has no offset of its own.
            x = float(getattr(component, "x", 0))
            y = float(getattr(component, "y", 0))
            child_offset = (offset[0] + a * x + c * y, offset[1] + b * x + d * y)
            child_matrix = matrix
            if hasattr(component, "transform"):
                (ta, tb), (tc, td) = component.transform
                child_matrix = (
                    a * ta + c * tb,
                    b * ta + d * tb,
                    a * tc + c * td,
                    b * tc + d * td,
                )
            self._collect(
                component.glyphName, child_matrix, child_offset, depth + 1, found
            )

    def circular_glyphs(self) -> List[str]:
        """One glyph of each loop of composite glyphs that refer to each
        other, in glyph order."""
        if "glyf" not in self.tt:
            return []
        glyf = self.tt["glyf"]
        done: Dict[str, bool] = {}  # name -> finished (False: on the path)
        loops: List[str] = []
        for start in self.glyph_order:
            if start in done:
                continue
            # (glyph, its components still to visit), without recursion: a
            # loop must not become a stack overflow here either.
            path = [(start, self._components(glyf, start))]
            done[start] = False
            while path:
                name, remaining = path[-1]
                if not remaining:
                    done[name] = True
                    path.pop()
                    continue
                child = remaining.pop()
                if child not in done:
                    done[child] = False
                    path.append((child, self._components(glyf, child)))
                elif done[child] is False:
                    loops.append(child)
        return list(dict.fromkeys(loops))

    @staticmethod
    def _components(glyf, name: str) -> List[str]:
        glyph = glyf[name]
        if not glyph.isComposite():
            return []
        return [component.glyphName for component in glyph.components]
