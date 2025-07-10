# -*- coding: utf-8 -*-
"""Advanced caching system for performance optimization."""

from __future__ import annotations

import pickle
import hashlib
import threading
from functools import wraps, lru_cache
from pathlib import Path
from typing import Any, Callable, Dict, Optional, TypeVar, Union
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..config import FontConstants, ProjectPaths

T = TypeVar('T')


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    value: Any
    created_at: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    def is_expired(self, ttl: timedelta) -> bool:
        """Check if cache entry is expired."""
        return datetime.now() - self.created_at > ttl
    
    def touch(self) -> None:
        """Update access information."""
        self.access_count += 1
        self.last_accessed = datetime.now()


class CacheManager:
    """Advanced cache manager with TTL, size limits, and persistence."""
    
    def __init__(
        self,
        max_size: int = FontConstants.LRU_CACHE_SIZE_XLARGE,
        default_ttl: Optional[timedelta] = None,
        enable_persistence: bool = True,
        cache_dir: Optional[Path] = None
    ):
        """Initialize cache manager."""
        self.max_size = max_size
        self.default_ttl = default_ttl or timedelta(hours=24)
        self.enable_persistence = enable_persistence
        
        if cache_dir is None:
            paths = ProjectPaths()
            self.cache_dir = paths.temp_dir / "cache"
        else:
            self.cache_dir = cache_dir
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        
        # Load persistent cache
        if self.enable_persistence:
            self._load_persistent_cache()
    
    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate cache key from function name and arguments."""
        # Create a hashable representation of args and kwargs
        key_data = (func_name, args, tuple(sorted(kwargs.items())))
        key_str = str(key_data)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _load_persistent_cache(self) -> None:
        """Load cache from persistent storage."""
        cache_file = self.cache_dir / "cache.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    self._cache = pickle.load(f)
                # Clean expired entries
                self._cleanup_expired()
            except (pickle.PickleError, EOFError, FileNotFoundError):
                # Cache file corrupted or missing, start fresh
                self._cache = {}
    
    def _save_persistent_cache(self) -> None:
        """Save cache to persistent storage."""
        if not self.enable_persistence:
            return
        
        cache_file = self.cache_dir / "cache.pkl"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(self._cache, f)
        except (pickle.PickleError, OSError):
            # Failed to save cache, continue without persistence
            pass
    
    def _cleanup_expired(self) -> None:
        """Remove expired cache entries."""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired(self.default_ttl)
        ]
        for key in expired_keys:
            del self._cache[key]
    
    def _evict_lru(self) -> None:
        """Evict least recently used entries when cache is full."""
        if len(self._cache) <= self.max_size:
            return
        
        # Sort by last accessed time (oldest first)
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda item: item[1].last_accessed or item[1].created_at
        )
        
        # Remove oldest entries
        excess_count = len(self._cache) - self.max_size
        for i in range(excess_count):
            key, _ = sorted_entries[i]
            del self._cache[key]
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if not entry.is_expired(self.default_ttl):
                    entry.touch()
                    return entry.value
                else:
                    # Remove expired entry
                    del self._cache[key]
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[timedelta] = None) -> None:
        """Set value in cache."""
        with self._lock:
            # Clean up expired entries
            self._cleanup_expired()
            
            # Evict LRU if necessary
            self._evict_lru()
            
            # Add new entry
            entry = CacheEntry(
                value=value,
                created_at=datetime.now(),
                last_accessed=datetime.now()
            )
            self._cache[key] = entry
            
            # Save to persistent storage
            self._save_persistent_cache()
    
    def invalidate(self, pattern: Optional[str] = None) -> None:
        """Invalidate cache entries matching pattern."""
        with self._lock:
            if pattern is None:
                self._cache.clear()
            else:
                keys_to_remove = [
                    key for key in self._cache.keys()
                    if pattern in key
                ]
                for key in keys_to_remove:
                    del self._cache[key]
            
            self._save_persistent_cache()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_entries = len(self._cache)
            total_accesses = sum(entry.access_count for entry in self._cache.values())
            
            if self._cache:
                avg_accesses = total_accesses / total_entries
                oldest_entry = min(self._cache.values(), key=lambda e: e.created_at)
                newest_entry = max(self._cache.values(), key=lambda e: e.created_at)
            else:
                avg_accesses = 0
                oldest_entry = None
                newest_entry = None
            
            return {
                'total_entries': total_entries,
                'max_size': self.max_size,
                'usage_percentage': (total_entries / self.max_size) * 100,
                'total_accesses': total_accesses,
                'average_accesses_per_entry': avg_accesses,
                'oldest_entry_age': (
                    datetime.now() - oldest_entry.created_at
                    if oldest_entry else None
                ),
                'newest_entry_age': (
                    datetime.now() - newest_entry.created_at
                    if newest_entry else None
                )
            }


# Global cache manager instance
_global_cache_manager: Optional[CacheManager] = None


def get_global_cache_manager() -> CacheManager:
    """Get or create global cache manager."""
    global _global_cache_manager
    if _global_cache_manager is None:
        _global_cache_manager = CacheManager()
    return _global_cache_manager


def cached_function(
    ttl: Optional[timedelta] = None,
    cache_manager: Optional[CacheManager] = None,
    key_func: Optional[Callable] = None
):
    """Decorator for caching function results with advanced features."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache_mgr = cache_manager or get_global_cache_manager()
        
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache_mgr._generate_key(func.__name__, args, kwargs)
            
            # Try to get from cache
            cached_result = cache_mgr.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Compute result and cache it
            result = func(*args, **kwargs)
            cache_mgr.set(cache_key, result, ttl)
            
            return result
        
        # Add cache management methods to the wrapper
        wrapper.cache_invalidate = lambda pattern=None: cache_mgr.invalidate(pattern)
        wrapper.cache_stats = lambda: cache_mgr.get_stats()
        
        return wrapper
    return decorator


