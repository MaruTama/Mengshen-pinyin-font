"""Loads a font and its spec, and runs the checks."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Set

from .checks import CHECKS, ERROR, Context, Finding
from .font import FontUnderTest
from .profiles import get_profile
from .readers import Phrase, read_dictionary, read_phrases
from .resolve import make_resolver
from .spec import Spec, load_spec


def build_context(font_path: Path, spec: Spec) -> Context:
    font = FontUnderTest(font_path)
    dictionary = {}
    if spec.dictionary is not None:
        dictionary = read_dictionary(spec.dictionary.path, spec.dictionary.format)
    phrases: List[Phrase] = []
    for source in spec.phrases:
        phrases += read_phrases(source.path, source.format)
    resolver = make_resolver(spec, font, dictionary)
    # The other way of reading a glyph, when the spec describes it too.
    second = None
    if spec.resolver_kind == "components" and spec.name_pattern and dictionary:
        second = make_resolver(spec, font, dictionary, kind="names")
    elif spec.resolver_kind == "names" and spec.letter_pattern:
        second = make_resolver(spec, font, dictionary, kind="components")
    return Context(
        font=font,
        spec=spec,
        profile=get_profile(spec.profile),
        dictionary=dictionary,
        phrases=phrases,
        resolver=resolver,
        second_resolver=second,
    )


def selected(select: Optional[str]) -> Set[str]:
    """The ids of the checks a run with `select` runs."""
    return {c.id for c in CHECKS if not select or c.id.startswith(select)}


def run(
    font_path: Path, spec_path: Path, select: Optional[str] = None
) -> List[Finding]:
    """Every finding of the checks whose id starts with `select` (all of
    them without it), in the order the checks are registered."""
    context = build_context(Path(font_path), load_spec(Path(spec_path)))
    findings: List[Finding] = []
    for check in CHECKS:
        if select and not check.id.startswith(select):
            continue
        try:
            findings += list(check.run(context))
        except Exception as error:  # a broken font must not hide the rest
            findings.append(
                Finding(
                    check.id,
                    ERROR,
                    "font",
                    f"the check could not run: {type(error).__name__}: {error}",
                )
            )
    return findings
