"""The substitution rules of a font, read without shaping anything.

`GsubModel` turns the contextual lookups (GSUB types 5 and 6, in the three
formats each, also behind an Extension lookup) into `Rule`s, and answers
static questions about them: which rule can never fire, which two rules claim
one context, which lookups a feature reaches.

How OpenType applies a lookup, which the definitions here rest on: the glyph
sequence is walked from the start; at each position the subtables of the
lookup are tried in order, and inside a subtable the rules in order. The first
rule whose context matches wins and the others are not tried at that position.
A rule without actions (what `ignore sub` makes) matches and wins all the
same. The lookups of the features that are on run one after another in
LookupList order, each on the output of the one before.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Dict,
    FrozenSet,
    Iterable,
    Iterator,
    List,
    Optional,
    Set,
    Tuple,
)

# GSUB lookup types.
SINGLE, MULTIPLE, ALTERNATE, LIGATURE, CONTEXT, CHAIN, EXTENSION = 1, 2, 3, 4, 5, 6, 7

# How many glyphs of a set a description names before it says "and N more".
SHOWN = 4


@dataclass(frozen=True)
class GlyphSet:
    """The glyphs a position of a rule accepts: those listed, or (`negated`)
    every glyph but those listed, as class 0 of a class definition is. The
    font is taken to have more glyphs than any list names, so a list never
    holds the rest of the font."""

    glyphs: FrozenSet[str]
    negated: bool = False

    def has(self, glyph: str) -> bool:
        return (glyph in self.glyphs) != self.negated

    def holds(self, other: "GlyphSet") -> bool:
        """Whether every glyph of `other` is in this set."""
        if not self.negated:
            return not other.negated and other.glyphs <= self.glyphs
        if other.negated:
            return self.glyphs <= other.glyphs
        return self.glyphs.isdisjoint(other.glyphs)

    def empty(self) -> bool:
        return not self.negated and not self.glyphs

    def text(self) -> str:
        names = sorted(self.glyphs)
        shown = " ".join(names[:SHOWN])
        if len(names) > SHOWN:
            shown += f" and {len(names) - SHOWN} more"
        if self.negated:
            return f"[any but {shown}]" if names else "[any]"
        return names[0] if len(names) == 1 else f"[{shown}]"


@dataclass(frozen=True)
class Rule:
    """One contextual rule: what must stand before, at and after a position,
    and the lookups it calls. `backtrack` runs outwards from the input (the
    glyph just before it first); `actions` are (index into the input, index
    of the lookup called)."""

    lookup: int
    subtable: int
    number: int
    backtrack: Tuple[GlyphSet, ...]
    input: Tuple[GlyphSet, ...]
    lookahead: Tuple[GlyphSet, ...]
    actions: Tuple[Tuple[int, int], ...]

    def where(self) -> str:
        return f"lookup {self.lookup} subtable {self.subtable} rule {self.number}"

    def context(self) -> Tuple[Tuple[GlyphSet, ...], ...]:
        return self.backtrack, self.input, self.lookahead

    def text(self) -> str:
        """The rule as feature syntax shows its match."""
        before = [item.text() for item in reversed(self.backtrack)]
        inside = [item.text() + "'" for item in self.input]
        after = [item.text() for item in self.lookahead]
        return " ".join(before + inside + after)

    def covers(self, other: "Rule") -> bool:
        """Whether this rule matches at every position where `other` does.
        It does when the inputs are as long, each of its sets holds the
        other's, and it asks no more of the surroundings: its backtrack and
        lookahead are no longer, and held position by position."""
        if len(self.input) != len(other.input):
            return False
        if len(self.backtrack) > len(other.backtrack):
            return False
        if len(self.lookahead) > len(other.lookahead):
            return False
        pairs = [
            *zip(self.backtrack, other.backtrack),
            *zip(self.input, other.input),
            *zip(self.lookahead, other.lookahead),
        ]
        return all(mine.holds(theirs) for mine, theirs in pairs)


# ---- reading the subtables ----------------------------------------------


def _set(glyphs: Iterable[str]) -> GlyphSet:
    return GlyphSet(frozenset(glyphs))


class _Classes:
    """A class definition, or its absence (every glyph is class 0)."""

    def __init__(self, classdef: Any) -> None:
        members: Dict[int, Set[str]] = {}
        for glyph, number in (getattr(classdef, "classDefs", None) or {}).items():
            if number:
                members.setdefault(number, set()).add(glyph)
        self.members = {n: frozenset(m) for n, m in members.items()}
        self.listed = frozenset(g for m in self.members.values() for g in m)

    def of(self, number: int) -> GlyphSet:
        """The glyphs of class `number`; for 0, all the font but the listed."""
        if number == 0:
            return GlyphSet(self.listed, negated=True)
        return GlyphSet(self.members.get(number, frozenset()))

    def among(self, number: int, glyphs: Iterable[str]) -> GlyphSet:
        """The glyphs of class `number` that are also in `glyphs`."""
        if number == 0:
            return _set(g for g in glyphs if g not in self.listed)
        return _set(g for g in glyphs if g in self.members.get(number, ()))


def _actions(records: Iterable[Any]) -> Tuple[Tuple[int, int], ...]:
    return tuple((r.SequenceIndex, r.LookupListIndex) for r in records)


# What a reader gives for each rule of a subtable: backtrack, input,
# lookahead and the lookup records.
Raw = Tuple[List[GlyphSet], List[GlyphSet], List[GlyphSet], Iterable[Any]]


def unwrap(subtable: Any) -> Any:
    return subtable.ExtSubTable if subtable.LookupType == EXTENSION else subtable


def subtable_rules(table: Any, lookup: int, subtable: int) -> List[Rule]:
    """The rules of one subtable of a lookup of type 5 or 6, in the order the
    font tries them; [] for any other kind of subtable. A rule with an empty
    set can match nothing and is left out, but keeps its number, so numbers
    stay the table's own."""
    table = unwrap(table)
    reader: Optional[Callable[[Any], Iterator[Raw]]] = {
        (CONTEXT, 1): _context1,
        (CONTEXT, 2): _context2,
        (CONTEXT, 3): _context3,
        (CHAIN, 1): _chain1,
        (CHAIN, 2): _chain2,
        (CHAIN, 3): _chain3,
    }.get((table.LookupType, getattr(table, "Format", 0)))
    if reader is None:
        return []
    found: List[Rule] = []
    for number, (backtrack, input, lookahead, records) in enumerate(reader(table)):
        if any(item.empty() for item in (*backtrack, *input, *lookahead)):
            continue
        found.append(
            Rule(
                lookup,
                subtable,
                number,
                tuple(backtrack),
                tuple(input),
                tuple(lookahead),
                _actions(records),
            )
        )
    return found


