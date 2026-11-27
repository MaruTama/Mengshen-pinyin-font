"""Shared helpers: build a test font with its spec, and lint it."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import pytest

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from fontmaker import (  # noqa: E402
    FontPlan,
    make_font,
    write_dictionary,
    write_phrases,
)

SPEC = """
[font]
profile = "pinyin"

[annotation]
position = "top"

[resolver]
kind = "{kind}"
pattern = '^(?P<base>.+)\\.ss(?P<index>\\d{{2}})$'

[resolver.letters]
pattern = '^py_alphabet_(?P<letter>.+)$'
encoding = "tone-number"

[dictionary]
path = "dictionary.txt"
format = "mengshen"

[[phrases]]
path = "phrases.txt"
format = "mengshen"

[selectors]
base = 0xE01E0

[limits]
glyph_headroom = {headroom}
"""

PHRASES = ["着手: zhuó/shǒu, 背着手: bèi/zhe/shǒu"]


class Project:
    """A font, its dictionary, its phrases and its spec in one directory."""

    def __init__(
        self,
        directory: Path,
        plan: Optional[FontPlan] = None,
        phrases: Sequence[str] = PHRASES,
        dictionary: Optional[Dict[str, List[str]]] = None,
        kind: str = "components",
        headroom: int = 500,
    ) -> None:
        self.font = make_font(directory / "font.ttf", plan)
        write_dictionary(directory / "dictionary.txt", dictionary)
        write_phrases(directory / "phrases.txt", phrases)
        self.spec = directory / "yomilint.toml"
        self.spec.write_text(
            SPEC.format(kind=kind, headroom=headroom), encoding="utf-8"
        )

    def findings(self) -> List[str]:
        """The ids of the checks that found something, one per finding."""
        from yomilint.runner import run

        return [finding.check for finding in run(self.font, self.spec)]


@pytest.fixture
def project(tmp_path: Path):
    def build(**options) -> Project:
        return Project(tmp_path, **options)

    return build
