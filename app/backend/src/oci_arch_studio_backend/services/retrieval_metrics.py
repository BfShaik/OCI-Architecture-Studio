from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter


@dataclass
class RetrievalMetrics:
    request_count: int = 0
    missing_index_count: int = 0
    total_latency_ms: float = 0.0
    last_latency_ms: float | None = None
    last_result_count: int = 0
    last_provider: str = "unknown"
    last_embedding_model: str = "unknown"
    last_intent: str | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def average_latency_ms(self) -> float:
        if self.request_count == 0:
            return 0.0
        return round(self.total_latency_ms / self.request_count, 2)

    def as_dict(self) -> dict[str, object]:
        return {
            "request_count": self.request_count,
            "missing_index_count": self.missing_index_count,
            "average_latency_ms": self.average_latency_ms,
            "last_latency_ms": self.last_latency_ms,
            "last_result_count": self.last_result_count,
            "last_provider": self.last_provider,
            "last_embedding_model": self.last_embedding_model,
            "last_intent": self.last_intent,
            "warnings": list(self.warnings[-10:]),
        }


class RetrievalMetricsRecorder:
    def __init__(self) -> None:
        self.metrics = RetrievalMetrics()

    def start(self) -> float:
        return perf_counter()

    def record(
        self,
        started_at: float,
        provider: str,
        embedding_model: str,
        result_count: int,
        intent: str | None,
        missing_index: bool = False,
        warning: str | None = None,
    ) -> None:
        latency_ms = round((perf_counter() - started_at) * 1000, 2)
        self.metrics.request_count += 1
        self.metrics.total_latency_ms += latency_ms
        self.metrics.last_latency_ms = latency_ms
        self.metrics.last_result_count = result_count
        self.metrics.last_provider = provider
        self.metrics.last_embedding_model = embedding_model
        self.metrics.last_intent = intent
        if missing_index:
            self.metrics.missing_index_count += 1
        if warning:
            self.metrics.warnings.append(warning)

    def snapshot(self) -> dict[str, object]:
        return self.metrics.as_dict()


retrieval_metrics = RetrievalMetricsRecorder()