def _context1(table: Any) -> Iterator[Raw]:
    for glyph, rules in zip(table.Coverage.glyphs, table.SubRuleSet):
        for rule in rules.SubRule if rules else ():
            input = [_set([glyph])] + [_set([g]) for g in rule.Input]
            yield [], input, [], rule.SubstLookupRecord


def _context2(table: Any) -> Iterator[Raw]:
    classes = _Classes(table.ClassDef)
    for number, rules in enumerate(table.SubClassSet):
        first = classes.among(number, table.Coverage.glyphs)
        for rule in rules.SubClassRule if rules else ():
            input = [first] + [classes.of(c) for c in rule.Class]
            yield [], input, [], rule.SubstLookupRecord


def _context3(table: Any) -> Iterator[Raw]:
    yield [], [_set(c.glyphs) for c in table.Coverage], [], table.SubstLookupRecord


def _chain1(table: Any) -> Iterator[Raw]:
    for glyph, rules in zip(table.Coverage.glyphs, table.ChainSubRuleSet):
        for rule in rules.ChainSubRule if rules else ():
            yield (
                [_set([g]) for g in rule.Backtrack],
                [_set([glyph])] + [_set([g]) for g in rule.Input],
                [_set([g]) for g in rule.LookAhead],
                rule.SubstLookupRecord,
            )


