"""The checks. Each is a function from a `Context` to findings, registered
with an id, a severity and the reason it exists."""

from __future__ import annotations

import tempfile
from collections import Counter
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, Iterator, List, Optional, Tuple

from fontTools.ttLib import TTFont

from .font import Box, FontUnderTest, Part, union
from .profiles import Profile
from .readers import Dictionary, Phrase
from .resolve import ComponentsResolver, Resolver
from .spec import Spec

ERROR = "ERROR"
WARN = "WARN"
INFO = "INFO"

MAX_GLYPHS = 65535


@dataclass(frozen=True)
class Finding:
    check: str
    severity: str
    subject: str
    message: str


@dataclass(frozen=True)
class Annotated:
    """A glyph that draws an annotation: the character it belongs to, the
    box of the character, the box of the annotation and the letter parts
    the annotation is made of."""

    char: str
    glyph: str
    base: Box
    box: Box
    letters: List[Part]


@dataclass
class Context:
    """What a check may look at."""

    font: FontUnderTest
    spec: Spec
    profile: Profile
    dictionary: Dictionary
    phrases: List[Phrase]
    resolver: Resolver
    # The resolver of the other kind, when the spec allows both.
    second_resolver: Optional[Resolver] = None
    _sequences: Optional[Dict] = field(default=None, repr=False)
    _selected: Optional[Dict[str, List[str]]] = field(default=None, repr=False)
    _alternates: Optional[Dict] = field(default=None, repr=False)
    _annotations: Optional[List[Annotated]] = field(default=None, repr=False)

    def reading(self, glyph: str) -> Optional[str]:
        return self.resolver.reading(glyph)

    def layout(self, glyph: str) -> Optional[Tuple[Box, Box]]:
        """The box of the character and the box of its annotation in
        `glyph`, or None when it has not both or its parts cannot be told
        apart (the font has no composites, or the spec no way to name the
        letters)."""
        found = self._split(glyph)
        return None if found is None else (found[0], found[1])

    def _split(self, glyph: str) -> Optional[Tuple[Box, Box, List[Part]]]:
        for resolver in (self.resolver, self.second_resolver):
            if isinstance(resolver, ComponentsResolver):
                base, annotation = resolver.split(glyph)
                base_box = union([part.box for part in base])
                annotation_box = union([part.box for part, _ in annotation])
                if base_box is None or annotation_box is None:
                    return None
                return base_box, annotation_box, [part for part, _ in annotation]
        return None

    def annotations(self) -> List[Annotated]:
        """Every glyph that draws an annotation, with what it is made of.
        Worked out once: the geometry checks all walk it."""
        if self._annotations is None:
            self._annotations = []
            for char, _ in self.mapped():
                for glyph in self.glyphs_of(char):
                    found = self._split(glyph)
                    if found is not None:
                        self._annotations.append(
                            Annotated(char, glyph, found[0], found[1], found[2])
                        )
        return self._annotations

    def annotated(self) -> Iterator[Tuple[str, str, Box, Box]]:
        """(character, glyph, character box, annotation box) of every glyph
        that draws an annotation."""
        for item in self.annotations():
            yield item.char, item.glyph, item.base, item.box

    def expected(self, char: str) -> List[str]:
        return [self.profile.normalize(r) for r in self.dictionary.get(char, [])]

    def mapped(self) -> Iterator[Tuple[str, str]]:
        """The characters of the dictionary the font has a glyph for, each
        with its default glyph."""
        for char in self.dictionary:
            glyph = self.font.glyph_for(char)
            if glyph is not None:
                yield char, glyph

    def sequences(self) -> Dict:
        if self._sequences is None:
            self._sequences = self.font.variation_sequences()
        return self._sequences

    def alternates(self) -> Dict[str, List[str]]:
        if self._alternates is None:
            self._alternates = self.font.alternates()
        return self._alternates

    def glyphs_of(self, char: str) -> List[str]:
        """Every glyph the font can show for `char`: the default one, those
        the variation selectors choose, and those `aalt` offers."""
        default = self.font.glyph_for(char)
        if default is None:
            return []
        if self._selected is None:
            # Grouped once: a font has tens of thousands of sequences.
            self._selected = {}
            for (c, _), glyph in self.sequences().items():
                self._selected.setdefault(c, []).append(glyph)
        glyphs = [default]
        glyphs += self._selected.get(char, [])
        glyphs += self.alternates().get(default, [])
        return list(dict.fromkeys(glyphs))


