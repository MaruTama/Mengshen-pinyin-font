"""The spec file (`yomilint.toml`): what the font under test should do."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .profiles import PROFILES

# The GSUB features a shaper runs without being asked: HarfBuzz's common and
# horizontal ones (ccmp, locl, rlig, calt, clig, liga, rclt), `rvrn`, the
# vertical `vert` and `vrt2`, and the bidirectional ones. `aalt`, `salt` and
# the stylistic sets are chosen by the user, so they are not here.
DEFAULT_FEATURES = (
    "ccmp",
    "locl",
    "rvrn",
    "rlig",
    "calt",
    "clig",
    "liga",
    "rclt",
    "vert",
    "vrt2",
    "ltra",
    "ltrm",
    "rtla",
    "rtlm",
)


@dataclass
class Source:
    """A data file and the format it is written in."""

    path: Path
    format: str


@dataclass
class Spec:
    directory: Path
    profile: str = "generic"
    position: str = "top"
    resolver_kind: str = "components"
    # `names`: glyph name -> (?P<base>) and (?P<index>), index 0 being bare.
    name_pattern: Optional[str] = None
    # `components`: glyph name of a part -> (?P<letter>).
    letter_pattern: Optional[str] = None
    letter_encoding: Optional[str] = None
    dictionary: Optional[Source] = None
    phrases: List[Source] = field(default_factory=list)
    # The variation selector of the bare glyph; reading n is at base + n.
    selector_base: Optional[int] = None
    # The least distance between the character and its annotation.
    min_gap: float = 0
    # How far the middle of the annotation may be from the middle of the
    # advance, as a part of the em (unitsPerEm).
    center_tolerance: float = 0.01
    # How far an annotation's baseline may be from the font's usual one, as a
    # part of the em.
    baseline_tolerance: float = 0.001
    # The smallest an annotation may be drawn, relative to the largest.
    min_scale: float = 0.6
    glyph_headroom: int = 500
    # The features that are on without the user choosing them.
    default_features: Tuple[str, ...] = DEFAULT_FEATURES
    # A file of known findings, which do not fail a run.
    baseline: Optional[Path] = None


class SpecError(ValueError):
    """The spec file cannot be used; the message says why."""


def _source(table: Dict[str, Any], directory: Path, what: str) -> Source:
    if "path" not in table:
        raise SpecError(f"[{what}] needs a path")
    return Source(directory / table["path"], table.get("format", "mengshen"))


def _in_range(
    value: Any,
    key: str,
    low: float,
    high: float,
    low_open: bool = False,
    high_open: bool = False,
) -> None:
    """Refuses a [geometry] value outside (or at the open end of) its range:
    the tolerances are parts of the em, so `20` (units) must not pass."""
    ok = (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and (value > low if low_open else value >= low)
        and (value < high if high_open else value <= high)
    )
    if not ok:
        left = "(" if low_open else "["
        right = ")" if high_open else "]"
        raise SpecError(
            f"[geometry] {key} = {value!r} must be a number in "
            f"{left}{low:g}, {high:g}{right}"
            + (" (a part of the em, not font units)" if key != "min_scale" else "")
        )


def _tags(value: Any) -> Tuple[str, ...]:
    """The feature tags of `[context] default_features`: four printable ASCII
    characters each."""
    ok = isinstance(value, list) and all(
        isinstance(tag, str)
        and len(tag) == 4
        and all(" " <= char <= "~" for char in tag)
        for tag in value
    )
    if not ok:
        raise SpecError(
            f"[context] default_features = {value!r} must be a list of "
            "four-letter feature tags"
        )
    return tuple(value)


def load_spec(path: Path) -> Spec:
    path = Path(path)
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise SpecError(f"cannot read {path}: {error}") from error
    directory = path.parent
    resolver = data.get("resolver", {})
    letters = resolver.get("letters", {})
    spec = Spec(
        directory=directory,
        profile=data.get("font", {}).get("profile", "generic"),
        position=data.get("annotation", {}).get("position", "top"),
        resolver_kind=resolver.get("kind", "components"),
        name_pattern=resolver.get("pattern"),
        letter_pattern=letters.get("pattern"),
        letter_encoding=letters.get("encoding"),
        selector_base=data.get("selectors", {}).get("base"),
        min_gap=data.get("geometry", {}).get("min_gap", 0),
        center_tolerance=data.get("geometry", {}).get("center_tolerance", 0.01),
        baseline_tolerance=data.get("geometry", {}).get("baseline_tolerance", 0.001),
        min_scale=data.get("geometry", {}).get("min_scale", 0.6),
        glyph_headroom=data.get("limits", {}).get("glyph_headroom", 500),
    )
    if "default_features" in data.get("context", {}):
        spec.default_features = _tags(data["context"]["default_features"])
    if "path" in data.get("ignore", {}):
        spec.baseline = directory / data["ignore"]["path"]
    _in_range(spec.center_tolerance, "center_tolerance", 0, 1, high_open=True)
    _in_range(spec.baseline_tolerance, "baseline_tolerance", 0, 1, high_open=True)
    _in_range(spec.min_scale, "min_scale", 0, 1, low_open=True)
    if spec.profile not in PROFILES:
        known = ", ".join(sorted(PROFILES))
        raise SpecError(f"[font] profile {spec.profile!r} is not known ({known})")
    if spec.position not in ("top", "bottom", "left", "right"):
        raise SpecError(f"[annotation] position {spec.position!r} is not a side")
    if spec.resolver_kind not in ("components", "names"):
        raise SpecError(f"[resolver] kind {spec.resolver_kind!r} is not known")
    if spec.resolver_kind == "names" and not spec.name_pattern:
        raise SpecError('[resolver] kind = "names" needs a pattern')
    if "dictionary" in data:
        spec.dictionary = _source(data["dictionary"], directory, "dictionary")
    spec.phrases = [_source(t, directory, "phrases") for t in data.get("phrases", [])]
    return spec
