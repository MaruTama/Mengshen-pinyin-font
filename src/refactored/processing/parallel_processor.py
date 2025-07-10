# -*- coding: utf-8 -*-
"""Parallel processing utilities for performance optimization."""

from __future__ import annotations

import asyncio
import concurrent.futures
from functools import partial
from typing import Any, Callable, Iterable, List, Optional, TypeVar
from dataclasses import dataclass
from multiprocessing import cpu_count

T = TypeVar('T')
U = TypeVar('U')


@dataclass
class ProcessingConfig:
    """Configuration for parallel processing."""
    max_workers: Optional[int] = None
    chunk_size: Optional[int] = None
    use_threads: bool = True  # True for I/O bound, False for CPU bound
    
    def __post_init__(self):
        """Set default values after initialization."""
        if self.max_workers is None:
            self.max_workers = min(32, (cpu_count() or 1) + 4)
        
        if self.chunk_size is None:
            self.chunk_size = max(1, 1000 // (self.max_workers or 1))


class ParallelProcessor:
    """High-performance parallel processor for font generation tasks."""
    
    def __init__(self, config: Optional[ProcessingConfig] = None):
        """Initialize parallel processor."""
        self.config = config or ProcessingConfig()
    
    def map_parallel(
        self,
        func: Callable[[T], U],
        iterable: Iterable[T],
        ordered: bool = True
    ) -> List[U]:
        """
        Apply function to iterable in parallel.
        
        Args:
            func: Function to apply
            iterable: Input data
            ordered: Whether to preserve order of results
            
        Returns:
            List of results
        """
        items = list(iterable)
        if not items:
            return []
        
        # Choose executor type based on configuration
        executor_class = (
            concurrent.futures.ThreadPoolExecutor
            if self.config.use_threads
            else concurrent.futures.ProcessPoolExecutor
        )
        
        with executor_class(max_workers=self.config.max_workers) as executor:
            if ordered:
                return list(executor.map(func, items))
            else:
                # Submit all tasks and collect results as they complete
                futures = [executor.submit(func, item) for item in items]
                return [future.result() for future in concurrent.futures.as_completed(futures)]
    
    def map_chunked(
        self,
        func: Callable[[List[T]], List[U]],
        iterable: Iterable[T],
        chunk_size: Optional[int] = None
    ) -> List[U]:
        """
        Apply function to chunks of data in parallel.
        
        Useful for batch processing where the function can efficiently
        process multiple items at once.
        """
        items = list(iterable)
        chunk_size = chunk_size or self.config.chunk_size
        
        # Split into chunks
        chunks = [
            items[i:i + chunk_size]
            for i in range(0, len(items), chunk_size)
        ]
        
        # Process chunks in parallel
        executor_class = (
            concurrent.futures.ThreadPoolExecutor
            if self.config.use_threads
            else concurrent.futures.ProcessPoolExecutor
        )
        
        with executor_class(max_workers=self.config.max_workers) as executor:
            chunk_results = list(executor.map(func, chunks))
        
        # Flatten results
        results = []
        for chunk_result in chunk_results:
            results.extend(chunk_result)
        
        return results
    
    async def map_async(
        self,
        func: Callable[[T], U],
        iterable: Iterable[T],
        semaphore_limit: int = 100
    ) -> List[U]:
        """
        Apply function to iterable using async/await for I/O bound tasks.
        
        Args:
            func: Function to apply (can be sync or async)
            iterable: Input data
            semaphore_limit: Maximum concurrent operations
            
        Returns:
            List of results
        """
        semaphore = asyncio.Semaphore(semaphore_limit)
        
        async def process_item(item: T) -> U:
            async with semaphore:
                if asyncio.iscoroutinefunction(func):
                    return await func(item)
                else:
                    # Run sync function in thread pool
                    loop = asyncio.get_event_loop()
                    return await loop.run_in_executor(None, func, item)
        
        tasks = [process_item(item) for item in iterable]
        return await asyncio.gather(*tasks)
    
    def filter_parallel(
        self,
        predicate: Callable[[T], bool],
        iterable: Iterable[T]
    ) -> List[T]:
        """Filter iterable in parallel."""
        items = list(iterable)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            results = list(executor.map(
                lambda item: (item, predicate(item)),
                items
            ))
        
        return [item for item, passed in results if passed]
    
    def reduce_parallel(
        self,
        func: Callable[[T, T], T],
        iterable: Iterable[T],
        initializer: Optional[T] = None
    ) -> T:
        """
        Parallel reduction using divide-and-conquer approach.
        
        Note: The function must be associative for correct results.
        """
        items = list(iterable)
        if not items:
            if initializer is not None:
                return initializer
            raise ValueError("reduce() of empty sequence with no initial value")
        
        if len(items) == 1:
            return items[0] if initializer is None else func(initializer, items[0])
        
        # Divide and conquer
        while len(items) > 1:
            pairs = []
            for i in range(0, len(items), 2):
                if i + 1 < len(items):
                    pairs.append((items[i], items[i + 1]))
                else:
                    pairs.append((items[i], None))
            
            def reduce_pair(pair):
                a, b = pair
                return a if b is None else func(a, b)
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                items = list(executor.map(reduce_pair, pairs))
        
        result = items[0]
        return result if initializer is None else func(initializer, result)


class PipelineProcessor:
    """Pipeline processor for chaining operations efficiently."""
    
    def __init__(self, parallel_processor: Optional[ParallelProcessor] = None):
        """Initialize pipeline processor."""
        self.parallel_processor = parallel_processor or ParallelProcessor()
        self.stages: List[Callable] = []
    
    def add_stage(self, func: Callable, parallel: bool = True) -> 'PipelineProcessor':
        """Add a processing stage to the pipeline."""
        if parallel:
            stage = partial(self.parallel_processor.map_parallel, func)
        else:
            stage = lambda data: [func(item) for item in data]
        
        self.stages.append(stage)
        return self
    
    def add_filter_stage(self, predicate: Callable[[T], bool]) -> 'PipelineProcessor':
        """Add a filtering stage to the pipeline."""
        stage = partial(self.parallel_processor.filter_parallel, predicate)
        self.stages.append(stage)
        return self
    
    def process(self, data: Iterable[T]) -> List[Any]:
        """Process data through the pipeline."""
        current_data = list(data)
        
        for stage in self.stages:
            current_data = stage(current_data)
        
        return current_data


# Global processor instance
_global_processor: Optional[ParallelProcessor] = None


def get_global_processor() -> ParallelProcessor:
    """Get or create global parallel processor."""
    global _global_processor
    if _global_processor is None:
        _global_processor = ParallelProcessor()
    return _global_processor


def parallel_map(
    func: Callable[[T], U],
    iterable: Iterable[T],
    max_workers: Optional[int] = None,
    ordered: bool = True
) -> List[U]:
    """Convenience function for parallel mapping."""
    config = ProcessingConfig(max_workers=max_workers)
    processor = ParallelProcessor(config)
    return processor.map_parallel(func, iterable, ordered)


def parallel_filter(
    predicate: Callable[[T], bool],
    iterable: Iterable[T],
    max_workers: Optional[int] = None
) -> List[T]:
    """Convenience function for parallel filtering."""
    config = ProcessingConfig(max_workers=max_workers)
    processor = ParallelProcessor(config)
    return processor.filter_parallel(predicate, iterable)


async def async_map(
    func: Callable[[T], U],
    iterable: Iterable[T],
    semaphore_limit: int = 100
) -> List[U]:
    """Convenience function for async mapping."""
    processor = get_global_processor()
    return await processor.map_async(func, iterable, semaphore_limit)


class BatchProcessor:
    """Specialized processor for batch operations on large datasets."""
    
    def __init__(
        self,
        batch_size: int = 1000,
        max_workers: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ):
        """Initialize batch processor."""
        self.batch_size = batch_size
        self.max_workers = max_workers or min(32, (cpu_count() or 1) + 4)
        self.progress_callback = progress_callback
    
    def process_batches(
        self,
        func: Callable[[List[T]], List[U]],
        data: Iterable[T]
    ) -> List[U]:
        """Process data in batches with progress tracking."""
        items = list(data)
        total_items = len(items)
        
        # Create batches
        batches = [
            items[i:i + self.batch_size]
            for i in range(0, total_items, self.batch_size)
        ]
        
        results = []
        processed_items = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all batches
            future_to_batch = {
                executor.submit(func, batch): batch
                for batch in batches
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_batch):
                batch = future_to_batch[future]
                batch_result = future.result()
                results.extend(batch_result)
                
                processed_items += len(batch)
                if self.progress_callback:
                    self.progress_callback(processed_items, total_items)
        
        return results


# Specialized processors for font generation
class FontProcessingOptimizer:
    """Optimized processing for font generation tasks."""
    
    @staticmethod
    def process_characters_parallel(
        characters: List[str],
        processing_func: Callable[[str], Any],
        chunk_size: int = 100
    ) -> List[Any]:
        """Process characters in parallel with optimal chunking."""
        def process_chunk(chunk: List[str]) -> List[Any]:
            return [processing_func(char) for char in chunk]
        
        config = ProcessingConfig(
            max_workers=min(8, cpu_count()),  # Limit for memory efficiency
            chunk_size=chunk_size,
            use_threads=True  # Font processing is often I/O bound
        )
        
        processor = ParallelProcessor(config)
        return processor.map_chunked(process_chunk, characters)
    
    @staticmethod
    def process_glyphs_parallel(
        glyph_data: dict,
        processing_func: Callable[[tuple], Any],
        max_workers: int = 4
    ) -> List[Any]:
        """Process glyph data in parallel with memory optimization."""
        # Convert dict to items for parallel processing
        items = list(glyph_data.items())
        
        config = ProcessingConfig(
            max_workers=max_workers,  # Limited for memory efficiency
            use_threads=False  # CPU-bound glyph processing
        )
        
        processor = ParallelProcessor(config)
        return processor.map_parallel(processing_func, items)