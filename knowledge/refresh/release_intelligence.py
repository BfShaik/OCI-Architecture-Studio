from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CHANGE_CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "new-service-feature": ("new", "now supports", "adds", "available", "introduces", "launch"),
    "feature-enhancement": ("enhance", "improve", "updated", "supports", "expanded", "additional"),
    "deprecated-behavior": ("deprecat", "retire", "removed", "end of support", "no longer"),
    "pricing-cost-change": ("price", "pricing", "cost", "billing", "budget", "meter", "free tier"),
    "security-change": ("security", "vulnerability", "iam", "policy", "vault", "secret", "encrypt", "key"),
    "ha-dr-change": ("disaster", "failover", "replication", "backup", "availability", "recovery", "rto", "rpo"),
    "observability-change": ("logging", "monitoring", "metrics", "alarm", "audit", "events", "connector"),
    "migration-relevance": ("migration", "compatibility", "s3", "api", "import", "export", "kubernetes", "rds", "eks"),
    "compatibility-risk": ("compatibility", "breaking", "behavior", "endpoint", "url", "renamed", "deprecated"),
}

WORKLOAD_KEYWORDS: dict[str, tuple[str, ...]] = {
    "webapp": ("web", "load balancer", "cdn", "waf", "api gateway"),
    "migration": ("migration", "compatibility", "import", "export", "s3", "rds", "eks"),
    "regulated-workload": ("security", "audit", "compliance", "vault", "iam", "data safe"),
    "saas-platform": ("tenant", "saas", "shared service", "cost allocation", "region"),
    "ai-inference": ("ai", "model", "inference", "gpu", "data science"),
    "analytics": ("analytics", "pipeline", "data lake", "streaming", "warehouse"),
    "cost-optimized-webapp": ("cost", "budget", "pricing", "billing", "right-size"),
}

DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "ecommerce": ("cdn", "waf", "object storage", "load balancer", "web"),
    "fintech": ("security", "audit", "compliance", "vault", "data safe", "encryption"),
    "SaaS": ("tenant", "saas", "shared service", "cost allocation"),
    "AI/ML": ("ai", "model", "inference", "gpu", "data science"),
    "enterprise": ("iam", "logging", "monitoring", "migration", "database", "network"),
}

DOMAIN_TO_SOURCE_IDS: dict[str, tuple[str, ...]] = {
    "security": ("oci-security-services-overview", "oci-iam-overview", "oci-vault-overview", "oci-cloud-guard-overview"),
    "storage": ("oci-object-storage-overview", "oci-block-volume-overview", "oci-file-storage-overview"),
    "networking": ("oci-vcn-overview", "oci-load-balancer-overview", "oci-dns-overview", "oci-fastconnect-overview"),
    "database": ("oci-database-overview", "oci-autonomous-database-overview", "oci-mysql-heatwave-overview"),
    "observability": ("oci-logging-overview", "oci-monitoring-overview", "oci-audit-overview", "oci-service-connector-hub-overview"),
    "resilience": ("oci-full-stack-dr-overview", "oci-database-overview", "oci-object-storage-overview"),
    "cost": ("oci-cost-management-overview", "oci-compute-overview", "oci-object-storage-overview"),
    "containers": ("oci-kubernetes-engine-overview", "oci-container-registry-overview"),
    "ai_ml": ("oci-data-science-overview", "oci-reference-ai-inference", "oci-compute-overview"),
    "analytics": ("oci-data-integration-overview", "oci-streaming-overview", "oci-goldengate-overview", "oci-object-storage-overview"),
}

CHANGE_TO_IMPACT_TAG: dict[str, str] = {
    "security-change": "security",
    "ha-dr-change": "dr",
    "pricing-cost-change": "cost",
    "observability-change": "observability",
    "migration-relevance": "migration",
    "compatibility-risk": "migration",
    "new-service-feature": "architecture",
    "feature-enhancement": "architecture",
    "deprecated-behavior": "architecture",
}

