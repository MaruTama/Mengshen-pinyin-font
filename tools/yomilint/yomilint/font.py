"""The font under test: what it maps, what it shapes to, what a glyph is
made of. Everything the checks know about the font comes through here."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import uharfbuzz as hb
from fontTools.ttLib import TTFont

# Composite glyphs nest a few levels; deeper than this is a reference cycle.
MAX_COMPONENT_DEPTH = 16

Matrix = Tuple[float, float, float, float]
IDENTITY: Matrix = (1.0, 0.0, 0.0, 1.0)


@dataclass(frozen=True)
class Part:
    """A simple glyph a composite draws, and where it is drawn."""

    glyph: str
    x: float
    y: float


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
                self._parts[glyph] = [Part(glyph, 0.0, 0.0)]
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
        if not glyph.isComposite():
            if glyph.numberOfContours > 0:
                found.append(Part(name, offset[0], offset[1]))
            return
        a, b, c, d = matrix
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
