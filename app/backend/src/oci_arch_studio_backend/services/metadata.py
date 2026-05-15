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
    oci_service_references: tuple[str, ...] = ()
    security_compliance_tags: tuple[str, ...] = ()
    migration_relevance: str = "none"
    ha_dr_relevance: str = "none"
    cost_optimization_relevance: str = "none"

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
            "oci_service_references": list(self.oci_service_references),
            "security_compliance_tags": list(self.security_compliance_tags),
            "migration_relevance": self.migration_relevance,
            "ha_dr_relevance": self.ha_dr_relevance,
            "cost_optimization_relevance": self.cost_optimization_relevance,
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
        oci_service_references=tuple(str(item) for item in metadata.get("oci_service_references", [])),
        security_compliance_tags=tuple(str(item) for item in metadata.get("security_compliance_tags", [])),
        migration_relevance=str(metadata.get("migration_relevance", "none")),
        ha_dr_relevance=str(metadata.get("ha_dr_relevance", "none")),
        cost_optimization_relevance=str(metadata.get("cost_optimization_relevance", "none")),
    ).as_dict()
    return {**metadata, **enriched}


def enrich_chunk_metadata(metadata: dict[str, Any], text: str) -> dict[str, Any]:
    normalized = text.lower()
    service_references = _infer_service_references(normalized)
    architecture_patterns = _merge_unique(
        metadata.get("architecture_patterns", []),
        _infer_patterns(normalized),
    )
    intent_tags = _merge_unique(metadata.get("intent_tags", []), _infer_intents(normalized))
    domain_tags = _merge_unique(metadata.get("domain_tags", []), _infer_domains(normalized))
    workload_types = _merge_unique(metadata.get("workload_types", []), _infer_workloads(normalized))
    security_tags = _infer_security_tags(normalized)
    enriched = {
        **metadata,
        "architecture_patterns": architecture_patterns,
        "intent_tags": intent_tags,
        "domain_tags": domain_tags,
        "workload_types": workload_types,
        "oci_service_references": service_references,
        "security_compliance_tags": security_tags,
        "migration_relevance": _relevance(normalized, ("migration", "migrate", "cutover", "rollback", "source", "target", "compatibility")),
        "ha_dr_relevance": _relevance(normalized, ("high availability", "disaster recovery", "failover", "rto", "rpo", "backup", "replication")),
        "cost_optimization_relevance": _relevance(normalized, ("cost", "budget", "right-size", "rightsizing", "lifecycle", "utilization", "tagging")),
    }
    return enrich_metadata(enriched)


SERVICE_REFERENCE_TERMS: dict[str, tuple[str, ...]] = {
    "API Gateway": ("api gateway",),
    "Audit": ("audit", "audit log"),
    "Autonomous Database": ("autonomous database", "adb"),
    "Bastion": ("bastion",),
    "Block Volume": ("block volume",),
    "CDN": ("cdn", "content delivery"),
    "Cloud Guard": ("cloud guard",),
    "Compute": ("compute", "shape", "autoscaling"),
    "Container Registry": ("container registry", "oci registry", "image registry"),
    "Data Integration": ("data integration", "etl"),
    "Data Safe": ("data safe",),
    "Database Migration": ("database migration",),
    "Database Services": ("database service", "database services", "base database"),
    "DNS": ("dns", "traffic management"),
    "Events": ("events", "event rule"),
    "FastConnect": ("fastconnect",),
    "File Storage": ("file storage",),
    "Functions": ("functions", "serverless function"),
    "Full Stack Disaster Recovery": ("full stack disaster recovery", "disaster recovery"),
    "GoldenGate": ("goldengate", "replication"),
    "Identity and Access Management": ("iam", "identity", "policy", "policies"),
    "Load Balancer": ("load balancer", "load balancing"),
    "Logging": ("logging", "logs"),
    "Monitoring": ("monitoring", "metrics", "alarms"),
    "MySQL HeatWave": ("mysql heatwave",),
    "Network Security Groups": ("network security groups", "nsg"),
    "Notifications": ("notifications", "notification topics"),
    "OCI Kubernetes Engine": ("oke", "kubernetes engine", "kubernetes"),
    "Object Storage": ("object storage", "bucket", "buckets"),
    "Resource Manager": ("resource manager", "terraform"),
    "Service Connector Hub": ("service connector", "service connector hub"),
    "Streaming": ("streaming", "stream pool"),
    "Vault": ("vault", "key management", "secrets"),
    "Virtual Cloud Network": ("vcn", "virtual cloud network"),
    "Web Application Firewall": ("waf", "web application firewall"),
}


def _infer_service_references(normalized: str) -> tuple[str, ...]:
    return tuple(
        service
        for service, terms in SERVICE_REFERENCE_TERMS.items()
        if any(term in normalized for term in terms)
    )


