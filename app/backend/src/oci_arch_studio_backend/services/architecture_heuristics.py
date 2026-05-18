from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArchitectureDomainHeuristics:
    domains: tuple[str, ...] = ()
    retrieval_terms: tuple[str, ...] = ()
    service_domains: tuple[str, ...] = ()
    architecture_patterns: tuple[str, ...] = ()
    workload_types: tuple[str, ...] = ()
    domain_tags: tuple[str, ...] = ()
    topics: tuple[str, ...] = ()
    recommendations: tuple[str, ...] = ()


DOMAIN_HEURISTICS: dict[str, ArchitectureDomainHeuristics] = {
    "ecommerce": ArchitectureDomainHeuristics(
        domains=("ecommerce",),
        retrieval_terms=("checkout", "seasonal traffic", "autoscaling", "CDN", "Object Storage", "WAF"),
        service_domains=("edge", "networking", "compute", "containers", "database", "storage", "observability"),
        architecture_patterns=("public-ingress", "high-availability", "autoscaling", "origin-offload", "static-assets"),
        workload_types=("ecommerce", "webapp"),
        domain_tags=("ecommerce",),
        topics=("architecture", "cost-optimization", "observability"),
        recommendations=(
            "For ecommerce, emphasize autoscaling, CDN/Object Storage offload, checkout consistency, WAF controls, and order-flow observability.",
        ),
    ),
    "fintech": ArchitectureDomainHeuristics(
        domains=("fintech",),
        retrieval_terms=("regulated", "RTO", "RPO", "audit", "encryption", "Vault", "disaster recovery"),
        service_domains=("resilience", "security", "database", "networking", "observability", "storage"),
        architecture_patterns=("disaster-recovery", "failover-runbook", "auditability", "key-management", "backup-recovery"),
        workload_types=("regulated-workload",),
        domain_tags=("fintech",),
        topics=("disaster-recovery", "observability", "architecture"),
        recommendations=(
            "For fintech, give DR, auditability, encryption, key management, least privilege, and tested failover stronger weight than generic topology guidance.",
        ),
    ),
    "saas": ArchitectureDomainHeuristics(
        domains=("SaaS",),
        retrieval_terms=(
            "ISV",
            "hosted software",
            "tenant isolation",
            "multi tenant",
            "shared services",
            "compartment strategy",
            "network topology",
            "VCN",
            "network security groups",
            "cost allocation",
            "multi region",
        ),
        service_domains=("networking", "containers", "compute", "database", "security", "observability", "cost", "edge"),
        architecture_patterns=(
            "network-isolation",
            "public-ingress",
            "least-privilege",
            "high-availability",
            "tagging",
            "operational-visibility",
            "compartment-strategy",
            "landing-zone",
        ),
        workload_types=("saas-platform", "webapp"),
        domain_tags=("SaaS",),
        topics=("architecture", "disaster-recovery", "cost-optimization", "observability"),
        recommendations=(
            "For SaaS or ISV hosting, call out tenant isolation, compartment boundaries, network topology, shared-service boundaries, data residency, noisy-neighbor risk, and cost allocation.",
        ),
    ),
    "ai_ml": ArchitectureDomainHeuristics(
        domains=("AI/ML",),
        retrieval_terms=("AI inference", "model artifacts", "GPU", "private API", "inference latency", "model rollout"),
        service_domains=("compute", "containers", "storage", "networking", "security", "observability", "cost"),
        architecture_patterns=("application-tier", "autoscaling", "operational-visibility", "key-management"),
        workload_types=("ai-inference",),
        domain_tags=("AI/ML",),
        topics=("architecture", "observability", "cost-optimization"),
        recommendations=(
            "For AI inference, keep model artifacts controlled, validate GPU/shape needs with sizing data, and monitor latency, saturation, rollout, and cost.",
        ),
    ),
    "observability": ArchitectureDomainHeuristics(
        domains=("observability",),
        retrieval_terms=("centralized logs", "metrics", "alarms", "audit trails", "dashboards", "runbooks"),
        service_domains=("observability", "security", "database", "compute", "containers"),
        architecture_patterns=("operational-visibility", "auditability", "alarms", "slo-monitoring"),
        workload_types=("enterprise-app", "regulated-workload", "saas-platform"),
        domain_tags=("enterprise", "fintech", "SaaS"),
        topics=("observability",),
        recommendations=(
            "For observability platforms, separate logs, metrics, alarms, audit evidence, retention, access control, and incident runbooks.",
        ),
    ),
    "analytics": ArchitectureDomainHeuristics(
        domains=("analytics",),
        retrieval_terms=("data pipeline", "data lake", "storage throughput", "pipeline scaling", "data lifecycle", "query performance"),
        service_domains=("storage", "database", "observability", "security", "cost"),
        architecture_patterns=("data-tier", "managed-database", "lifecycle-management", "operational-visibility"),
        workload_types=("analytics",),
        domain_tags=("enterprise",),
        topics=("architecture", "cost-optimization", "observability"),
        recommendations=(
            "For analytics, emphasize storage throughput, data lifecycle, pipeline scaling, governance, freshness, and query-performance observability.",
        ),
    ),
}


