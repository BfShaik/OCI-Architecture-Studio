from __future__ import annotations

from dataclasses import dataclass, field

from oci_arch_studio_backend.services.architecture_heuristics import ArchitectureDomainHeuristics
from oci_arch_studio_backend.services.service_mapping import QueryServiceMapping
from oci_arch_studio_backend.services.vector_store import VectorChunk, VectorSearchFilters


@dataclass(frozen=True)
class RerankTrace:
    chunk_id: str
    title: str
    base_score: float
    final_score: float
    adjustments: dict[str, float] = field(default_factory=dict)


class RetrievalReranker:
    def rerank(
        self,
        candidates: list[tuple[VectorChunk, float]],
        *,
        filters: VectorSearchFilters,
        service_mapping: QueryServiceMapping,
        heuristics: ArchitectureDomainHeuristics,
    ) -> tuple[list[tuple[VectorChunk, float]], list[RerankTrace]]:
        traces: list[RerankTrace] = []
        reranked: list[tuple[VectorChunk, float]] = []
        mapped_services = {service.lower() for service in service_mapping.mapped_services}
        mapped_sources = {mapping.source_service for mapping in service_mapping.mappings}

        for chunk, base_score in candidates:
            adjustments = self._adjustments(
                chunk,
                filters=filters,
                mapped_services=mapped_services,
                mapped_sources=mapped_sources,
                heuristics=heuristics,
            )
            final_score = base_score + sum(adjustments.values())
            reranked.append((chunk, final_score))
            traces.append(
                RerankTrace(
                    chunk_id=chunk.id,
                    title=chunk.title,
                    base_score=round(base_score, 4),
                    final_score=round(final_score, 4),
                    adjustments={key: round(value, 4) for key, value in adjustments.items() if value},
                )
            )

        reranked.sort(key=lambda item: item[1], reverse=True)
        trace_by_chunk = {trace.chunk_id: trace for trace in traces}
        ordered_traces = [trace_by_chunk[chunk.id] for chunk, _score in reranked]
        return reranked, ordered_traces

    def _adjustments(
        self,
        chunk: VectorChunk,
        *,
        filters: VectorSearchFilters,
        mapped_services: set[str],
        mapped_sources: set[str],
        heuristics: ArchitectureDomainHeuristics,
    ) -> dict[str, float]:
        metadata = chunk.metadata
        service = str(metadata.get("service", "")).lower()
        service_domain = str(metadata.get("service_domain", "")).lower()
        category = str(metadata.get("category", "")).lower()
        intent_tags = {str(tag).lower() for tag in metadata.get("intent_tags", [])}
        patterns = {str(pattern).lower() for pattern in metadata.get("architecture_patterns", [])}
        workload_types = {str(workload).lower() for workload in metadata.get("workload_types", [])}
        domain_tags = {str(tag).lower() for tag in metadata.get("domain_tags", [])}
        topic = str(metadata.get("topic", "")).lower()
        migration_mappings = {str(key) for key in metadata.get("migration_mappings", {}).keys()}

        service_domains = {item.lower() for item in filters.service_domains}
        services = {item.lower() for item in filters.services}
        architecture_patterns = {item.lower() for item in filters.architecture_patterns}
        filter_workloads = {item.lower() for item in filters.workload_types}
        filter_domains = {item.lower() for item in filters.domain_tags}
        topics = {item.lower() for item in filters.topics}

        heuristic_domains = {item.lower() for item in heuristics.domain_tags}
        heuristic_workloads = {item.lower() for item in heuristics.workload_types}
        heuristic_patterns = {item.lower() for item in heuristics.architecture_patterns}
        heuristic_service_domains = {item.lower() for item in heuristics.service_domains}

        return {
            "intent_match": 0.18 if filters.intent and filters.intent.lower() in intent_tags else 0.0,
            "service_domain_match": 0.1 if service_domain in service_domains else 0.0,
            "service_relevance": 0.36 if service in services or service in mapped_services else 0.0,
            "architecture_pattern_match": 0.12 if patterns.intersection(architecture_patterns | heuristic_patterns) else 0.0,
            "workload_match": 0.1 if workload_types.intersection(filter_workloads | heuristic_workloads) else 0.0,
            "domain_match": 0.1 if domain_tags.intersection(filter_domains | heuristic_domains) else 0.0,
            "topic_match": 0.08 if topic and topic in topics else 0.0,
            "migration_mapping_match": 0.26 if migration_mappings.intersection(mapped_sources) else 0.0,
            "category_match": 0.05 if category and category in service_domains else 0.0,
            "heuristic_domain_match": 0.08 if service_domain in heuristic_service_domains else 0.0,
            "official_source": 0.03 if metadata.get("trust_level") == "official" else 0.0,
        }