CHANGE_TO_SOURCE_IDS: dict[str, tuple[str, ...]] = {
    "observability-change": ("oci-logging-overview", "oci-monitoring-overview", "oci-audit-overview"),
    "ha-dr-change": ("oci-full-stack-dr-overview", "oci-database-overview", "oci-dns-overview"),
    "pricing-cost-change": ("oci-cost-management-overview",),
    "security-change": ("oci-security-services-overview", "oci-iam-overview", "oci-vault-overview"),
    "migration-relevance": ("oci-database-migration-overview", "oci-kubernetes-engine-overview"),
    "compatibility-risk": ("oci-database-migration-overview", "oci-object-storage-overview"),
}

SERVICE_TO_SOURCE_HINTS: dict[str, tuple[str, ...]] = {
    "API Gateway": ("oci-api-gateway-overview",),
    "Audit": ("oci-audit-overview",),
    "Autonomous Database": ("oci-autonomous-database-overview", "oci-database-overview"),
    "Cloud Guard": ("oci-cloud-guard-overview", "oci-security-services-overview"),
    "Compute": ("oci-compute-overview",),
    "Data Integration": ("oci-data-integration-overview",),
    "Data Safe": ("oci-data-safe-overview", "oci-security-services-overview"),
    "Database Migration": ("oci-database-migration-overview",),
    "Database Services": ("oci-database-overview",),
    "DNS": ("oci-dns-overview",),
    "FastConnect": ("oci-fastconnect-overview",),
    "Full Stack Disaster Recovery": ("oci-full-stack-dr-overview",),
    "GoldenGate": ("oci-goldengate-overview",),
    "Load Balancer": ("oci-load-balancer-overview",),
    "Logging": ("oci-logging-overview",),
    "Monitoring": ("oci-monitoring-overview",),
    "MySQL HeatWave": ("oci-mysql-heatwave-overview",),
    "Network Security Groups": ("oci-network-security-groups-overview",),
    "Object Storage": ("oci-object-storage-overview",),
    "OCI Kubernetes Engine": ("oci-kubernetes-engine-overview",),
    "Secret Management": ("oci-vault-overview", "oci-security-services-overview"),
    "Vault": ("oci-vault-overview", "oci-security-services-overview"),
    "Virtual Cloud Network": ("oci-vcn-overview",),
    "Web Application Firewall": ("oci-waf-overview",),
}


def normalize_release_item(release: dict[str, Any]) -> dict[str, Any]:
    text = " ".join(
        str(release.get(key, ""))
        for key in ("title", "summary", "service", "service_domain")
    ).lower()
    change_categories = _matches(text, CHANGE_CATEGORY_KEYWORDS) or ["feature-enhancement"]
    workload_relevance = _matches(text, WORKLOAD_KEYWORDS)
    architecture_domains = _matches(text, DOMAIN_KEYWORDS)
    impact_tags = sorted(set(str(tag) for tag in release.get("impact_tags", [])) | {CHANGE_TO_IMPACT_TAG[item] for item in change_categories})
    importance = classify_importance(text, change_categories, impact_tags)
    recommendation_affecting = importance in {"review", "high"} or any(
        category in change_categories
        for category in ("deprecated-behavior", "pricing-cost-change", "security-change", "ha-dr-change", "compatibility-risk")
    )
    enriched = {
        **release,
        "change_categories": change_categories,
        "impact_tags": impact_tags,
        "impact_level": importance,
        "severity": importance,
        "workload_relevance": workload_relevance,
        "architecture_domain_relevance": architecture_domains,
        "recommendation_affecting": recommendation_affecting,
        "retrieval_affecting": bool(recommendation_affecting or workload_relevance or architecture_domains),
        "metadata_update_required": bool(recommendation_affecting or architecture_domains),
        "prompt_template_review_required": any(category in change_categories for category in ("deprecated-behavior", "compatibility-risk")),
        "service_mapping_review_required": "migration-relevance" in change_categories or "compatibility-risk" in change_categories,
        "regression_required": importance in {"review", "high"} or recommendation_affecting,
    }
    return enriched


