# -*- coding: utf-8 -*-
# !/usr/bin/env python

from __future__ import annotations

from functools import lru_cache

from .pinyin_utils import PINYIN_TONE_TO_NUMERIC


# ピンイン表記の簡略化、e.g.: wěi -> we3i
@lru_cache(maxsize=1024)
def simplification_pronunciation(pronunciation: str) -> str:
    """Simplify pinyin pronunciation with caching for performance."""
    return "".join([PINYIN_TONE_TO_NUMERIC[c] for c in pronunciation])
