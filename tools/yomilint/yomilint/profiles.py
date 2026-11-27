"""What differs between kinds of annotation: pinyin, zhuyin, furigana, ...

A profile knows how a reading is written. The checks and the resolvers know
nothing about pinyin; they ask the profile.
"""

from __future__ import annotations

import unicodedata
from typing import Dict, Optional

# Base letter -> the same letter with tones 1 to 4.
_TONES: Dict[str, str] = {
    "a": "āáǎà",
    "e": "ēéěè",
    "i": "īíǐì",
    "o": "ōóǒò",
    "u": "ūúǔù",
    "v": "ǖǘǚǜ",
}
# Letters written with a combining mark have no single code point per tone.
_COMBINING_TONES = ["̄", "́", "̌", "̀"]
_PLAIN = {"v": "ü", "eh": "ê"}


class Profile:
    """A kind of annotation. The base class accepts any reading as it is."""

    name = "generic"

    def normalize(self, reading: str) -> str:
        return unicodedata.normalize("NFC", reading)

    def is_annotation_char(self, char: str) -> bool:
        """Whether `char` can be part of an annotation (and not the base)."""
        return True

    def decode_letter(self, encoded: str, encoding: Optional[str]) -> Optional[str]:
        """The letter a glyph name stands for, or None when it is none."""
        return encoded if len(encoded) == 1 else None


class PinyinProfile(Profile):
    name = "pinyin"

    def is_annotation_char(self, char: str) -> bool:
        if unicodedata.combining(char):
            return True
        return unicodedata.name(char, "").startswith("LATIN")

    def decode_letter(self, encoded: str, encoding: Optional[str]) -> Optional[str]:
        if encoding != "tone-number":
            return super().decode_letter(encoded, encoding)
        stem, tone = encoded, 0
        if encoded[-1:] in "1234" and len(encoded) > 1:
            stem, tone = encoded[:-1], int(encoded[-1])
        if tone == 0:
            return _PLAIN.get(stem, stem if len(stem) == 1 else None)
        if stem in _TONES:
            return _TONES[stem][tone - 1]
        # ê, m and n take a combining tone mark.
        letter = _PLAIN.get(stem, stem)
        if len(letter) != 1:
            return None
        return unicodedata.normalize("NFC", letter + _COMBINING_TONES[tone - 1])


PROFILES = {profile.name: profile for profile in (Profile(), PinyinProfile())}


def get_profile(name: str) -> Profile:
    if name not in PROFILES:
        known = ", ".join(sorted(PROFILES))
        raise ValueError(f"unknown profile {name!r} (known: {known})")
    return PROFILES[name]
