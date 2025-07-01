# -*- coding: utf-8 -*-
"""
Mengshen Pinyin Font - Package for generating Chinese fonts with pinyin annotations.

This package provides tools for creating fonts that display pinyin above Chinese
characters, with special support for homographs (多音字) - characters that have
different pronunciations depending on context.
"""

from __future__ import annotations

__version__ = "2.0.0"
__author__ = "Mengshen Font Project"
__description__ = "Chinese font generator with automatic pinyin annotations"

# Package-level imports for convenience
from .config import FontType, FontConfig
from .font import FontBuilder
from .cli import main

__all__ = [
    "FontType",
    "FontConfig", 
    "FontBuilder",
    "main"
]