def _chain2(table: Any) -> Iterator[Raw]:
    before = _Classes(table.BacktrackClassDef)
    inside = _Classes(table.InputClassDef)
    after = _Classes(table.LookAheadClassDef)
    for number, rules in enumerate(table.ChainSubClassSet):
        first = inside.among(number, table.Coverage.glyphs)
        for rule in rules.ChainSubClassRule if rules else ():
            yield (
                [before.of(c) for c in rule.Backtrack],
                [first] + [inside.of(c) for c in rule.Input],
                [after.of(c) for c in rule.LookAhead],
                rule.SubstLookupRecord,
            )


def _chain3(table: Any) -> Iterator[Raw]:
    yield (
        [_set(c.glyphs) for c in table.BacktrackCoverage],
        [_set(c.glyphs) for c in table.InputCoverage],
        [_set(c.glyphs) for c in table.LookAheadCoverage],
        table.SubstLookupRecord,
    )


# ---- the model -----------------------------------------------------------

Substitutions = Dict[str, Tuple[str, ...]]


class GsubModel:
    def __init__(self, font: Any) -> None:
        self._rules: List[List[Rule]] = []
        self._substitutions: List[Optional[Substitutions]] = []
        # Feature tag -> the lookups its records list (any script), sorted.
        self.features: Dict[str, List[int]] = {}
        if "GSUB" not in font:
            return
        gsub = font["GSUB"].table
        for number, lookup in enumerate(
            gsub.LookupList.Lookup if gsub.LookupList else []
        ):
            rules: List[Rule] = []
            maps: Optional[Substitutions] = {}
            for index, subtable in enumerate(lookup.SubTable):
                rules += subtable_rules(subtable, number, index)
                maps = _merge(maps, unwrap(subtable))
            self._rules.append(rules)
            self._substitutions.append(maps)
        found: Dict[str, Set[int]] = {}
        for record in gsub.FeatureList.FeatureRecord if gsub.FeatureList else []:
            found.setdefault(record.FeatureTag, set()).update(
                i for i in record.Feature.LookupListIndex if i < len(self._rules)
            )
        self.features = {tag: sorted(found[tag]) for tag in sorted(found)}

    def rules(self, lookup: int) -> List[Rule]:
        """The rules of a lookup in the order they are tried; [] for a lookup
        that is not contextual."""
        return self._rules[lookup] if 0 <= lookup < len(self._rules) else []

    def substitutions(self, lookup: int) -> Optional[Substitutions]:
        """What a single, multiple or alternate substitution lookup replaces
        each glyph by (the first subtable that has the glyph wins); None for
        any other kind."""
        if 0 <= lookup < len(self._substitutions):
            return self._substitutions[lookup]
        return None

    def lookup_count(self) -> int:
        return len(self._rules)

    def reachable(self, tags: Iterable[str]) -> Set[int]:
        """The lookups the features `tags` run, and those their rules call
        (and so on)."""
        todo = [i for tag in tags for i in self.features.get(tag, [])]
        seen: Set[int] = set()
        while todo:
            lookup = todo.pop()
            if lookup in seen:
                continue
            seen.add(lookup)
            for rule in self.rules(lookup):
                todo += [
                    called for _, called in rule.actions if called < len(self._rules)
                ]
        return seen

    def tags_of(self, lookup: int) -> List[str]:
        """The features that list `lookup` themselves."""
        return [tag for tag, lookups in self.features.items() if lookup in lookups]

    # ---- hidden rules ----------------------------------------------------

    def hidden_rules(self) -> List[Tuple[Rule, Rule]]:
        """(rule, earlier rule) for every rule of a lookup some feature
        reaches that an earlier rule of the same lookup covers: wherever the
        rule would fire the earlier one fires first, so it never does."""
        found: List[Tuple[Rule, Rule]] = []
        for lookup in sorted(self.reachable(self.features)):
            found += _hidden_in(self.rules(lookup))
        return found

    # ---- rules that claim one context -----------------------------------

    def conflicting_rules(self) -> List[Tuple[Rule, Rule]]:
        """(first, second) for rules of two lookups of one feature that match
        exactly the same context and substitute differently. The lookup with
        the lower index runs first."""
        found: List[Tuple[Rule, Rule]] = []
        seen: Set[Tuple[str, str]] = set()
        for lookups in self.features.values():
            by_context: Dict[Any, List[Rule]] = {}
            for lookup in lookups:
                for rule in self.rules(lookup):
                    by_context.setdefault(rule.context(), []).append(rule)
            for rules in by_context.values():
                for position, first in enumerate(rules):
                    for second in rules[position + 1 :]:
                        pair = (first.where(), second.where())
                        if (
                            first.lookup != second.lookup
                            and pair not in seen
                            and self._disagree(first, second)
                        ):
                            seen.add(pair)
                            found.append((first, second))
        return found

    def _effect(self, rule: Rule) -> Dict[Tuple[int, Optional[str]], Any]:
        """What a rule does, as far as it can be told without shaping: for
        each glyph its input can have at a position, what the lookup called
        there replaces it by. A lookup that is not a plain substitution
        stands for itself."""
        effect: Dict[Tuple[int, Optional[str]], Any] = {}
        for index, called in rule.actions:
            if index >= len(rule.input):
                continue
            replaced = self.substitutions(called)
            if replaced is None:
                effect.setdefault((index, None), called)
                continue
            for glyph, outputs in replaced.items():
                if rule.input[index].has(glyph):
                    effect.setdefault((index, glyph), outputs)
        return effect

    def _disagree(self, first: Rule, second: Rule) -> bool:
        one, other = self._effect(first), self._effect(second)
        return any(one[key] != other[key] for key in one.keys() & other.keys())

    # ---- lookups that choose ---------------------------------------------

    def choosing(self, differs: Callable[[str, str], bool]) -> List[int]:
        """The contextual lookups with a rule that calls a substitution
        replacing a glyph its input has by one that `differs` from it."""
        found = []
        for lookup, rules in enumerate(self._rules):
            if any(self._chooses(rule, differs) for rule in rules):
                found.append(lookup)
        return found

    def _chooses(self, rule: Rule, differs: Callable[[str, str], bool]) -> bool:
        for index, called in rule.actions:
            replaced = self.substitutions(called)
            if replaced is None or index >= len(rule.input):
                continue
            for glyph, outputs in replaced.items():
                if rule.input[index].has(glyph) and any(
                    differs(glyph, out) for out in outputs
                ):
                    return True
        return False


