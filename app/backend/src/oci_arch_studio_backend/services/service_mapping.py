from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceMapping:
    source_service: str
    target_services: tuple[str, ...]
    retrieval_terms: tuple[str, ...]


@dataclass(frozen=True)
class QueryServiceMapping:
    mappings: tuple[ServiceMapping, ...]

    @property
    def mapped_services(self) -> tuple[str, ...]:
        services: list[str] = []
        for mapping in self.mappings:
            services.extend(mapping.target_services)
        return tuple(dict.fromkeys(services))

    @property
    def retrieval_terms(self) -> tuple[str, ...]:
        terms: list[str] = []
        for mapping in self.mappings:
            terms.extend(mapping.retrieval_terms)
        return tuple(dict.fromkeys(terms))

    def summary(self) -> str:
        if not self.mappings:
            return "No source cloud service mappings detected."
        return "; ".join(
            f"{mapping.source_service} -> {', '.join(mapping.target_services)}"
            for mapping in self.mappings
        )


AWS_TO_OCI_MAPPINGS: tuple[ServiceMapping, ...] = (
    ServiceMapping(
        source_service="EKS",
        target_services=("OCI Kubernetes Engine",),
        retrieval_terms=("OKE", "OCI Kubernetes Engine", "Kubernetes", "container platform", "node pools"),
    ),
    ServiceMapping(
        source_service="RDS",
        target_services=("Database Services", "Autonomous Database"),
        retrieval_terms=("OCI Base Database", "Autonomous Database", "Database Migration", "database engine compatibility"),
    ),
    ServiceMapping(
        source_service="S3",
        target_services=("Object Storage",),
        retrieval_terms=("Object Storage", "S3-compatible", "buckets", "static assets", "backups"),
    ),
    ServiceMapping(
        source_service="CloudFront",
        target_services=("CDN",),
        retrieval_terms=("OCI CDN", "edge delivery", "origin offload", "static asset delivery"),
    ),
    ServiceMapping(
        source_service="Route53",
        target_services=("OCI DNS",),
        retrieval_terms=("OCI DNS", "DNS cutover", "traffic management", "failover"),
    ),
    ServiceMapping(
        source_service="Fargate",
        target_services=("OKE Virtual Nodes", "OCI Kubernetes Engine"),
        retrieval_terms=("OKE Virtual Nodes", "serverless containers", "container workload migration"),
    ),
)


class OciServiceMapper:
    def map_text(self, text: str) -> QueryServiceMapping:
        normalized = text.lower()
        detected = tuple(
            mapping
            for mapping in AWS_TO_OCI_MAPPINGS
            if mapping.source_service.lower() in normalized
        )
        return QueryServiceMapping(mappings=detected)
