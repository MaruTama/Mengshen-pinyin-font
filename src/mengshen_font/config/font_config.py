# -*- coding: utf-8 -*-
"""Font configuration management with type safety."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Dict


class FontType(IntEnum):
    """Font type enumeration for type safety."""
    HAN_SERIF = 1
    HANDWRITTEN = 2


@dataclass(frozen=True)
class PinyinCanvas:
    """Pinyin canvas configuration."""
    width: float
    height: float
    base_line: float
    tracking: float


@dataclass(frozen=True) 
class HanziCanvas:
    """Hanzi canvas configuration."""
    width: float
    height: float


@dataclass(frozen=True)
class FontMetadata:
    """Font metadata configuration."""
    pinyin_canvas: PinyinCanvas
    hanzi_canvas: HanziCanvas


class FontConfig:
    """Centralized font configuration management."""
    
    # Font style configurations
    _CONFIGS: Dict[FontType, FontMetadata] = {
        FontType.HAN_SERIF: FontMetadata(
            pinyin_canvas=PinyinCanvas(
                width=1000.0,
                height=1280.0,
                base_line=950.0,
                tracking=10.0
            ),
            hanzi_canvas=HanziCanvas(
                width=880.0,
                height=880.0
            )
        ),
        FontType.HANDWRITTEN: FontMetadata(
            pinyin_canvas=PinyinCanvas(
                width=1000.0,
                height=1280.0,
                base_line=950.0,
                tracking=10.0
            ),
            hanzi_canvas=HanziCanvas(
                width=880.0,
                height=880.0
            )
        )
    }
    
    @classmethod
    def get_config(cls, font_type: FontType) -> FontMetadata:
        """Get configuration for specified font type."""
        if font_type not in cls._CONFIGS:
            raise ValueError(f"Unsupported font type: {font_type}")
        return cls._CONFIGS[font_type]
    
    @classmethod
    def get_pinyin_canvas(cls, font_type: FontType) -> PinyinCanvas:
        """Get pinyin canvas configuration for font type."""
        return cls.get_config(font_type).pinyin_canvas
    
    @classmethod
    def get_hanzi_canvas(cls, font_type: FontType) -> HanziCanvas:
        """Get hanzi canvas configuration for font type."""
        return cls.get_config(font_type).hanzi_canvas


# Backward compatibility constants
HAN_SERIF_TYPE = FontType.HAN_SERIF
HANDWRITTEN_TYPE = FontType.HANDWRITTEN

# Legacy metadata access (deprecated - use FontConfig class instead)
METADATA_FOR_PINYIN = {
    FontType.HAN_SERIF: FontConfig.get_config(FontType.HAN_SERIF),
    FontType.HANDWRITTEN: FontConfig.get_config(FontType.HANDWRITTEN)
}