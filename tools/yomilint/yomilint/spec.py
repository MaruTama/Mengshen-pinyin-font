"""The spec file (`yomilint.toml`): what the font under test should do."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .profiles import PROFILES


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
    # A file of known findings, which do not fail a run.
    baseline: Optional[Path] = None


class SpecError(ValueError):
    """The spec file cannot be used; the message says why."""


def _source(table: Dict[str, Any], directory: Path, what: str) -> Source:
    if "path" not in table:
        raise SpecError(f"[{what}] needs a path")
    return Source(directory / table["path"], table.get("format", "mengshen"))


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
    if "path" in data.get("ignore", {}):
        spec.baseline = directory / data["ignore"]["path"]
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
