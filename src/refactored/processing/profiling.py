# -*- coding: utf-8 -*-
"""Performance profiling and monitoring utilities."""

from __future__ import annotations

import cProfile
import pstats
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path
from typing import Callable, Dict, Iterator, List, Optional

import psutil


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""

    function_name: str
    execution_time: float
    memory_usage: float
    cpu_usage: float
    call_count: int = 1

    def __add__(self, other: "PerformanceMetrics") -> "PerformanceMetrics":
        """Add metrics for aggregation."""
        if self.function_name != other.function_name:
            raise ValueError("Cannot add metrics for different functions")

        return PerformanceMetrics(
            function_name=self.function_name,
            execution_time=self.execution_time + other.execution_time,
            memory_usage=max(self.memory_usage, other.memory_usage),
            cpu_usage=max(self.cpu_usage, other.cpu_usage),
            call_count=self.call_count + other.call_count,
        )

    @property
    def avg_execution_time(self) -> float:
        """Average execution time per call."""
        return self.execution_time / self.call_count if self.call_count > 0 else 0.0


@dataclass
class PerformanceReport:
    """Comprehensive performance report."""

    total_execution_time: float
    peak_memory_usage: float
    average_cpu_usage: float
    function_metrics: Dict[str, PerformanceMetrics] = field(default_factory=dict)
    profiling_data: Optional[str] = None

    def get_top_functions_by_time(self, limit: int = 10) -> List[PerformanceMetrics]:
        """Get top functions by execution time."""
        return sorted(
            self.function_metrics.values(), key=lambda m: m.execution_time, reverse=True
        )[:limit]

    def get_top_functions_by_calls(self, limit: int = 10) -> List[PerformanceMetrics]:
        """Get top functions by call count."""
        return sorted(
            self.function_metrics.values(), key=lambda m: m.call_count, reverse=True
        )[:limit]


class PerformanceProfiler:
    """Advanced performance profiler for font generation pipeline."""

    def __init__(self, enable_detailed_profiling: bool = False):
        """Initialize performance profiler."""
        self.enable_detailed_profiling = enable_detailed_profiling
        self.metrics: Dict[str, List[PerformanceMetrics]] = {}
        self.start_time: Optional[float] = None
        self.profiler: Optional[cProfile.Profile] = None
        self._lock = threading.Lock()

        # System monitoring
        self.process = psutil.Process()
        self.initial_memory = self.process.memory_info().rss

    def start_profiling(self) -> None:
        """Start performance profiling session."""
        self.start_time = time.perf_counter()
        self.initial_memory = self.process.memory_info().rss

        if self.enable_detailed_profiling:
            self.profiler = cProfile.Profile()
            self.profiler.enable()

    def stop_profiling(self) -> PerformanceReport:
        """Stop profiling and generate report."""
        if self.start_time is None:
            raise RuntimeError("Profiling not started")

        total_time = time.perf_counter() - self.start_time
        peak_memory = self.process.memory_info().rss
        cpu_percent = self.process.cpu_percent()

        # Aggregate function metrics
        aggregated_metrics = {}
        for func_name, metric_list in self.metrics.items():
            if metric_list:
                base_metric = metric_list[0]
                for metric in metric_list[1:]:
                    base_metric = base_metric + metric
                aggregated_metrics[func_name] = base_metric

        # Get profiling data if enabled
        profiling_data = None
        if self.profiler:
            self.profiler.disable()
            stats = pstats.Stats(self.profiler)
            stats.sort_stats("cumulative")
            # Convert to string representation
            import io

            s = io.StringIO()
            stats.print_stats(20, s)  # Top 20 functions
            profiling_data = s.getvalue()

        return PerformanceReport(
            total_execution_time=total_time,
            peak_memory_usage=peak_memory,
            average_cpu_usage=cpu_percent,
            function_metrics=aggregated_metrics,
            profiling_data=profiling_data,
        )

    def record_function_metrics(self, func_name: str, execution_time: float) -> None:
        """Record metrics for a function call."""
        current_memory = self.process.memory_info().rss
        cpu_usage = self.process.cpu_percent()

        metrics = PerformanceMetrics(
            function_name=func_name,
            execution_time=execution_time,
            memory_usage=current_memory,
            cpu_usage=cpu_usage,
        )

        with self._lock:
            if func_name not in self.metrics:
                self.metrics[func_name] = []
            self.metrics[func_name].append(metrics)

    @contextmanager
    def profile_function(self, func_name: str) -> Iterator[None]:
        """Context manager for profiling a function."""
        start_time = time.perf_counter()
        try:
            yield
        finally:
            execution_time = time.perf_counter() - start_time
            self.record_function_metrics(func_name, execution_time)

    def save_report(self, report: PerformanceReport, output_path: Path) -> None:
        """Save performance report to file."""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# Font Generation Performance Report\n\n")
            f.write(f"Total Execution Time: {report.total_execution_time:.2f}s\n")
            f.write(
                f"Peak Memory Usage: {report.peak_memory_usage / 1024 / 1024:.2f} MB\n"
            )
            f.write(f"Average CPU Usage: {report.average_cpu_usage:.1f}%\n\n")

            f.write("## Top Functions by Execution Time\n")
            for i, metrics in enumerate(report.get_top_functions_by_time(10), 1):
                f.write(
                    f"{i}. {metrics.function_name}: {metrics.execution_time:.3f}s "
                    f"({metrics.call_count} calls, avg: {metrics.avg_execution_time:.3f}s)\n"
                )

            f.write("\n## Top Functions by Call Count\n")
            for i, metrics in enumerate(report.get_top_functions_by_calls(10), 1):
                f.write(
                    f"{i}. {metrics.function_name}: {metrics.call_count} calls "
                    f"({metrics.execution_time:.3f}s total)\n"
                )

            if report.profiling_data:
                f.write("\n## Detailed Profiling Data\n")
                f.write("```\n")
                f.write(report.profiling_data)
                f.write("```\n")


