"""Performance monitoring and metrics collection for Test Coordinator infrastructure."""

import time
import asyncio
from collections import deque, defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
import statistics
import structlog

from test_coordinator.infrastructure.constants import (
    PERFORMANCE_METRICS_WINDOW_SIZE,
    PERFORMANCE_METRICS_RETENTION_SECONDS
)

logger = structlog.get_logger()


@dataclass
class MetricDataPoint:
    """Individual metric data point."""
    timestamp: float
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """Performance metrics summary."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0
    requests_per_second: float = 0.0
    error_rate: float = 0.0
    success_rate: float = 0.0


class MetricsCollector:
    """Collects and aggregates performance metrics."""

    def __init__(self, window_size: int = PERFORMANCE_METRICS_WINDOW_SIZE):
        """Initialize metrics collector.

        Args:
            window_size: Size of the sliding window for metrics
        """
        self.window_size = window_size
        self._response_times: deque = deque(maxlen=window_size)
        self._request_counts: deque = deque(maxlen=window_size)
        self._error_counts: deque = deque(maxlen=window_size)
        self._timestamps: deque = deque(maxlen=window_size)
        self._custom_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self._start_time = time.time()

    def record_request(self, response_time: float, success: bool = True, labels: Optional[Dict[str, str]] = None):
        """Record a request with its response time and outcome.

        Args:
            response_time: Response time in seconds
            success: Whether the request was successful
            labels: Optional labels for the metric
        """
        now = time.time()

        self._response_times.append(response_time)
        self._request_counts.append(1)
        self._error_counts.append(0 if success else 1)
        self._timestamps.append(now)

        logger.debug(
            "Request recorded",
            response_time=response_time,
            success=success,
            labels=labels or {}
        )

    def record_custom_metric(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a custom metric.

        Args:
            name: Metric name
            value: Metric value
            labels: Optional labels for the metric
        """
        self._custom_metrics[name].append(value)

        logger.debug(
            "Custom metric recorded",
            metric=name,
            value=value,
            labels=labels or {}
        )

    def get_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics.

        Returns:
            PerformanceMetrics object with current statistics
        """
        if not self._response_times:
            return PerformanceMetrics()

        response_times = list(self._response_times)
        request_counts = list(self._request_counts)
        error_counts = list(self._error_counts)

        total_requests = sum(request_counts)
        failed_requests = sum(error_counts)
        successful_requests = total_requests - failed_requests

        # Calculate time-based metrics
        time_window = time.time() - (self._timestamps[0] if self._timestamps else self._start_time)
        requests_per_second = total_requests / max(time_window, 1.0)

        # Calculate response time statistics
        avg_response_time = statistics.mean(response_times) if response_times else 0.0
        min_response_time = min(response_times) if response_times else 0.0
        max_response_time = max(response_times) if response_times else 0.0

        # Calculate percentiles
        p95_response_time = 0.0
        p99_response_time = 0.0
        if len(response_times) >= 2:
            sorted_times = sorted(response_times)
            p95_index = int(0.95 * len(sorted_times))
            p99_index = int(0.99 * len(sorted_times))
            p95_response_time = sorted_times[min(p95_index, len(sorted_times) - 1)]
            p99_response_time = sorted_times[min(p99_index, len(sorted_times) - 1)]

        # Calculate rates
        error_rate = (failed_requests / total_requests) if total_requests > 0 else 0.0
        success_rate = (successful_requests / total_requests) if total_requests > 0 else 0.0

        return PerformanceMetrics(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            success_rate=success_rate
        )

    def get_custom_metrics(self) -> Dict[str, Dict[str, float]]:
        """Get custom metrics statistics.

        Returns:
            Dictionary mapping metric names to their statistics
        """
        result = {}

        for name, values in self._custom_metrics.items():
            if values:
                value_list = list(values)
                result[name] = {
                    'count': len(value_list),
                    'sum': sum(value_list),
                    'avg': statistics.mean(value_list),
                    'min': min(value_list),
                    'max': max(value_list),
                    'latest': value_list[-1]
                }
            else:
                result[name] = {
                    'count': 0,
                    'sum': 0.0,
                    'avg': 0.0,
                    'min': 0.0,
                    'max': 0.0,
                    'latest': 0.0
                }

        return result

    def clear(self):
        """Clear all collected metrics."""
        self._response_times.clear()
        self._request_counts.clear()
        self._error_counts.clear()
        self._timestamps.clear()
        self._custom_metrics.clear()
        self._start_time = time.time()
        logger.info("Metrics collector cleared")


class PerformanceMonitor:
    """Monitor and track performance across multiple components."""

    def __init__(self):
        """Initialize performance monitor."""
        self._collectors: Dict[str, MetricsCollector] = {}
        self._global_collector = MetricsCollector()
        self._start_time = time.time()

    def get_collector(self, component: str) -> MetricsCollector:
        """Get or create a metrics collector for a component.

        Args:
            component: Component name

        Returns:
            MetricsCollector for the component
        """
        if component not in self._collectors:
            self._collectors[component] = MetricsCollector()
            logger.debug("Created metrics collector", component=component)

        return self._collectors[component]

    def record_request(self, component: str, response_time: float, success: bool = True,
                      labels: Optional[Dict[str, str]] = None):
        """Record a request for a specific component.

        Args:
            component: Component name
            response_time: Response time in seconds
            success: Whether the request was successful
            labels: Optional labels for the metric
        """
        collector = self.get_collector(component)
        collector.record_request(response_time, success, labels)

        # Also record in global collector
        self._global_collector.record_request(response_time, success, labels)

    def record_custom_metric(self, component: str, metric_name: str, value: float,
                           labels: Optional[Dict[str, str]] = None):
        """Record a custom metric for a specific component.

        Args:
            component: Component name
            metric_name: Metric name
            value: Metric value
            labels: Optional labels for the metric
        """
        collector = self.get_collector(component)
        collector.record_custom_metric(metric_name, value, labels)

    def get_component_metrics(self, component: str) -> PerformanceMetrics:
        """Get metrics for a specific component.

        Args:
            component: Component name

        Returns:
            PerformanceMetrics for the component
        """
        collector = self.get_collector(component)
        return collector.get_metrics()

    def get_global_metrics(self) -> PerformanceMetrics:
        """Get global performance metrics across all components.

        Returns:
            Global PerformanceMetrics
        """
        return self._global_collector.get_metrics()

    def get_all_metrics(self) -> Dict[str, PerformanceMetrics]:
        """Get metrics for all components.

        Returns:
            Dictionary mapping component names to their metrics
        """
        result = {'_global': self.get_global_metrics()}

        for component, collector in self._collectors.items():
            result[component] = collector.get_metrics()

        return result

    def get_custom_metrics(self, component: str) -> Dict[str, Dict[str, float]]:
        """Get custom metrics for a specific component.

        Args:
            component: Component name

        Returns:
            Custom metrics for the component
        """
        collector = self.get_collector(component)
        return collector.get_custom_metrics()

    def get_summary_report(self) -> Dict[str, Any]:
        """Get a comprehensive summary report.

        Returns:
            Dictionary with comprehensive performance summary
        """
        uptime = time.time() - self._start_time
        global_metrics = self.get_global_metrics()

        report = {
            'uptime_seconds': uptime,
            'global_metrics': {
                'total_requests': global_metrics.total_requests,
                'successful_requests': global_metrics.successful_requests,
                'failed_requests': global_metrics.failed_requests,
                'average_response_time': global_metrics.average_response_time,
                'requests_per_second': global_metrics.requests_per_second,
                'error_rate': global_metrics.error_rate,
                'success_rate': global_metrics.success_rate
            },
            'component_metrics': {}
        }

        for component in self._collectors.keys():
            metrics = self.get_component_metrics(component)
            custom_metrics = self.get_custom_metrics(component)

            report['component_metrics'][component] = {
                'requests': metrics.total_requests,
                'avg_response_time': metrics.average_response_time,
                'error_rate': metrics.error_rate,
                'custom_metrics': custom_metrics
            }

        return report

    def clear_all_metrics(self):
        """Clear all metrics across all collectors."""
        self._global_collector.clear()
        for collector in self._collectors.values():
            collector.clear()
        self._start_time = time.time()
        logger.info("All performance metrics cleared")


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def timed_operation(component: str, operation_name: str = "operation"):
    """Decorator to time operations and record metrics.

    Args:
        component: Component name
        operation_name: Name of the operation being timed

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                success = True
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    success = False
                    raise
                finally:
                    duration = time.time() - start_time
                    performance_monitor.record_request(
                        component=component,
                        response_time=duration,
                        success=success,
                        labels={'operation': operation_name}
                    )
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                success = True
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    success = False
                    raise
                finally:
                    duration = time.time() - start_time
                    performance_monitor.record_request(
                        component=component,
                        response_time=duration,
                        success=success,
                        labels={'operation': operation_name}
                    )
            return sync_wrapper
    return decorator