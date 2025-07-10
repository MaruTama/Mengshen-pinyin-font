# -*- coding: utf-8 -*-
"""Performance-optimized utility functions for font generation."""

from __future__ import annotations

from functools import lru_cache
from typing import Iterator, List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from ..config import FontConstants
from ..data import CharacterDataManager, get_default_character_manager
from .cache_manager import cached_function, persistent_cache
from .profiling import profile_function, performance_monitor
from .parallel_processor import parallel_map, FontProcessingOptimizer


# Simplified alphabet mapping for pinyin conversion
SIMPLED_ALPHABET = {
    "a":"a", "ā":"a1", "á":"a2", "ǎ":"a3", "à":"a4",
    "b":"b",
    "c":"c",
    "d":"d",
    "e":"e", "ē":"e1", "é":"e2", "ě":"e3", "è":"e4",
    "f":"f",
    "g":"g",
    "h":"h",
    "i":"i", "ī":"i1", "í":"i2", "ǐ":"i3", "ì":"i4",
    "j":"j",
    "k":"k",
    "l":"l",
    "m":"m", "m̄":"m1", "ḿ":"m2", "m̀":"m4",
    "n":"n",           "ń":"n2", "ň":"n3", "ǹ":"n4",
    "o":"o", "ō":"o1", "ó":"o2", "ǒ":"o3", "ò":"o4",
    "p":"p",
    "q":"q",
    "r":"r",
    "s":"s",
    "t":"t",
    "u":"u", "ū":"u1", "ú":"u2" ,"ǔ":"u3", "ù":"u4", "ü":"v", "ǖ":"v1", "ǘ":"v2", "ǚ":"v3", "ǜ":"v4",
    "v":"v",
    "w":"w",
    "x":"x",
    "y":"y",
    "z":"z"
}


@lru_cache(maxsize=512)
def simplification_pronunciation(pronunciation: str) -> str:
    """Simplify pinyin pronunciation with caching for performance."""
    try:
        return "".join([SIMPLED_ALPHABET[c] for c in pronunciation])
    except KeyError as e:
        # Handle missing characters - fallback to original character
        result = []
        for c in pronunciation:
            result.append(SIMPLED_ALPHABET.get(c, c))
        print(f"DEBUG: simplification_pronunciation fallback for '{pronunciation}' -> {''.join(result)}")
        return "".join(result)


# Global cmap table for legacy compatibility
_cmap_table: Dict[str, str] = {}

def set_cmap_table(cmap_table: Dict[str, str]) -> None:
    """Set global cmap table for utility functions."""
    global _cmap_table
    _cmap_table = cmap_table

def get_cmap_table() -> Dict[str, str]:
    """Get global cmap table."""
    return _cmap_table


@dataclass(frozen=True)
class OptimizedHanziPinyin:
    """Optimized version of HanziPinyin with better performance characteristics."""
    character: str
    pronunciations: tuple[str, ...]  # Use tuple for immutability and hashability
    
    def __post_init__(self):
        """Validate data after initialization."""
        if not self.character:
            raise ValueError("Character cannot be empty")
        if not self.pronunciations:
            raise ValueError("Pronunciations cannot be empty")
    
    @property
    def is_single_pronunciation(self) -> bool:
        """Check if the character has only one pronunciation."""
        return len(self.pronunciations) == 1
    
    @property
    def is_multiple_pronunciation(self) -> bool:
        """Check if the character has multiple pronunciations."""
        return len(self.pronunciations) > 1
    
    def __iter__(self):
        """Enable tuple unpacking: hanzi, pinyins = hanzi_pinyin_obj"""
        return iter((self.character, list(self.pronunciations)))
    
    def __getitem__(self, index: int):
        """Enable index access for backward compatibility."""
        if index == 0:
            return self.character
        elif index == 1:
            return list(self.pronunciations)
        else:
            raise IndexError("OptimizedHanziPinyin index out of range")


# Pre-compiled pronunciation simplification mapping for performance
SIMPLIFIED_ALPHABET = {
    "a": "a", "ā": "a1", "á": "a2", "ǎ": "a3", "à": "a4",
    "b": "b", "c": "c", "d": "d",
    "e": "e", "ē": "e1", "é": "e2", "ě": "e3", "è": "e4",
    "f": "f", "g": "g", "h": "h",
    "i": "i", "ī": "i1", "í": "i2", "ǐ": "i3", "ì": "i4",
    "j": "j", "k": "k", "l": "l",
    "m": "m", "m̄": "m1", "ḿ": "m2", "m̀": "m4",
    "n": "n", "ń": "n2", "ň": "n3", "ǹ": "n4",
    "o": "o", "ō": "o1", "ó": "o2", "ǒ": "o3", "ò": "o4",
    "p": "p", "q": "q", "r": "r", "s": "s", "t": "t",
    "u": "u", "ū": "u1", "ú": "u2", "ǔ": "u3", "ù": "u4",
    "ü": "v", "ǖ": "v1", "ǘ": "v2", "ǚ": "v3", "ǜ": "v4",
    "v": "v", "w": "w", "x": "x", "y": "y", "z": "z"
}


