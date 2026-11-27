"""The checks. Each is a function from a `Context` to findings, registered
with an id, a severity and the reason it exists."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, Iterator, List, Optional, Tuple

from fontTools.ttLib import TTFont

from .font import FontUnderTest
from .profiles import Profile
from .readers import Dictionary, Phrase
from .resolve import Resolver
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
    _alternates: Optional[Dict] = field(default=None, repr=False)

    def reading(self, glyph: str) -> Optional[str]:
        return self.resolver.reading(glyph)

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
        glyphs = [default]
        glyphs += [g for (c, _), g in self.sequences().items() if c == char]
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


# ---- format ------------------------------------------------------------


@check(
    "format/glyph-count",
    WARN,
    "A font holds 65,535 glyphs; one close to that has no room for another "
    "reading.",
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
