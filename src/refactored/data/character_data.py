# -*- coding: utf-8 -*-
"""Character data management and classification."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Iterator, List, Optional, Protocol, Union

from .pinyin_data import PinyinDataManager, get_default_pinyin_manager


@dataclass(frozen=True)
class CharacterInfo:
    """Information about a Chinese character."""

    character: str
    pronunciations: List[str]

    @property
    def is_single_pronunciation(self) -> bool:
        """Check if character has single pronunciation."""
        return len(self.pronunciations) == 1

    @property
    def is_multiple_pronunciation(self) -> bool:
        """Check if character has multiple pronunciations."""
        return len(self.pronunciations) > 1

    @property
    def pronunciation_count(self) -> int:
        """Get number of pronunciations."""
        return len(self.pronunciations)

    def __iter__(self) -> Iterator[Union[str, List[str]]]:
        """Enable tuple unpacking for backward compatibility."""
        return iter((self.character, self.pronunciations))

    def __getitem__(self, index: int) -> Union[str, List[str]]:
        """Enable index access for backward compatibility."""
        if index == 0:
            return self.character
        elif index == 1:
            return self.pronunciations
        else:
            raise IndexError("CharacterInfo index out of range")


class CharacterClassifier(Protocol):
    """Protocol for character classification strategies."""

    def classify_character(self, char_info: CharacterInfo) -> bool:
        """Classify a character based on some criteria."""
        ...


class SinglePronunciationClassifier:
    """Classifier for characters with single pronunciation."""

    def classify_character(self, char_info: CharacterInfo) -> bool:
        """Check if character has single pronunciation."""
        return char_info.is_single_pronunciation


class MultiplePronunciationClassifier:
    """Classifier for characters with multiple pronunciations."""

    def classify_character(self, char_info: CharacterInfo) -> bool:
        """Check if character has multiple pronunciations."""
        return char_info.is_multiple_pronunciation


class CharacterDataManager:
    """Manages character data and provides classification services."""

    def __init__(self, pinyin_manager: Optional[PinyinDataManager] = None):
        """Initialize with optional pinyin data manager."""
        self._pinyin_manager = pinyin_manager or get_default_pinyin_manager()

    def get_character_info(self, character: str) -> Optional[CharacterInfo]:
        """Get character information."""
        pronunciations = self._pinyin_manager.get_pinyin(character)
        if pronunciations is None:
            return None
        return CharacterInfo(character=character, pronunciations=pronunciations)

    def iter_all_characters(self) -> Iterator[CharacterInfo]:
        """Memory-efficient iterator over all characters."""
        mappings = self._pinyin_manager.get_all_mappings()
        for character, pronunciations in mappings.items():
            yield CharacterInfo(character=character, pronunciations=pronunciations)

    def iter_characters_by_classifier(
        self, classifier: CharacterClassifier
    ) -> Iterator[CharacterInfo]:
        """Iterate over characters matching classification criteria."""
        for char_info in self.iter_all_characters():
            if classifier.classify_character(char_info):
                yield char_info

    def iter_single_pronunciation_characters(self) -> Iterator[CharacterInfo]:
        """Iterate over characters with single pronunciation."""
        classifier = SinglePronunciationClassifier()
        return self.iter_characters_by_classifier(classifier)

    def iter_multiple_pronunciation_characters(self) -> Iterator[CharacterInfo]:
        """Iterate over characters with multiple pronunciations."""
        classifier = MultiplePronunciationClassifier()
        return self.iter_characters_by_classifier(classifier)

    @lru_cache(maxsize=1)
    def get_single_pronunciation_characters(self) -> List[CharacterInfo]:
        """Get all characters with single pronunciation (cached)."""
        return list(self.iter_single_pronunciation_characters())

    @lru_cache(maxsize=1)
    def get_multiple_pronunciation_characters(self) -> List[CharacterInfo]:
        """Get all characters with multiple pronunciations (cached)."""
        return list(self.iter_multiple_pronunciation_characters())

    def get_statistics(self) -> dict:
        """Get character statistics."""
        total = 0
        single_count = 0
        multiple_count = 0

        for char_info in self.iter_all_characters():
            total += 1
            if char_info.is_single_pronunciation:
                single_count += 1
            else:
                multiple_count += 1

        return {
            "total_characters": total,
            "single_pronunciation": single_count,
            "multiple_pronunciation": multiple_count,
            "homograph_percentage": (
                round((multiple_count / total) * 100, 2) if total > 0 else 0
            ),
        }


# Global instance for backward compatibility
_default_character_manager: Optional[CharacterDataManager] = None


def get_default_character_manager() -> CharacterDataManager:
    """Get the default character data manager."""
    global _default_character_manager
    if _default_character_manager is None:
        _default_character_manager = CharacterDataManager()
    return _default_character_manager