def _merge(maps: Optional[Substitutions], table: Any) -> Optional[Substitutions]:
    """Adds the substitutions of one subtable; None once a subtable is of a
    kind that is not a plain substitution."""
    if maps is None:
        return None
    if table.LookupType == SINGLE:
        found = {g: (o,) for g, o in table.mapping.items()}
    elif table.LookupType == MULTIPLE:
        found = {g: tuple(o) for g, o in table.mapping.items()}
    elif table.LookupType == ALTERNATE:
        found = {g: tuple(o) for g, o in table.alternates.items()}
    else:
        return None
    for glyph, outputs in found.items():
        maps.setdefault(glyph, outputs)
    return maps


def _hidden_in(rules: List[Rule]) -> List[Tuple[Rule, Rule]]:
    """The rules of one lookup, in order, that an earlier one covers. Earlier
    rules are found by a glyph of the rule's first input set: a rule that
    covers it must hold that glyph too."""
    found: List[Tuple[Rule, Rule]] = []
    by_glyph: Dict[str, List[int]] = {}
    wide: List[int] = []  # earlier rules whose first set is "all but ..."
    for number, rule in enumerate(rules):
        first = rule.input[0]
        if first.negated:
            candidates: Iterable[int] = range(number)
        else:
            candidates = sorted(by_glyph.get(min(first.glyphs), []) + wide)
        for earlier in candidates:
            if rules[earlier].covers(rule):
                found.append((rule, rules[earlier]))
                break
        if first.negated:
            wide.append(number)
        else:
            for glyph in first.glyphs:
                by_glyph.setdefault(glyph, []).append(number)
    return found