class OptimizedUtility:
    """Performance-optimized utility class for font generation."""
    
    def __init__(self, character_manager: Optional[CharacterDataManager] = None):
        """Initialize with character manager."""
        self.character_manager = character_manager or get_default_character_manager()
        self._cmap_table_cache: Optional[Dict[str, str]] = None
    
    @lru_cache(maxsize=FontConstants.LRU_CACHE_SIZE_XLARGE)
    def simplify_pronunciation(self, pronunciation: str) -> str:
        """
        Optimized pronunciation simplification with aggressive caching.
        
        Uses pre-computed mapping and efficient string operations.
        """
        if not pronunciation:
            return ""
        
        # Use list comprehension with get() for better performance
        simplified_chars = [
            SIMPLIFIED_ALPHABET.get(char, char) 
            for char in pronunciation
        ]
        return "".join(simplified_chars)
    
    @cached_function(ttl=None)  # Cache indefinitely as data rarely changes
    def get_single_pronunciation_characters_optimized(self) -> List[OptimizedHanziPinyin]:
        """Get single pronunciation characters with optimized data structure."""
        with performance_monitor("get_single_pronunciation_characters"):
            characters = []
            for char_info in self.character_manager.iter_single_pronunciation_characters():
                optimized = OptimizedHanziPinyin(
                    character=char_info.character,
                    pronunciations=tuple(char_info.pronunciations)
                )
                characters.append(optimized)
            return characters
    
    @cached_function(ttl=None)
    def get_multiple_pronunciation_characters_optimized(self) -> List[OptimizedHanziPinyin]:
        """Get multiple pronunciation characters with optimized data structure."""
        with performance_monitor("get_multiple_pronunciation_characters"):
            characters = []
            for char_info in self.character_manager.iter_multiple_pronunciation_characters():
                optimized = OptimizedHanziPinyin(
                    character=char_info.character,
                    pronunciations=tuple(char_info.pronunciations)
                )
                characters.append(optimized)
            return characters
    
    def iter_single_pronunciation_characters_fast(self) -> Iterator[OptimizedHanziPinyin]:
        """Memory-efficient iterator for single pronunciation characters."""
        for char_info in self.character_manager.iter_single_pronunciation_characters():
            yield OptimizedHanziPinyin(
                character=char_info.character,
                pronunciations=tuple(char_info.pronunciations)
            )
    
    def iter_multiple_pronunciation_characters_fast(self) -> Iterator[OptimizedHanziPinyin]:
        """Memory-efficient iterator for multiple pronunciation characters."""
        for char_info in self.character_manager.iter_multiple_pronunciation_characters():
            yield OptimizedHanziPinyin(
                character=char_info.character,
                pronunciations=tuple(char_info.pronunciations)
            )
    
    @profile_function("batch_process_characters")
    def batch_process_characters(
        self,
        characters: List[str],
        processing_func: callable,
        batch_size: int = 1000
    ) -> List[Any]:
        """
        Process characters in optimized batches with parallel execution.
        
        Args:
            characters: List of characters to process
            processing_func: Function to apply to each character
            batch_size: Size of each processing batch
            
        Returns:
            List of processing results
        """
        return FontProcessingOptimizer.process_characters_parallel(
            characters, processing_func, batch_size
        )
    
    @lru_cache(maxsize=1)
    def get_cmap_table(self) -> Dict[str, str]:
        """Get character map table with aggressive caching."""
        if self._cmap_table_cache is None:
            # Load from character data manager
            from ..data import get_default_mapping_manager
            mapping_manager = get_default_mapping_manager()
            self._cmap_table_cache = mapping_manager.get_cmap_table()
        return self._cmap_table_cache
    
    @lru_cache(maxsize=FontConstants.LRU_CACHE_SIZE_XLARGE)
    def convert_hanzi_to_cid_fast(self, hanzi: str) -> Optional[str]:
        """Fast hanzi to CID conversion with optimized caching."""
        cmap_table = self.get_cmap_table()
        unicode_key = str(ord(hanzi))
        return cmap_table.get(unicode_key)
    
    @profile_function("parallel_pronunciation_simplification")
    def simplify_pronunciations_parallel(self, pronunciations: List[str]) -> List[str]:
        """Parallel pronunciation simplification for large datasets."""
        if len(pronunciations) < 100:
            # Use serial processing for small datasets
            return [self.simplify_pronunciation(p) for p in pronunciations]
        
        # Use parallel processing for large datasets
        return parallel_map(
            self.simplify_pronunciation,
            pronunciations,
            max_workers=4  # Limit workers for memory efficiency
        )
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get performance statistics for optimization analysis."""
        single_chars = self.get_single_pronunciation_characters_optimized()
        multiple_chars = self.get_multiple_pronunciation_characters_optimized()
        
        return {
            'single_pronunciation_count': len(single_chars),
            'multiple_pronunciation_count': len(multiple_chars),
            'total_characters': len(single_chars) + len(multiple_chars),
            'cache_stats': {
                'simplify_pronunciation': self.simplify_pronunciation.cache_info(),
                'convert_hanzi_to_cid': self.convert_hanzi_to_cid_fast.cache_info(),
                'cmap_table': self.get_cmap_table.cache_info()
            }
        }
    
    def optimize_memory_usage(self) -> None:
        """Optimize memory usage by clearing unnecessary caches."""
        # Clear less critical caches while keeping essential ones
        if hasattr(self.simplify_pronunciation, 'cache_clear'):
            # Keep some entries but reduce cache size
            cache_info = self.simplify_pronunciation.cache_info()
            if cache_info.currsize > FontConstants.LRU_CACHE_SIZE_LARGE:
                # Partial cache clear - remove oldest entries
                self.simplify_pronunciation.cache_clear()


class BatchCharacterProcessor:
    """Specialized processor for batch character operations."""
    
    def __init__(self, utility: Optional[OptimizedUtility] = None):
        """Initialize batch processor."""
        self.utility = utility or OptimizedUtility()
    
    def process_character_batch(
        self,
        characters: List[str],
        operations: List[str]
    ) -> Dict[str, Any]:
        """
        Process a batch of characters with multiple operations efficiently.
        
        Args:
            characters: List of characters to process
            operations: List of operation names ['simplify', 'cid', 'pronunciation']
            
        Returns:
            Dictionary with results for each operation
        """
        results = {}
        
        with performance_monitor("batch_character_processing"):
            if 'simplify' in operations:
                # Get pronunciations and simplify them in parallel
                pronunciations = []
                for char in characters:
                    char_info = self.utility.character_manager.get_character_info(char)
                    if char_info:
                        pronunciations.extend(char_info.pronunciations)
                
                simplified = self.utility.simplify_pronunciations_parallel(pronunciations)
                results['simplified_pronunciations'] = simplified
            
            if 'cid' in operations:
                # Convert characters to CIDs in parallel
                cids = parallel_map(
                    self.utility.convert_hanzi_to_cid_fast,
                    characters,
                    max_workers=8
                )
                results['character_cids'] = cids
            
            if 'pronunciation' in operations:
                # Get pronunciation info for all characters
                def get_char_pronunciations(char: str) -> Optional[List[str]]:
                    char_info = self.utility.character_manager.get_character_info(char)
                    return char_info.pronunciations if char_info else None
                
                pronunciations = parallel_map(
                    get_char_pronunciations,
                    characters,
                    max_workers=4
                )
                results['character_pronunciations'] = pronunciations
        
        return results


# Global optimized utility instance
_global_optimized_utility: Optional[OptimizedUtility] = None


def get_global_optimized_utility() -> OptimizedUtility:
    """Get or create global optimized utility instance."""
    global _global_optimized_utility
    if _global_optimized_utility is None:
        _global_optimized_utility = OptimizedUtility()
    return _global_optimized_utility


# Backward compatibility functions with performance optimization
@persistent_cache(ttl_hours=24)
def get_has_single_pinyin_hanzi_optimized() -> List[OptimizedHanziPinyin]:
    """Optimized version of get_has_single_pinyin_hanzi with persistent caching."""
    utility = get_global_optimized_utility()
    return utility.get_single_pronunciation_characters_optimized()


@persistent_cache(ttl_hours=24)
def get_has_multiple_pinyin_hanzi_optimized() -> List[OptimizedHanziPinyin]:
    """Optimized version of get_has_multiple_pinyin_hanzi with persistent caching."""
    utility = get_global_optimized_utility()
    return utility.get_multiple_pronunciation_characters_optimized()


def simplification_pronunciation_fast(pronunciation: str) -> str:
    """Fast pronunciation simplification using global utility."""
    utility = get_global_optimized_utility()
    return utility.simplify_pronunciation(pronunciation)


def convert_str_hanzi_2_cid_fast(hanzi: str) -> Optional[str]:
    """Fast hanzi to CID conversion using global utility."""
    utility = get_global_optimized_utility()
    return utility.convert_hanzi_to_cid_fast(hanzi)