CheckFunction = Callable[[Context], Iterable[Finding]]


@dataclass(frozen=True)
class Check:
    id: str
    severity: str
    rationale: str
    run: CheckFunction


CHECKS: List[Check] = []


def check(id: str, severity: str, rationale: str) -> Callable[[Callable], Callable]:
    """Registers a check. The function yields (subject, message) pairs."""

    def register(function: Callable) -> Callable:
        def run(context: Context) -> Iterator[Finding]:
            for subject, message in function(context):
                yield Finding(id, severity, subject, message)

        CHECKS.append(Check(id, severity, rationale, run))
        return function

    return register


def shown(reading: Optional[str]) -> str:
    return "no annotation" if reading is None else reading


# ---- coverage ----------------------------------------------------------


@check(
    "coverage/charset-has-glyph",
    ERROR,
    "A character of the dictionary the font has no glyph for falls back to "
    "another font, without annotation.",
)
def charset_has_glyph(context: Context):
    for char in context.dictionary:
        if context.font.glyph_for(char) is None:
            yield char, f"U+{ord(char):04X} is not in the font"


@check(
    "coverage/charset-has-reading",
    ERROR,
    "The default glyph of an annotated character must show a reading.",
)
def charset_has_reading(context: Context):
    for char, glyph in context.mapped():
        if context.reading(glyph) is None:
            yield char, f"its default glyph {glyph} shows no annotation"


@check(
    "coverage/default-reading",
    ERROR,
    "Without context or a selector, a character shows the dictionary's first "
    "reading.",
)
def default_reading(context: Context):
    for char, glyph in context.mapped():
        reading = context.reading(glyph)
        expected = context.expected(char)
        if reading is not None and expected and reading != expected[0]:
            yield char, f"shows {reading}, the dictionary's default is {expected[0]}"


@check(
    "coverage/all-readings-reachable",
    ERROR,
    "Every reading the dictionary lists must be shown by some glyph the "
    "user can reach.",
)
def all_readings_reachable(context: Context):
    for char, _ in context.mapped():
        reachable = {context.reading(glyph) for glyph in context.glyphs_of(char)}
        missing = [r for r in context.expected(char) if r not in reachable]
        if missing:
            yield char, f"no glyph shows {', '.join(missing)}"


# ---- context -----------------------------------------------------------


@check(
    "context/phrase",
    ERROR,
    "A phrase must shape to the readings its characters have in it.",
)
def phrase(context: Context):
    for item in context.phrases:
        expected = [context.profile.normalize(r) for r in item.readings]
        if len(expected) != len(item.text):
            yield item.text, (
                f"has {len(item.text)} characters and {len(expected)} readings "
                f"(line {item.line})"
            )
            continue
        absent = [c for c in item.text if context.font.glyph_for(c) is None]
        if absent:
            yield item.text, f"{''.join(absent)} is not in the font"
            continue
        glyphs = context.font.shape(item.text)
        got = [context.reading(glyph) for glyph in glyphs]
        if got != expected:
            yield item.text, (
                f"reads {'/'.join(shown(r) for r in got)}, "
                f"expected {'/'.join(expected)}"
            )


@check(
    "context/isolated-default",
    ERROR,
    "A character with several readings, set alone, shows the default one: no "
    "rule may fire without context.",
)
def isolated_default(context: Context):
    for char, _ in context.mapped():
        expected = context.expected(char)
        if len(expected) < 2:
            continue
        glyphs = context.font.shape(char)
        got = context.reading(glyphs[0]) if len(glyphs) == 1 else None
        if got != expected[0]:
            yield char, f"alone it reads {shown(got)}, expected {expected[0]}"