# Global profiler instance
_global_profiler: Optional[PerformanceProfiler] = None


def get_global_profiler() -> PerformanceProfiler:
    """Get or create global profiler instance."""
    global _global_profiler
    if _global_profiler is None:
        _global_profiler = PerformanceProfiler()
    return _global_profiler


@contextmanager
def performance_monitor(func_name: str) -> Iterator[None]:
    """Context manager for monitoring performance of code blocks."""
    profiler = get_global_profiler()
    with profiler.profile_function(func_name):
        yield


def profile_function(func_name: Optional[str] = None):
    """Decorator for profiling function performance."""

    def decorator(func: Callable) -> Callable:
        name = func_name or f"{func.__module__}.{func.__name__}"

        @wraps(func)
        def wrapper(*args, **kwargs):
            with performance_monitor(name):
                return func(*args, **kwargs)

        return wrapper

    return decorator


class MemoryProfiler:
    """Memory usage profiler for tracking memory consumption."""

    def __init__(self):
        """Initialize memory profiler."""
        self.process = psutil.Process()
        self.snapshots: List[tuple[str, float, float]] = []

    def take_snapshot(self, label: str) -> None:
        """Take a memory usage snapshot."""
        memory_info = self.process.memory_info()
        rss = memory_info.rss / 1024 / 1024  # MB
        vms = memory_info.vms / 1024 / 1024  # MB
        # timestamp = time.perf_counter()  # Unused

        self.snapshots.append((label, rss, vms))

    def get_memory_usage_report(self) -> str:
        """Generate memory usage report."""
        if not self.snapshots:
            return "No memory snapshots taken"

        report = ["Memory Usage Report", "=" * 50]

        for i, (label, rss, vms) in enumerate(self.snapshots):
            report.append(f"{i+1:2d}. {label:<30} RSS: {rss:8.2f}MB  VMS: {vms:8.2f}MB")

            if i > 0:
                prev_rss = self.snapshots[i - 1][1]
                diff = rss - prev_rss
                sign = "+" if diff >= 0 else ""
                report[-1] += f"  ({sign}{diff:+7.2f}MB)"

        return "\n".join(report)

    @contextmanager
    def monitor_memory(self, label: str) -> Iterator[None]:
        """Context manager for monitoring memory during execution."""
        self.take_snapshot(f"{label} - Start")
        try:
            yield
        finally:
            self.take_snapshot(f"{label} - End")
