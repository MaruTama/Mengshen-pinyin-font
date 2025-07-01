# -*- coding: utf-8 -*-
"""Benchmarking utilities for performance analysis."""

from __future__ import annotations

import time
import statistics
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from contextlib import contextmanager

from .profiling import PerformanceProfiler, MemoryProfiler


@dataclass
class BenchmarkResult:
    """Result of a benchmark test."""
    name: str
    execution_times: List[float]
    memory_usage: Optional[float] = None
    iterations: int = 1
    
    @property
    def mean_time(self) -> float:
        """Mean execution time."""
        return statistics.mean(self.execution_times)
    
    @property
    def median_time(self) -> float:
        """Median execution time."""
        return statistics.median(self.execution_times)
    
    @property
    def std_deviation(self) -> float:
        """Standard deviation of execution times."""
        return statistics.stdev(self.execution_times) if len(self.execution_times) > 1 else 0.0
    
    @property
    def min_time(self) -> float:
        """Minimum execution time."""
        return min(self.execution_times)
    
    @property
    def max_time(self) -> float:
        """Maximum execution time."""
        return max(self.execution_times)


@dataclass
class BenchmarkSuite:
    """Collection of benchmark results."""
    name: str
    results: List[BenchmarkResult] = field(default_factory=list)
    
    def add_result(self, result: BenchmarkResult) -> None:
        """Add a benchmark result."""
        self.results.append(result)
    
    def get_result(self, name: str) -> Optional[BenchmarkResult]:
        """Get benchmark result by name."""
        for result in self.results:
            if result.name == name:
                return result
        return None
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics for the benchmark suite."""
        if not self.results:
            return {}
        
        total_time = sum(result.mean_time for result in self.results)
        fastest_test = min(self.results, key=lambda r: r.mean_time)
        slowest_test = max(self.results, key=lambda r: r.mean_time)
        
        return {
            'suite_name': self.name,
            'total_tests': len(self.results),
            'total_time': total_time,
            'fastest_test': {'name': fastest_test.name, 'time': fastest_test.mean_time},
            'slowest_test': {'name': slowest_test.name, 'time': slowest_test.mean_time},
            'average_test_time': total_time / len(self.results)
        }


class Benchmark:
    """High-performance benchmarking utility."""
    
    def __init__(self, enable_memory_profiling: bool = True):
        """Initialize benchmark."""
        self.enable_memory_profiling = enable_memory_profiling
        self.profiler = PerformanceProfiler(enable_detailed_profiling=True)
        self.memory_profiler = MemoryProfiler() if enable_memory_profiling else None
    
    def time_function(
        self,
        func: Callable,
        *args,
        iterations: int = 10,
        warmup_iterations: int = 2,
        **kwargs
    ) -> BenchmarkResult:
        """
        Benchmark a function with multiple iterations.
        
        Args:
            func: Function to benchmark
            *args: Arguments for the function
            iterations: Number of benchmark iterations
            warmup_iterations: Number of warmup iterations (not counted)
            **kwargs: Keyword arguments for the function
            
        Returns:
            BenchmarkResult with timing statistics
        """
        func_name = getattr(func, '__name__', str(func))
        
        # Warmup runs
        for _ in range(warmup_iterations):
            func(*args, **kwargs)
        
        # Benchmark runs
        execution_times = []
        memory_usage = None
        
        for iteration in range(iterations):
            if self.memory_profiler:
                with self.memory_profiler.monitor_memory(f"{func_name}_iteration_{iteration}"):
                    start_time = time.perf_counter()
                    func(*args, **kwargs)
                    end_time = time.perf_counter()
            else:
                start_time = time.perf_counter()
                func(*args, **kwargs)
                end_time = time.perf_counter()
            
            execution_times.append(end_time - start_time)
        
        if self.memory_profiler and self.memory_profiler.snapshots:
            # Calculate average memory usage during benchmark
            memory_values = [snapshot[1] for snapshot in self.memory_profiler.snapshots]
            memory_usage = statistics.mean(memory_values)
        
        return BenchmarkResult(
            name=func_name,
            execution_times=execution_times,
            memory_usage=memory_usage,
            iterations=iterations
        )
    
    @contextmanager
    def benchmark_context(self, name: str):
        """Context manager for benchmarking code blocks."""
        start_time = time.perf_counter()
        if self.memory_profiler:
            self.memory_profiler.take_snapshot(f"{name}_start")
        
        try:
            yield
        finally:
            end_time = time.perf_counter()
            if self.memory_profiler:
                self.memory_profiler.take_snapshot(f"{name}_end")
            
            execution_time = end_time - start_time
            print(f"Benchmark '{name}': {execution_time:.4f}s")
    
    def compare_functions(
        self,
        functions: Dict[str, Callable],
        *args,
        iterations: int = 10,
        **kwargs
    ) -> BenchmarkSuite:
        """
        Compare multiple functions with the same arguments.
        
        Args:
            functions: Dictionary of {name: function} to compare
            *args: Arguments for all functions
            iterations: Number of benchmark iterations
            **kwargs: Keyword arguments for all functions
            
        Returns:
            BenchmarkSuite with results for all functions
        """
        suite = BenchmarkSuite(name="Function Comparison")
        
        for name, func in functions.items():
            result = self.time_function(func, *args, iterations=iterations, **kwargs)
            result.name = name  # Override with custom name
            suite.add_result(result)
        
        return suite
    
    def profile_with_comparison(
        self,
        old_func: Callable,
        new_func: Callable,
        *args,
        iterations: int = 10,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Profile and compare old vs new function implementations.
        
        Returns detailed comparison including performance improvements.
        """
        old_result = self.time_function(old_func, *args, iterations=iterations, **kwargs)
        old_result.name = "Old Implementation"
        
        new_result = self.time_function(new_func, *args, iterations=iterations, **kwargs)
        new_result.name = "New Implementation"
        
        # Calculate improvements
        time_improvement = (old_result.mean_time - new_result.mean_time) / old_result.mean_time * 100
        memory_improvement = None
        
        if old_result.memory_usage and new_result.memory_usage:
            memory_improvement = (old_result.memory_usage - new_result.memory_usage) / old_result.memory_usage * 100
        
        return {
            'old_implementation': {
                'mean_time': old_result.mean_time,
                'std_dev': old_result.std_deviation,
                'memory_usage': old_result.memory_usage
            },
            'new_implementation': {
                'mean_time': new_result.mean_time,
                'std_dev': new_result.std_deviation,
                'memory_usage': new_result.memory_usage
            },
            'improvements': {
                'time_improvement_percent': time_improvement,
                'memory_improvement_percent': memory_improvement,
                'speedup_factor': old_result.mean_time / new_result.mean_time if new_result.mean_time > 0 else float('inf')
            }
        }