@check(
    "context/phrase-in-sentence",
    ERROR,
    "A phrase reads the same inside a sentence as alone: a rule must not "
    "depend on the phrase starting or ending the text.",
)
def phrase_in_sentence(context: Context):
    in_phrases = {char for item in context.phrases for char in item.text}
    # Put around each phrase: a character of one reading that is in none.
    filler = next(
        (
            char
            for char, _ in context.mapped()
            if len(context.expected(char)) == 1 and char not in in_phrases
        ),
        None,
    )
    if filler is None:
        return
    for item in context.phrases:
        expected = [context.profile.normalize(r) for r in item.readings]
        if len(expected) != len(item.text):
            continue
        if any(context.font.glyph_for(c) is None for c in item.text):
            continue
        alone = [context.reading(g) for g in context.font.shape(item.text)]
        if alone != expected:
            continue  # `context/phrase` reports it
        glyphs = context.font.shape(filler + item.text + filler)
        got = [context.reading(g) for g in glyphs[1:-1]]
        if got != expected:
            yield item.text, (
                f"between two {filler} it reads "
                f"{'/'.join(shown(r) for r in got)}, expected {'/'.join(expected)}"
            )


# ---- selection ---------------------------------------------------------


@check(
    "select/ivs-order",
    ERROR,
    "Variation selector n chooses the dictionary's n-th reading, so a "
    "document that picked a reading keeps it.",
)
def ivs_order(context: Context):
    base = context.spec.selector_base
    if base is None:
        return
    sequences = context.sequences()
    for char, _ in context.mapped():
        expected = context.expected(char)
        if len(expected) < 2:
            continue
        wrong = []
        for n, reading in enumerate(expected, 1):
            glyph = sequences.get((char, base + n))
            if glyph is None:
                wrong.append(f"U+{base + n:04X} is missing ({reading})")
            elif context.reading(glyph) != reading:
                got = shown(context.reading(glyph))
                wrong.append(f"U+{base + n:04X} shows {got}, expected {reading}")
        if wrong:
            yield char, "; ".join(wrong)


@check(
    "select/ivs-none",
    WARN,
    "The base selector chooses the character without annotation.",
)
def ivs_none(context: Context):
    base = context.spec.selector_base
    if base is None:
        return
    sequences = context.sequences()
    for char, _ in context.mapped():
        glyph = sequences.get((char, base))
        if glyph is None:
            yield char, f"U+{base:04X} is missing"
        elif context.reading(glyph) is not None:
            yield char, f"U+{base:04X} shows {context.reading(glyph)}"


@check(
    "select/aalt-covers-readings",
    ERROR,
    "The alternates an application lists (`aalt`) are the bare character and "
    "every reading, in the dictionary's order.",
)
def aalt_covers_readings(context: Context):
    alternates = context.alternates()
    for char, default in context.mapped():
        expected = context.expected(char)
        offered = alternates.get(default, [])
        readings = [context.reading(glyph) for glyph in offered]
        if None not in readings:
            yield char, "aalt does not offer the character without annotation"
        elif len(expected) > 1 and [r for r in readings if r is not None] != expected:
            got = "/".join(shown(r) for r in readings)
            yield char, f"aalt offers {got}, expected {'/'.join(expected)}"


# ---- resolving ---------------------------------------------------------


@check(
    "resolve/methods-agree",
    WARN,
    "A glyph's name and its parts must say the same reading; a difference is "
    "a glyph built or named for the wrong one.",
)
def methods_agree(context: Context):
    if context.second_resolver is None:
        return
    for char, _ in context.mapped():
        for glyph in context.glyphs_of(char):
            first = context.reading(glyph)
            second = context.second_resolver.reading(glyph)
            if first != second:
                yield char, f"{glyph} is {shown(first)} one way and {shown(second)} the other"
                break


# ---- geometry ----------------------------------------------------------


def once_per_character(found: Iterable[Tuple[str, str]]) -> Iterator[Tuple[str, str]]:
    """The first finding of each character: its glyphs share a design, so
    one says it."""
    seen = set()
    for char, message in found:
        if char not in seen:
            seen.add(char)
            yield char, message


