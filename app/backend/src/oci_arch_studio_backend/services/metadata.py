from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


METADATA_SCHEMA_VERSION = "2026-05-oci-advisory-v2"


@dataclass(frozen=True)
class OciChunkMetadata:
    service: str
    service_domain: str
    service_category: str = "general"
    category: str = "general"
    topic: str = "architecture"
    workload_types: tuple[str, ...] = ()
    workload: str | None = None
    domain_tags: tuple[str, ...] = ()
    domain: str | None = None
    intent_tags: tuple[str, ...] = ()
    architecture_patterns: tuple[str, ...] = ()
    pattern: str | None = None
    migration_mappings: dict[str, str] = field(default_factory=dict)
    ha_dr_tags: tuple[str, ...] = ()
    cost_optimization_tags: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "metadata_schema_version": METADATA_SCHEMA_VERSION,
            "service": self.service,
            "service_domain": self.service_domain,
            "service_category": self.service_category,
            "category": self.category,
            "topic": self.topic,
            "workload_types": list(self.workload_types),
            "workload": self.workload,
            "domain_tags": list(self.domain_tags),
            "domain": self.domain,
            "intent_tags": list(self.intent_tags),
            "architecture_patterns": list(self.architecture_patterns),
            "pattern": self.pattern,
            "migration_mappings": dict(self.migration_mappings),
            "ha_dr_tags": list(self.ha_dr_tags),
            "cost_optimization_tags": list(self.cost_optimization_tags),
        }


def enrich_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    intent_tags = tuple(str(tag) for tag in metadata.get("intent_tags", []))
    patterns = tuple(str(pattern) for pattern in metadata.get("architecture_patterns", []))
    service = str(metadata.get("service") or "Unknown")
    service_domain = str(metadata.get("service_domain") or "general")

    domain_tags = _infer_domain_tags(service, service_domain, intent_tags, patterns)
    workload_types = _infer_workload_types(service, service_domain, intent_tags, patterns)
    ha_dr_tags = tuple(tag for tag in patterns if tag in HA_DR_PATTERN_TAGS)
    cost_tags = tuple(tag for tag in patterns if tag in COST_PATTERN_TAGS)

    category = _infer_category(service_domain, intent_tags)
    topic = _infer_topic(service_domain, intent_tags, patterns)
    enriched = OciChunkMetadata(
        service=service,
        service_domain=service_domain,
        service_category=service_domain,
        category=category,
        topic=topic,
        workload_types=workload_types,
        workload=workload_types[0] if workload_types else None,
        domain_tags=domain_tags,
        domain=domain_tags[0] if domain_tags else None,
        intent_tags=intent_tags,
        architecture_patterns=patterns,
        pattern=patterns[0] if patterns else None,
        migration_mappings=_migration_mappings_for_service(service),
        ha_dr_tags=ha_dr_tags,
        cost_optimization_tags=cost_tags,
    ).as_dict()
    return {**metadata, **enriched}


HA_DR_PATTERN_TAGS = {
    "backup-recovery",
    "disaster-recovery",
    "failover-runbook",
    "high-availability",
    "operational-visibility",
}

COST_PATTERN_TAGS = {
    "autoscaling",
    "budgets",
    "lifecycle-management",
    "origin-offload",
    "rightsizing",
    "tagging",
}


def _infer_category(service_domain: str, intent_tags: tuple[str, ...]) -> str:
    if "migration" in intent_tags:
        return "migration"
    if "cost" in intent_tags or service_domain == "cost":
        return "cost-optimization"
    if "security" in intent_tags or service_domain == "security":
        return "security"
    if service_domain == "resilience":
        return "resilience"
    return service_domain


def _infer_topic(service_domain: str, intent_tags: tuple[str, ...], patterns: tuple[str, ...]) -> str:
    if "disaster-recovery" in patterns or "dr" in intent_tags:
        return "disaster-recovery"
    if "migration" in intent_tags:
        return "migration"
    if "cost" in intent_tags:
        return "cost-optimization"
    if service_domain == "observability":
        return "observability"
    return "architecture"


def _infer_domain_tags(
    service: str,
    service_domain: str,
    intent_tags: tuple[str, ...],
    patterns: tuple[str, ...],
) -> tuple[str, ...]:
    tags = {"enterprise"}
    if service_domain in {"edge", "storage", "networking"} or "public-ingress" in patterns:
        tags.add("ecommerce")
        tags.add("SaaS")
    if "dr" in intent_tags or service_domain in {"resilience", "security"}:
        tags.add("fintech")
    if service_domain in {"compute", "containers", "storage", "observability"}:
        tags.add("AI/ML")
    if service_domain in {"containers", "database", "networking", "edge"}:
        tags.add("SaaS")
    if service == "Cost Management":
        tags.update({"ecommerce", "SaaS", "AI/ML"})
    return tuple(sorted(tags))


def _infer_workload_types(
    service: str,
    service_domain: str,
    intent_tags: tuple[str, ...],
    patterns: tuple[str, ...],
) -> tuple[str, ...]:
    workloads = {"enterprise-app"}
    if service_domain in {"edge", "networking", "compute", "database", "storage"}:
        workloads.add("webapp")
        workloads.add("ecommerce")
    if "migration" in intent_tags:
        workloads.add("migration")
    if "dr" in intent_tags or "disaster-recovery" in patterns:
        workloads.add("regulated-workload")
    if service_domain in {"containers", "compute", "storage", "observability"}:
        workloads.add("ai-inference")
    if service_domain in {"containers", "database", "networking", "edge", "cost"}:
        workloads.add("saas-platform")
    if service_domain in {"database", "storage", "observability"}:
        workloads.add("analytics")
    if service == "Cost Management":
        workloads.add("cost-optimized-webapp")
    return tuple(sorted(workloads))


def _migration_mappings_for_service(service: str) -> dict[str, str]:
    if service == "OCI Kubernetes Engine":
        return {"EKS": "OKE", "Fargate": "OKE Virtual Nodes"}
    if service in {"Database Services", "Autonomous Database", "Database Migration"}:
        return {"RDS": "OCI Base Database / Autonomous Database"}
    if service == "Object Storage":
        return {"S3": "OCI Object Storage"}
    if service == "CDN":
        return {"CloudFront": "OCI CDN"}
    return {}