def _infer_patterns(normalized: str) -> tuple[str, ...]:
    pattern_map = {
        "public-ingress": ("public ingress", "internet-facing", "load balancer", "api gateway", "waf"),
        "private-subnets": ("private subnet", "private endpoint", "private access"),
        "network-isolation": ("network security", "nsg", "security list", "segmentation"),
        "high-availability": ("high availability", "highly available", "fault domain", "availability domain"),
        "disaster-recovery": ("disaster recovery", "rto", "rpo", "failover"),
        "backup-recovery": ("backup", "restore", "recovery"),
        "migration-waves": ("migration wave", "phased migration", "cutover", "rollback"),
        "operational-visibility": ("logging", "monitoring", "metrics", "alarms", "dashboard"),
        "least-privilege": ("least privilege", "iam", "policy", "compartment"),
        "key-management": ("vault", "key", "secret", "encryption"),
        "lifecycle-management": ("lifecycle", "retention", "archive"),
        "rightsizing": ("right-size", "rightsizing", "utilization"),
        "data-tier": ("database", "data tier", "replication"),
        "analytics-pipeline": ("pipeline", "etl", "streaming", "data lake"),
        "model-serving": ("model", "inference", "gpu"),
    }
    return tuple(pattern for pattern, terms in pattern_map.items() if any(term in normalized for term in terms))


def _infer_intents(normalized: str) -> tuple[str, ...]:
    intents = []
    if any(term in normalized for term in ("migration", "migrate", "cutover", "rollback", "compatibility")):
        intents.append("migration")
    if any(term in normalized for term in ("disaster recovery", "rto", "rpo", "failover", "backup", "replication")):
        intents.append("dr")
    if any(term in normalized for term in ("cost", "budget", "right-size", "utilization", "tagging")):
        intents.append("cost")
    if any(term in normalized for term in ("security", "iam", "vault", "encryption", "compliance", "audit")):
        intents.append("security")
    if any(term in normalized for term in ("logging", "monitoring", "metrics", "alarms", "observability")):
        intents.append("observability")
    if any(term in normalized for term in ("analytics", "data lake", "pipeline", "warehouse", "streaming")):
        intents.append("analytics")
    if any(term in normalized for term in ("ai", "model", "inference", "gpu")):
        intents.append("ai_ml")
    return tuple(intents)


def _infer_domains(normalized: str) -> tuple[str, ...]:
    domains = []
    if any(term in normalized for term in ("ecommerce", "storefront", "checkout", "product media")):
        domains.append("ecommerce")
    if any(term in normalized for term in ("fintech", "payment", "pci", "regulated", "audit")):
        domains.append("fintech")
    if any(term in normalized for term in ("saas", "tenant", "multi-tenant", "shared service")):
        domains.append("SaaS")
    if any(term in normalized for term in ("ai", "model", "inference", "gpu")):
        domains.append("AI/ML")
    if any(term in normalized for term in ("enterprise", "platform", "operations")):
        domains.append("enterprise")
    return tuple(domains)


def _infer_workloads(normalized: str) -> tuple[str, ...]:
    workloads = []
    if any(term in normalized for term in ("web app", "web application", "public ingress", "load balancer")):
        workloads.append("webapp")
    if any(term in normalized for term in ("ecommerce", "checkout", "storefront")):
        workloads.append("ecommerce")
    if any(term in normalized for term in ("migration", "migrate", "cutover")):
        workloads.append("migration")
    if any(term in normalized for term in ("regulated", "fintech", "pci", "rto", "rpo")):
        workloads.append("regulated-workload")
    if any(term in normalized for term in ("saas", "tenant", "multi-tenant")):
        workloads.append("saas-platform")
    if any(term in normalized for term in ("analytics", "data lake", "pipeline", "warehouse")):
        workloads.append("analytics")
    if any(term in normalized for term in ("model", "inference", "gpu")):
        workloads.append("ai-inference")
    return tuple(workloads)


def _infer_security_tags(normalized: str) -> tuple[str, ...]:
    tag_map = {
        "identity": ("iam", "identity", "policy", "federation"),
        "network-security": ("nsg", "security list", "private subnet", "segmentation"),
        "encryption": ("encryption", "key", "vault", "secret"),
        "audit": ("audit", "logging", "evidence"),
        "compliance": ("compliance", "regulated", "pci", "sox"),
        "posture-management": ("cloud guard", "security zones", "detector"),
    }
    return tuple(tag for tag, terms in tag_map.items() if any(term in normalized for term in terms))


def _relevance(normalized: str, terms: tuple[str, ...]) -> str:
    matches = sum(1 for term in terms if term in normalized)
    if matches >= 3:
        return "high"
    if matches:
        return "medium"
    return "none"


def _merge_unique(*groups: object) -> list[str]:
    values: list[str] = []
    for group in groups:
        if isinstance(group, str):
            candidates = [group]
        else:
            try:
                candidates = list(group)  # type: ignore[arg-type]
            except TypeError:
                candidates = []
        values.extend(str(item) for item in candidates if str(item))
    return list(dict.fromkeys(values))


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
    if service_domain == "resilience":
        return "resilience"
    if "cost" in intent_tags or service_domain == "cost":
        return "cost-optimization"
    if "security" in intent_tags or service_domain == "security":
        return "security"
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
