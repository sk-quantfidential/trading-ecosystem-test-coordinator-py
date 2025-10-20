"""Observability infrastructure for test coordinator service.

This module provides concrete implementations of observability ports,
including Prometheus metrics and RED pattern middleware.
"""
from test_coordinator.infrastructure.observability.prometheus_adapter import (
    PrometheusMetricsAdapter,
)

__all__ = [
    "PrometheusMetricsAdapter",
]
