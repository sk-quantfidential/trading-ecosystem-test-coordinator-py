"""Domain ports for test coordinator service.

Ports define the interfaces that infrastructure adapters must implement.
Following Clean Architecture: domain defines contracts, infrastructure implements them.
"""
from test_coordinator.domain.ports.metrics import MetricsLabels, MetricsPort

__all__ = [
    "MetricsPort",
    "MetricsLabels",
]
