# -*- coding: utf-8 -*-
"""
Mengshen Pinyin Font - Package for generating Chinese fonts with pinyin annotations.

This package provides tools for creating fonts that display pinyin above Chinese
characters, with special support for homographs (多音字) - characters that have
different pronunciations depending on context.
"""

from __future__ import annotations

from .utils.version_utils import get_project_version

__version__ = get_project_version()
__author__ = "Mengshen Font Project"
__description__ = "Chinese font generator with automatic pinyin annotations"

from .cli import main

# Package-level imports for convenience
from .config import FontConfig, FontType
from .generation import FontBuilder

__all__ = ["FontType", "FontConfig", "FontBuilder", "main"]
