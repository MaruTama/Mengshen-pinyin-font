# -*- coding: utf-8 -*-
"""
Mengshen Font Utilities Module

This module contains utility functions for handling Chinese characters,
pinyin processing, and font operations.
"""

from __future__ import annotations

from typing import Any, Callable, Union

from .pinyin_utils import PINYIN_TONE_TO_NUMERIC, simplification_pronunciation
from .shell_utils import SecurityError, ShellExecutor, safe_command_execution

# Dynamic import return type
ModuleAttribute = Union[type, object, Callable]


# Use lazy imports to avoid circular dependencies
def __getattr__(name: str) -> Any:
    """Lazy import for circular dependency resolution."""
    if name in [
        "get_multiple_pronunciation_characters",
        "get_single_pronunciation_characters",
        "iter_multiple_pronunciation_characters",
        "iter_single_pronunciation_characters",
    ]:
        return locals()[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    "PINYIN_TONE_TO_NUMERIC",
    "simplification_pronunciation",
    "ShellExecutor",
    "safe_command_execution",
    "SecurityError",
]