class SmartCache:
    """Smart cache with automatic invalidation based on file modifications."""
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        """Initialize smart cache."""
        self.cache_manager = cache_manager or get_global_cache_manager()
        self.file_mtimes: Dict[str, float] = {}
    
    def _get_file_mtime(self, file_path: Union[str, Path]) -> float:
        """Get file modification time."""
        path = Path(file_path)
        return path.stat().st_mtime if path.exists() else 0.0
    
    def _check_file_dependencies(self, dependencies: list[Union[str, Path]]) -> bool:
        """Check if any file dependencies have been modified."""
        for dep in dependencies:
            dep_str = str(dep)
            current_mtime = self._get_file_mtime(dep)
            
            if dep_str in self.file_mtimes:
                if current_mtime > self.file_mtimes[dep_str]:
                    return True  # File was modified
            else:
                self.file_mtimes[dep_str] = current_mtime
        
        return False
    
    def cached_with_file_deps(
        self,
        dependencies: list[Union[str, Path]],
        ttl: Optional[timedelta] = None
    ):
        """Decorator for caching with file dependency checking."""
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            def wrapper(*args, **kwargs) -> T:
                # Check if dependencies have changed
                if self._check_file_dependencies(dependencies):
                    # Invalidate cache for this function
                    pattern = func.__name__
                    self.cache_manager.invalidate(pattern)
                    
                    # Update file modification times
                    for dep in dependencies:
                        dep_str = str(dep)
                        self.file_mtimes[dep_str] = self._get_file_mtime(dep)
                
                # Use regular caching
                cache_key = self.cache_manager._generate_key(func.__name__, args, kwargs)
                cached_result = self.cache_manager.get(cache_key)
                
                if cached_result is not None:
                    return cached_result
                
                result = func(*args, **kwargs)
                self.cache_manager.set(cache_key, result, ttl)
                
                return result
            return wrapper
        return decorator


# Optimized lru_cache variants for different use cases
def fast_lru_cache(maxsize: int = FontConstants.LRU_CACHE_SIZE_MEDIUM):
    """Fast LRU cache for frequently called functions."""
    return lru_cache(maxsize=maxsize)


def memory_efficient_cache(maxsize: int = FontConstants.LRU_CACHE_SIZE_SMALL):
    """Memory-efficient cache for large objects."""
    return lru_cache(maxsize=maxsize)


def persistent_cache(ttl_hours: int = 24):
    """Persistent cache that survives across program runs."""
    return cached_function(ttl=timedelta(hours=ttl_hours))