# -*- coding: utf-8 -*-
#!/usr/bin/env python

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Phrase:
    """Represents a Chinese phrase with its pinyin pronunciation."""
    phrase: str
    string_pinyin: str
    normal_pronunciations: Optional[list[str]] = None
    
    def __post_init__(self) -> None:
        """Clean up string_pinyin after initialization."""
        self.string_pinyin = self.string_pinyin.rstrip('\n')
        if self.normal_pronunciations is None:
            self.normal_pronunciations = []

    def get_name(self) -> str:
        return self.phrase

    def get_string_pinyin(self) -> str:
        return self.string_pinyin
    
    def get_list_pinyin(self) -> list[str]:
        return self.string_pinyin.split('/')

    def get_normal_pronunciations(self) -> list[str]:
        return self.normal_pronunciations