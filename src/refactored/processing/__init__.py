# -*- coding: utf-8 -*-
"""Processing module for performance optimization and monitoring."""

from __future__ import annotations

from .cache_manager import CacheManager, cached_function
from .gsub_table_generator import GSUBTableGenerator
from .optimized_utility import simplification_pronunciation
from .parallel_processor import ParallelProcessor, parallel_map
from .profiling import PerformanceProfiler, performance_monitor, profile_function

__all__ = [
    "PerformanceProfiler",
    "performance_monitor",
    "profile_function",
    "CacheManager",
    "cached_function",
    "ParallelProcessor",
    "parallel_map",
    "GSUBTableGenerator",
    "simplification_pronunciation",
]
