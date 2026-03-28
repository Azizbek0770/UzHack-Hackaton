from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from statistics import mean
from typing import Deque, Dict, List


@dataclass
class QueryMetric:
    """Single query execution metric."""

    latency_ms: int
    retrieved_count: int
    source_count: int
    confidence: float
    mode: str


class TelemetryCollector:
    """Rolling in-memory telemetry collector for QA operations."""

    def __init__(self, window_size: int = 300) -> None:
        self._window_size = window_size
        self._metrics: Deque[QueryMetric] = deque(maxlen=window_size)

    def add(self, metric: QueryMetric) -> None:
        """Store one query metric sample."""

        self._metrics.append(metric)

    def summary(self) -> Dict[str, float | int]:
        """Return aggregated telemetry snapshot."""

        if not self._metrics:
            return {
                "sample_size": 0,
                "latency_avg_ms": 0.0,
                "latency_p95_ms": 0.0,
                "retrieved_avg": 0.0,
                "source_avg": 0.0,
                "confidence_avg": 0.0,
            }
        latencies: List[int] = sorted(metric.latency_ms for metric in self._metrics)
        p95_index = max(0, int(len(latencies) * 0.95) - 1)
        return {
            "sample_size": len(self._metrics),
            "latency_avg_ms": round(mean(latencies), 2),
            "latency_p95_ms": float(latencies[p95_index]),
            "retrieved_avg": round(mean(metric.retrieved_count for metric in self._metrics), 2),
            "source_avg": round(mean(metric.source_count for metric in self._metrics), 2),
            "confidence_avg": round(mean(metric.confidence for metric in self._metrics), 4),
        }