class FontGenerationBenchmark:
    """Specialized benchmark for font generation pipeline."""
    
    def __init__(self):
        """Initialize font generation benchmark."""
        self.benchmark = Benchmark(enable_memory_profiling=True)
        self.results = {}
    
    def benchmark_character_processing(self, characters: List[str]) -> BenchmarkResult:
        """Benchmark character processing operations."""
        from .optimized_utility import OptimizedUtility
        
        utility = OptimizedUtility()
        
        def process_characters():
            results = []
            for char in characters:
                char_info = utility.character_manager.get_character_info(char)
                if char_info:
                    simplified = utility.simplify_pronunciation(char_info.pronunciations[0])
                    cid = utility.convert_hanzi_to_cid_fast(char)
                    results.append((char, simplified, cid))
            return results
        
        return self.benchmark.time_function(
            process_characters,
            iterations=5,
            warmup_iterations=1
        )
    
    def benchmark_parallel_vs_serial(self, data: List[Any], processing_func: Callable) -> Dict[str, Any]:
        """Compare parallel vs serial processing performance."""
        from .parallel_processor import parallel_map
        
        def serial_processing():
            return [processing_func(item) for item in data]
        
        def parallel_processing():
            return parallel_map(processing_func, data, max_workers=4)
        
        return self.benchmark.profile_with_comparison(
            serial_processing,
            parallel_processing,
            iterations=5
        )
    
    def benchmark_caching_impact(self, operation_func: Callable, test_data: List[Any]) -> Dict[str, Any]:
        """Benchmark the impact of caching on performance."""
        # Clear cache first
        if hasattr(operation_func, 'cache_clear'):
            operation_func.cache_clear()
        
        # Benchmark without cache (cold start)
        def cold_run():
            return [operation_func(item) for item in test_data]
        
        cold_result = self.benchmark.time_function(cold_run, iterations=1)
        
        # Warm up cache
        cold_run()
        
        # Benchmark with cache (warm)
        warm_result = self.benchmark.time_function(cold_run, iterations=5)
        
        cache_improvement = (cold_result.mean_time - warm_result.mean_time) / cold_result.mean_time * 100
        
        return {
            'cold_cache_time': cold_result.mean_time,
            'warm_cache_time': warm_result.mean_time,
            'cache_improvement_percent': cache_improvement,
            'cache_speedup_factor': cold_result.mean_time / warm_result.mean_time
        }
    
    def run_comprehensive_benchmark(self, sample_characters: List[str]) -> Dict[str, Any]:
        """Run comprehensive benchmark of font generation pipeline."""
        print("Running comprehensive font generation benchmark...")
        
        results = {}
        
        # Character processing benchmark
        with self.benchmark.benchmark_context("Character Processing"):
            char_result = self.benchmark_character_processing(sample_characters[:100])
            results['character_processing'] = char_result
        
        # Parallel processing benchmark
        from .optimized_utility import simplification_pronunciation_fast
        
        with self.benchmark.benchmark_context("Parallel vs Serial"):
            parallel_result = self.benchmark_parallel_vs_serial(
                sample_characters[:50],
                lambda char: simplification_pronunciation_fast(char)
            )
            results['parallel_comparison'] = parallel_result
        
        # Caching impact benchmark
        with self.benchmark.benchmark_context("Caching Impact"):
            from .optimized_utility import get_global_optimized_utility
            utility = get_global_optimized_utility()
            
            cache_result = self.benchmark_caching_impact(
                utility.simplify_pronunciation,
                ["zhōng", "zhòng", "píng", "yīn"] * 25
            )
            results['caching_impact'] = cache_result
        
        return results