@check(
    "geometry/no-clipping",
    ERROR,
    "Windows cuts a glyph off above usWinAscent and below usWinDescent; an "
    "annotation that reaches past them loses its top or bottom.",
)
def no_clipping(context: Context):
    window = context.font.window()
    if window is None:
        return
    low, high = window

    def found():
        for char, glyph, _, box in context.annotated():
            if box[3] > high:
                yield char, f"{glyph} reaches {box[3]:g}, above usWinAscent {high}"
            elif box[1] < low:
                yield char, f"{glyph} reaches {box[1]:g}, below usWinDescent {low}"

    yield from once_per_character(found())


@check(
    "geometry/no-overlap",
    ERROR,
    "The annotation must stand clear of its character, at least "
    "[geometry] min_gap away.",
)
def no_overlap(context: Context):
    side = context.spec.position
    least = context.spec.min_gap

    def found():
        for char, glyph, base, box in context.annotated():
            gap = {
                "top": box[1] - base[3],
                "bottom": base[1] - box[3],
                "right": box[0] - base[2],
                "left": base[0] - box[2],
            }[side]
            if gap < 0:
                yield char, f"{glyph}: the annotation overlaps the character by {-gap:g}"
            elif gap < least:
                yield char, f"{glyph}: the annotation is {gap:g} away, less than {least:g}"

    yield from once_per_character(found())


@check(
    "geometry/advance-matches-base",
    ERROR,
    "Choosing another reading must not move the text: every glyph of a "
    "character has the same advance width.",
)
def advance_matches_base(context: Context):
    for char, default in context.mapped():
        expected = context.font.advance(default)
        for glyph in context.glyphs_of(char):
            if context.font.advance(glyph) != expected:
                yield char, (
                    f"{glyph} advances {context.font.advance(glyph)}, "
                    f"{default} advances {expected}"
                )
                break


@check(
    "geometry/annotation-within-advance",
    WARN,
    "An annotation wider than its character runs into the next one.",
)
def annotation_within_advance(context: Context):
    if context.spec.position not in ("top", "bottom"):
        return

    def found():
        for char, glyph, _, box in context.annotated():
            advance = context.font.advance(glyph)
            if box[0] < 0 or box[2] > advance:
                yield char, (
                    f"{glyph}: the annotation spans {box[0]:g} to {box[2]:g}, "
                    f"outside 0 to {advance}"
                )

    yield from once_per_character(found())


def _beside_the_line(context: Context) -> bool:
    """Whether the annotation stands above or below the character: the
    checks of its width and baseline mean nothing for one at the side."""
    return context.spec.position in ("top", "bottom")


@check(
    "geometry/centered",
    WARN,
    "An annotation off the middle of its character looks as if it belonged to "
    "the neighbour; its middle must be within [geometry] center_tolerance of "
    "the middle of the advance.",
)
def centered(context: Context):
    if not _beside_the_line(context):
        return
    em = context.font.units_per_em()
    tolerance = context.spec.center_tolerance

    def found():
        for char, glyph, _, box in context.annotated():
            # The advance of the character itself: a glyph that advances
            # otherwise is the business of geometry/advance-matches-base.
            default = context.font.glyph_for(char) or glyph
            advance = context.font.advance(default)
            off = (box[0] + box[2]) / 2 - advance / 2
            if abs(off) / em > tolerance:
                side = "right" if off > 0 else "left"
                yield char, (
                    f"{glyph}: the annotation is {abs(off):.1f} units "
                    f"({abs(off) / em:.4f} em) to the {side} of the middle of "
                    f"the advance, more than {tolerance:g} em"
                )

    yield from once_per_character(found())


@check(
    "geometry/baseline-aligned",
    WARN,
    "The letters of annotations stand on one line across the font; one "
    "raised or lowered by a few units shows next to its neighbours.",
)
def baseline_aligned(context: Context):
    if not _beside_the_line(context):
        return
    em = context.font.units_per_em()
    tolerance = context.spec.baseline_tolerance
    # The baseline of a letter is where its glyph's origin is drawn. The
    # usual one is the one most letters stand on.
    counts = Counter(
        round(part.y) for item in context.annotations() for part in item.letters
    )
    if not counts:
        return
    usual = counts.most_common(1)[0][0]

    def found():
        for item in context.annotations():
            for part in item.letters:
                off = abs(part.y - usual)
                if off / em > tolerance:
                    yield item.char, (
                        f"{item.glyph}: a letter stands on {part.y:g}, the usual "
                        f"baseline is {usual}: {off:.1f} units ({off / em:.4f} "
                        f"em) apart, more than {tolerance:g} em"
                    )
                    break

    yield from once_per_character(found())


