"""Readers of dictionaries (character -> readings) and phrase lists."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterator, List, Tuple

Dictionary = Dict[str, List[str]]


@dataclass(frozen=True)
class Phrase:
    """A text and the reading each of its characters should show."""

    text: str
    readings: List[str]
    line: int

    def __hash__(self) -> int:
        return hash((self.text, tuple(self.readings), self.line))


class DataError(ValueError):
    """A data file has a line that cannot be read."""


def _lines(path: Path) -> Iterator[Tuple[int, str]]:
    with open(path, encoding="utf-8") as lines:
        for number, line in enumerate(lines, 1):
            line = line.strip()
            if line and not line.startswith("#"):
                yield number, line


def _mengshen_dictionary(path: Path) -> Dictionary:
    # `U+7740: zhe,zhuó  #着`
    dictionary: Dictionary = {}
    for number, line in _lines(path):
        entry = line.split("#")[0].strip()
        code, _, readings = entry.partition(":")
        try:
            char = chr(int(code.strip().removeprefix("U+"), 16))
        except ValueError as error:
            raise DataError(f"{path}:{number}: no code point in {line!r}") from error
        dictionary[char] = [r.strip() for r in readings.split(",") if r.strip()]
    return dictionary


def _mengshen_phrases(path: Path) -> List[Phrase]:
    # `着手: zhuó/shǒu, 背着手: bèi/zhe/shǒu`
    phrases: List[Phrase] = []
    for number, line in _lines(path):
        for part in line.split(","):
            text, separator, readings = part.partition(":")
            if not separator:
                raise DataError(f"{path}:{number}: no readings in {part.strip()!r}")
            phrases.append(
                Phrase(text.strip(), [r.strip() for r in readings.split("/")], number)
            )
    return phrases


def read_dictionary(path: Path, format: str) -> Dictionary:
    if format != "mengshen":
        raise DataError(f"unknown dictionary format {format!r}")
    return _mengshen_dictionary(Path(path))


def read_phrases(path: Path, format: str) -> List[Phrase]:
    if format != "mengshen":
        raise DataError(f"unknown phrase format {format!r}")
    return _mengshen_phrases(Path(path))