def run_performance_comparison() -> None:
    """Run performance comparison between old and new implementations."""
    print("=" * 60)
    print("PERFORMANCE OPTIMIZATION BENCHMARK")
    print("=" * 60)
    
    # Sample data for testing
    sample_characters = ["中", "国", "拼", "音", "字", "体"] * 20
    sample_pronunciations = ["zhōng", "guó", "pīn", "yīn", "zì", "tǐ"] * 20
    
    benchmark_suite = FontGenerationBenchmark()
    results = benchmark_suite.run_comprehensive_benchmark(sample_characters)
    
    print("\n📊 BENCHMARK RESULTS:")
    print("-" * 40)
    
    for test_name, result in results.items():
        print(f"\n{test_name.upper()}:")
        
        if isinstance(result, BenchmarkResult):
            print(f"  Mean time: {result.mean_time:.4f}s")
            print(f"  Std dev: {result.std_deviation:.4f}s")
            if result.memory_usage:
                print(f"  Memory usage: {result.memory_usage:.2f}MB")
        
        elif isinstance(result, dict) and 'improvements' in result:
            print(f"  Time improvement: {result['improvements']['time_improvement_percent']:.1f}%")
            print(f"  Speedup factor: {result['improvements']['speedup_factor']:.2f}x")
            if result['improvements']['memory_improvement_percent']:
                print(f"  Memory improvement: {result['improvements']['memory_improvement_percent']:.1f}%")
        
        elif isinstance(result, dict) and 'cache_improvement_percent' in result:
            print(f"  Cache improvement: {result['cache_improvement_percent']:.1f}%")
            print(f"  Cache speedup: {result['cache_speedup_factor']:.2f}x")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    run_performance_comparison()