@check(
    "geometry/min-scale",
    WARN,
    "A long reading is drawn smaller to fit; below [geometry] min_scale of "
    "the largest letters it is too small to read.",
)
def min_scale(context: Context):
    items = [item for item in context.annotations() if item.letters]
    if not items:
        return
    # The size of a reading is that of its smallest letter; the full size is
    # the largest any reading is drawn at.
    sizes = {id(item): min(part.scale for part in item.letters) for item in items}
    largest = max(sizes.values())
    if largest <= 0:
        return
    least = context.spec.min_scale

    def found():
        for item in items:
            ratio = sizes[id(item)] / largest
            if ratio < least:
                yield item.char, (
                    f"{item.glyph}: the letters are drawn at {ratio:.2f} of the "
                    f"largest, less than {least:g}"
                )

    yield from once_per_character(found())


@check(
    "geometry/line-gap",
    WARN,
    "With the font's own line spacing (hhea), the annotation of one line must "
    "not reach the characters of the line next to it.",
)
def line_gap(context: Context):
    side = context.spec.position
    pitch = context.font.line_pitch()
    if side not in ("top", "bottom") or pitch is None or not context.annotations():
        return
    least = context.spec.min_gap
    # Lines are `pitch` apart. Above the characters, the annotation of the
    # lower line reaches up toward the characters of the upper line; below,
    # the annotation of the upper line reaches down.
    if side == "top":
        reaching = max(context.annotations(), key=lambda item: item.box[3])
        facing = min(context.annotations(), key=lambda item: item.base[1])
        gap = pitch + facing.base[1] - reaching.box[3]
    else:
        reaching = min(context.annotations(), key=lambda item: item.box[1])
        facing = max(context.annotations(), key=lambda item: item.base[3])
        gap = pitch + reaching.box[1] - facing.base[3]
    if gap < least:
        yield reaching.char, (
            f"lines {pitch} apart leave {gap:g} between the annotation of "
            f"{reaching.glyph} and the character of {facing.glyph} on the next "
            f"line, less than {least:g}"
        )


# ---- format ------------------------------------------------------------


@check(
    "format/glyph-count",
    WARN,
    "A font holds 65,535 glyphs; one close to that has no room for another " "reading.",
)
def glyph_count(context: Context):
    count = len(context.font.glyph_order)
    spare = MAX_GLYPHS - count
    if spare < context.spec.glyph_headroom:
        yield "font", (
            f"{count} glyphs leave {spare} to spare, "
            f"fewer than {context.spec.glyph_headroom}"
        )


@check(
    "format/tables-parse",
    ERROR,
    "A table fontTools cannot read is a table applications may drop: a "
    "broken GSUB loses every reading rule at once.",
)
def tables_parse(context: Context):
    strict = TTFont(str(context.font.path), lazy=False, ignoreDecompileErrors=False)
    for tag in strict.keys():
        if tag == "GlyphOrder":
            continue
        try:
            strict[tag]
        except Exception as error:  # fontTools raises many kinds
            yield tag, f"{type(error).__name__}: {error}"


@check(
    "format/no-circular-reference",
    ERROR,
    "Composite glyphs that refer to each other cannot be drawn, and stop "
    "some applications.",
)
def no_circular_reference(context: Context):
    for glyph in context.font.circular_glyphs():
        yield glyph, "is its own component, through the glyphs it refers to"


@check(
    "format/ots",
    ERROR,
    "Browsers pass a font through the OpenType Sanitizer and refuse the "
    "tables, or the font, it rejects. Runs when the `ots` module is installed.",
)
def sanitizer(context: Context):
    try:
        import ots
    except ImportError:
        return
    with tempfile.NamedTemporaryFile() as out:
        done = ots.sanitize(str(context.font.path), out.name, capture_output=True)
    if done.returncode != 0:
        lines = done.stderr.decode(errors="replace").strip().splitlines()
        yield "font", lines[-1] if lines else f"ots exited with {done.returncode}"
