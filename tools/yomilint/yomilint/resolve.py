"""Which reading a glyph shows.

Shaping gives glyphs, and the checks need readings. A resolver answers
"what does this glyph say above (or beside) its character": from the parts
the glyph is made of, or from its name.
"""

from __future__ import annotations

import re
from typing import List, Optional, Pattern, Tuple

from .font import FontUnderTest, Part
from .profiles import Profile, get_profile
from .readers import Dictionary
from .spec import Spec


class Resolver:
    def reading(self, glyph: str) -> Optional[str]:
        """The reading `glyph` shows, or None when it shows none."""
        raise NotImplementedError


class ComponentsResolver(Resolver):
    """Reads the annotation off the glyph's parts: every part that is a
    letter, in the order it is drawn."""

    def __init__(
        self,
        font: FontUnderTest,
        profile: Profile,
        position: str,
        letter_pattern: Optional[str],
        letter_encoding: Optional[str],
    ) -> None:
        self.font = font
        self.profile = profile
        self.vertical = position in ("left", "right")
        self.letter_pattern: Optional[Pattern[str]] = (
            re.compile(letter_pattern) if letter_pattern else None
        )
        self.letter_encoding = letter_encoding

    def letter(self, glyph: str) -> Optional[str]:
        """The letter the part `glyph` is: by the cmap, then by its name."""
        chars = self.font.chars_of.get(glyph)
        if chars is not None:
            letters = [c for c in chars if self.profile.is_annotation_char(c)]
            return letters[0] if letters else None
        if self.letter_pattern is not None:
            match = self.letter_pattern.match(glyph)
            if match:
                return self.profile.decode_letter(
                    match.group("letter"), self.letter_encoding
                )
        return None

    def split(self, glyph: str) -> Tuple[List[Part], List[Tuple[Part, str]]]:
        """The parts of `glyph` that draw the character, and those that
        draw the annotation, each with its letter."""
        base: List[Part] = []
        annotation: List[Tuple[Part, str]] = []
        for part in self.font.parts(glyph):
            letter = self.letter(part.glyph)
            if letter is None:
                base.append(part)
            else:
                annotation.append((part, letter))
        return base, annotation

    def reading(self, glyph: str) -> Optional[str]:
        _, annotation = self.split(glyph)
        if not annotation:
            return None
        # Left to right, or top to bottom beside the character.
        annotation.sort(key=lambda item: -item[0].y if self.vertical else item[0].x)
        return self.profile.normalize("".join(letter for _, letter in annotation))


class NamesResolver(Resolver):
    """Reads the glyph name: `<base>.ss02` is the second reading the
    dictionary gives the character of `<base>`, and index 0 is the bare one."""

    def __init__(
        self, font: FontUnderTest, profile: Profile, pattern: str, dictionary: Dictionary
    ) -> None:
        self.font = font
        self.profile = profile
        self.pattern = re.compile(pattern)
        self.dictionary = dictionary

    def reading(self, glyph: str) -> Optional[str]:
        match = self.pattern.match(glyph)
        # A name without the suffix is the default glyph: the first reading.
        base, index = (match.group("base"), int(match.group("index"))) if match else (glyph, 1)
        # Of the characters mapped to the glyph, the one the dictionary has.
        readings: List[str] = []
        for char in self.font.chars_of.get(base, []):
            if char in self.dictionary:
                readings = self.dictionary[char]
                break
        if index == 0 or index > len(readings):
            return None
        return self.profile.normalize(readings[index - 1])


def make_resolver(
    spec: Spec,
    font: FontUnderTest,
    dictionary: Optional[Dictionary] = None,
    kind: Optional[str] = None,
) -> Resolver:
    """The resolver the spec asks for, or the one of `kind`."""
    profile = get_profile(spec.profile)
    kind = kind or spec.resolver_kind
    if kind == "names":
        if dictionary is None:
            from .readers import read_dictionary

            if spec.dictionary is None:
                raise ValueError("the names resolver needs a dictionary")
            dictionary = read_dictionary(spec.dictionary.path, spec.dictionary.format)
        if not spec.name_pattern:
            raise ValueError("the names resolver needs [resolver] pattern")
        return NamesResolver(font, profile, spec.name_pattern, dictionary)
    return ComponentsResolver(
        font, profile, spec.position, spec.letter_pattern, spec.letter_encoding
    )
