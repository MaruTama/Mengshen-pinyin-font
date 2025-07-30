# -*- coding: utf-8 -*-
"""OpenType table processing module."""

from __future__ import annotations

from .cmap_manager import CmapTableManager
from .gsub_table_generator import GSUBTableGenerator

__all__ = [
    "GSUBTableGenerator",
    "CmapTableManager",
]
