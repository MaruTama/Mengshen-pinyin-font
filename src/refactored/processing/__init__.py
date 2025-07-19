# -*- coding: utf-8 -*-
"""Processing module for GSUB table generation and basic utilities."""

from __future__ import annotations

from ..utils.pinyin_utils import simplification_pronunciation
from .gsub_table_generator import GSUBTableGenerator

__all__ = [
    "GSUBTableGenerator",
    "simplification_pronunciation",
]