class ArchitectureHeuristicClassifier:
    def detect(self, text: str) -> ArchitectureDomainHeuristics:
        normalized = text.lower()
        selected: list[ArchitectureDomainHeuristics] = []
        if any(token in normalized for token in ("ecommerce", "e-commerce", "checkout", "storefront", "product media")):
            selected.append(DOMAIN_HEURISTICS["ecommerce"])
        if any(token in normalized for token in ("fintech", "payment", "regulated", "pci", "audit", "rto", "rpo")):
            selected.append(DOMAIN_HEURISTICS["fintech"])
        if any(
            token in normalized
            for token in (
                "saas",
                "isv",
                "independent software vendor",
                "software vendor",
                "hosted software",
                "hosted application",
                "customer tenant",
                "tenant",
                "multi-tenant",
                "multi tenant",
                "shared services",
            )
        ):
            selected.append(DOMAIN_HEURISTICS["saas"])
        if any(token in normalized for token in ("ai/ml", "ai inference", "inference", "model artifact", "sagemaker", "gpu")):
            selected.append(DOMAIN_HEURISTICS["ai_ml"])
        if any(token in normalized for token in ("observability", "logging", "monitoring", "metrics", "alarms", "dashboard", "audit trail")):
            selected.append(DOMAIN_HEURISTICS["observability"])
        if any(token in normalized for token in ("analytics", "data platform", "data lake", "pipeline", "warehouse", "glue")):
            selected.append(DOMAIN_HEURISTICS["analytics"])
        return self._merge(selected)

    def _merge(self, heuristics: list[ArchitectureDomainHeuristics]) -> ArchitectureDomainHeuristics:
        return ArchitectureDomainHeuristics(
            domains=self._unique(item for heuristic in heuristics for item in heuristic.domains),
            retrieval_terms=self._unique(item for heuristic in heuristics for item in heuristic.retrieval_terms),
            service_domains=self._unique(item for heuristic in heuristics for item in heuristic.service_domains),
            architecture_patterns=self._unique(item for heuristic in heuristics for item in heuristic.architecture_patterns),
            workload_types=self._unique(item for heuristic in heuristics for item in heuristic.workload_types),
            domain_tags=self._unique(item for heuristic in heuristics for item in heuristic.domain_tags),
            topics=self._unique(item for heuristic in heuristics for item in heuristic.topics),
            recommendations=self._unique(item for heuristic in heuristics for item in heuristic.recommendations),
        )

    def _unique(self, items) -> tuple[str, ...]:
        return tuple(dict.fromkeys(item for item in items if item))