def classify_importance(text: str, change_categories: list[str], impact_tags: list[str]) -> str:
    if any(token in text for token in ("breaking", "critical", "vulnerability", "deprecated", "end of support", "removed")):
        return "high"
    if any(category in change_categories for category in ("security-change", "ha-dr-change", "compatibility-risk", "deprecated-behavior")):
        return "review"
    if any(tag in impact_tags for tag in ("security", "dr", "migration", "cost")):
        return "review"
    return "informational"


def impact_analysis(
    *,
    releases: list[dict[str, Any]],
    knowledge_index: dict[str, Any],
    eval_case_paths: list[Path],
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    policy = policy or {}
    affected_source_ids = set()
    affected_chunk_ids = set()
    affected_services = set()
    change_categories = set()
    impacted_eval_cases: dict[str, list[str]] = {}
    source_to_chunks = _source_to_chunks(knowledge_index)
    service_to_chunks = _service_to_chunks(knowledge_index)
    service_to_sources = policy.get("service_to_source_ids", {})
    impact_to_sources = policy.get("impact_to_source_ids", {})

    for release in releases:
        normalized = normalize_release_item(release)
        services = [str(service) for service in normalized.get("services", [])]
        if normalized.get("service"):
            services.append(str(normalized["service"]))
        services = list(dict.fromkeys(services))
        affected_services.update(services)
        change_categories.update(str(category) for category in normalized.get("change_categories", []))

        release_source_ids = set()
        for service in services:
            release_source_ids.update(str(item) for item in service_to_sources.get(service, []))
            release_source_ids.update(SERVICE_TO_SOURCE_HINTS.get(service, ()))
        service_domain = str(normalized.get("service_domain", ""))
        release_source_ids.update(DOMAIN_TO_SOURCE_IDS.get(service_domain, ()))
        for tag in normalized.get("impact_tags", []):
            release_source_ids.update(str(item) for item in impact_to_sources.get(str(tag), []))
        for category in normalized.get("change_categories", []):
            release_source_ids.update(CHANGE_TO_SOURCE_IDS.get(str(category), ()))

        affected_source_ids.update(release_source_ids)
        for source_id in release_source_ids:
            affected_chunk_ids.update(source_to_chunks.get(source_id, ()))
        for service in services:
            affected_chunk_ids.update(service_to_chunks.get(service.lower(), ()))

        for case_id in impacted_eval_case_ids(normalized, eval_case_paths):
            impacted_eval_cases.setdefault(case_id, []).append(str(normalized.get("id") or normalized.get("title")))

    actions = []
    if affected_source_ids:
        actions.append("selective_reindex")
        actions.append("refresh_embeddings")
    if any(category in change_categories for category in ("security-change", "ha-dr-change", "pricing-cost-change", "compatibility-risk")):
        actions.append("retag_chunks")
    if impacted_eval_cases:
        actions.append("targeted_regression")
    if any(normalize_release_item(release).get("prompt_template_review_required") for release in releases):
        actions.append("prompt_template_review")
    if any(normalize_release_item(release).get("service_mapping_review_required") for release in releases):
        actions.append("service_mapping_review")

    return {
        "release_count": len(releases),
        "affected_services": sorted(affected_services),
        "affected_source_ids": sorted(affected_source_ids),
        "affected_chunk_ids": sorted(affected_chunk_ids),
        "change_categories": sorted(change_categories),
        "impacted_eval_cases": dict(sorted(impacted_eval_cases.items())),
        "refresh_actions": sorted(set(actions)),
        "metadata_update_required": "retag_chunks" in actions,
        "regression_required": "targeted_regression" in actions or any(normalize_release_item(release).get("regression_required") for release in releases),
        "unresolved_risks": unresolved_risks(releases, affected_source_ids, impacted_eval_cases),
    }


def apply_release_overlay(
    knowledge_index: dict[str, Any],
    releases: list[dict[str, Any]],
    impact: dict[str, Any],
) -> dict[str, Any]:
    affected_sources = set(str(item) for item in impact.get("affected_source_ids", []))
    affected_chunks = set(str(item) for item in impact.get("affected_chunk_ids", []))
    release_ids = [str(item.get("id") or item.get("title")) for item in releases]
    categories = sorted({category for release in releases for category in normalize_release_item(release).get("change_categories", [])})
    valid_from = sorted(
        {
            str(item.get("valid_from") or item.get("release_date"))
            for item in releases
            if item.get("valid_from") or item.get("release_date")
        }
    )
    updated_chunks = []
    for chunk in knowledge_index.get("chunks", []):
        metadata = dict(chunk.get("metadata", {}))
        if chunk.get("source_id") in affected_sources or chunk.get("id") in affected_chunks:
            metadata["release_impacted"] = True
            metadata["release_item_ids"] = sorted(set(metadata.get("release_item_ids", [])) | set(release_ids))
            metadata["release_change_categories"] = sorted(set(metadata.get("release_change_categories", [])) | set(categories))
            metadata["current_knowledge"] = True
            metadata["historical_knowledge"] = False
            metadata["valid_from"] = valid_from[0] if valid_from else metadata.get("valid_from")
            metadata["valid_to"] = None
            metadata["refresh_reason"] = "release-impact"
            chunk = {**chunk, "metadata": metadata}
        updated_chunks.append(chunk)
    return {**knowledge_index, "chunks": updated_chunks, "release_overlay": impact}


def impacted_eval_case_ids(release: dict[str, Any], eval_case_paths: list[Path]) -> list[str]:
    terms = {
        str(release.get("service", "")).lower(),
        str(release.get("service_domain", "")).lower(),
        *[str(tag).lower() for tag in release.get("impact_tags", [])],
        *[str(category).lower() for category in release.get("change_categories", [])],
        *[str(workload).lower() for workload in release.get("workload_relevance", [])],
        *[str(domain).lower() for domain in release.get("architecture_domain_relevance", [])],
    }
    terms = {term for term in terms if len(term) >= 3}
    impacted = []
    for path in eval_case_paths:
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as file:
            for line in file:
                if not line.strip():
                    continue
                case = json.loads(line)
                haystack = json.dumps(case).lower()
                if any(term in haystack for term in terms):
                    impacted.append(str(case.get("id", path.name)))
    return sorted(set(impacted))


def unresolved_risks(
    releases: list[dict[str, Any]],
    affected_source_ids: set[str],
    impacted_eval_cases: dict[str, list[str]],
) -> list[str]:
    risks = []
    if releases and not affected_source_ids:
        risks.append("No affected knowledge sources were mapped for one or more release items.")
    if any(normalize_release_item(release).get("regression_required") for release in releases) and not impacted_eval_cases:
        risks.append("Release appears regression-relevant, but no targeted eval cases were matched.")
    if any(normalize_release_item(release).get("service_mapping_review_required") for release in releases):
        risks.append("Migration or compatibility release may require source-service mapping review.")
    return risks


def _matches(text: str, mapping: dict[str, tuple[str, ...]]) -> list[str]:
    return [label for label, keywords in mapping.items() if any(keyword in text for keyword in keywords)]


def _source_to_chunks(knowledge_index: dict[str, Any]) -> dict[str, tuple[str, ...]]:
    result: dict[str, list[str]] = {}
    for chunk in knowledge_index.get("chunks", []):
        source_id = str(chunk.get("source_id", ""))
        if source_id:
            result.setdefault(source_id, []).append(str(chunk.get("id")))
    return {key: tuple(values) for key, values in result.items()}


def _service_to_chunks(knowledge_index: dict[str, Any]) -> dict[str, tuple[str, ...]]:
    result: dict[str, list[str]] = {}
    for chunk in knowledge_index.get("chunks", []):
        service = str(chunk.get("metadata", {}).get("service", "")).lower()
        if service:
            result.setdefault(service, []).append(str(chunk.get("id")))
    return {key: tuple(values) for key, values in result.items()}
