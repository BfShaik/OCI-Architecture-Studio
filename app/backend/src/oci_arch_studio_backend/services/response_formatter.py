from __future__ import annotations

from oci_arch_studio_backend.models.architecture import RetrievedSource, SectionCitation, SectionCitationSource
from oci_arch_studio_backend.services.architecture_heuristics import ArchitectureHeuristicClassifier
from oci_arch_studio_backend.services.architecture_patterns import ArchitecturePatternProfile, ArchitecturePatternSelector
from oci_arch_studio_backend.services.intents import IntentProfile


STANDARD_RESPONSE_SECTIONS: tuple[str, ...] = (
    "Executive Summary",
    "Recommended OCI Services",
    "Reference Architecture",
    "HA/DR Design",
    "Security Considerations",
    "Cost Optimization",
    "Risks & Assumptions",
    "Migration Strategy",
    "Observability",
    "Recommended Next Steps",
)


def format_standard_answer(
    *,
    profile: IntentProfile,
    context_note: str,
    sources: list[RetrievedSource],
    workload_context: str | None,
    question: str = "",
) -> str:
    service_names = sorted({source.service for source in sources if source.service})
    service_summary = ", ".join(service_names[:8]) if service_names else "insufficient retrieved service evidence"
    source_summary = _source_summary(sources)
    heuristics = ArchitectureHeuristicClassifier().detect(
        " ".join((question, profile.intent.value, workload_context or ""))
    )
    pattern = ArchitecturePatternSelector().select(
        question=question,
        workload_context=workload_context,
        profile=profile,
        sources=sources,
    )
    domain_guidance = " ".join(heuristics.recommendations) if heuristics.recommendations else profile.focus
    migration_note = (
        _migration_guidance(sources)
        if profile.intent.value in {"migration", "modernization", "saas_platform", "release_awareness"}
        else "No source migration path is assumed unless the workload context adds one."
    )
    service_priorities = _prioritized_services(pattern, service_names)
    design_moves = " ".join(pattern.design_moves)
    risk_moves = " ".join(pattern.risks)
    next_moves = " ".join(pattern.next_steps)
    lines = [
        f"1. Executive Summary\nIntent: {profile.intent.value}. Selected pattern: {pattern.name}. {context_note} The recommendation is grounded in retrieved OCI evidence for {source_summary}.",
        f"2. Recommended OCI Services\nPrioritize {service_priorities}. Retrieved service candidates: {service_summary}. Service choices remain provisional where the local corpus lacks specialized evidence.",
        f"3. Reference Architecture\n{design_moves} {domain_guidance}",
        f"4. HA/DR Design\n{_ha_dr_guidance(pattern, sources)}",
        f"5. Security Considerations\n{_security_guidance(pattern, sources)}",
        f"6. Cost Optimization\n{_cost_guidance(pattern, sources)}",
        f"7. Risks & Assumptions\n{risk_moves} Treat unstated traffic, data sensitivity, compliance, SLOs, and RTO/RPO targets as design assumptions until validated.",
        f"8. Migration Strategy\n{migration_note}",
        f"9. Observability\n{_observability_guidance(pattern, sources)}",
        f"10. Recommended Next Steps\n{next_moves} Confirm requirements, validate evidence coverage, fill corpus gaps, and rerun golden evals before production approval.",
    ]
    if workload_context:
        lines[0] = f"{lines[0]} Workload context: {workload_context}"
    return "\n\n".join(lines)


def _source_summary(sources: list[RetrievedSource]) -> str:
    labels = []
    for source in sources[:5]:
        label = source.service or source.title
        if source.chunk_id:
            label = f"{label} ({source.chunk_id})"
        labels.append(label)
    return ", ".join(labels) if labels else "no retrieved chunks"


def _prioritized_services(pattern: ArchitecturePatternProfile, retrieved_services: list[str]) -> str:
    ordered = [service for service in pattern.service_priorities if service in retrieved_services]
    ordered.extend(service for service in retrieved_services if service not in ordered)
    ordered.extend(service for service in pattern.service_priorities if service not in ordered)
    return ", ".join(ordered[:8])


def _ha_dr_guidance(pattern: ArchitecturePatternProfile, sources: list[RetrievedSource]) -> str:
    services = {source.service for source in sources if source.service}
    details = [
        "Use fault-domain or AD placement where available and make backup/restore expectations explicit.",
    ]
    if "Full Stack Disaster Recovery" in services:
        details.append("Use Full Stack Disaster Recovery evidence to shape failover groups and runbooks.")
    if "Database Services" in services or "Autonomous Database" in services:
        details.append("Tie database protection to backups, replication, and Data Guard-style patterns where supported by the selected service.")
    if pattern.name in {"fintech_disaster_recovery_platform", "saas_multi_region_platform"}:
        details.append("For cross-region designs, document traffic failover, data residency, RTO/RPO, and return-to-primary procedures.")
    return " ".join(details)


def _security_guidance(pattern: ArchitecturePatternProfile, sources: list[RetrievedSource]) -> str:
    services = {source.service for source in sources if source.service}
    details = [
        "Use compartment boundaries, least-privilege IAM policies, private subnets, and NSG rules to separate ingress, application, data, and operations concerns.",
    ]
    if "Vault" in services:
        details.append("Use Vault-backed key and secret controls for application, data, and DR paths.")
    if "Web Application Firewall" in services:
        details.append("Place WAF controls in front of public application paths that need edge protection.")
    if pattern.name == "saas_multi_region_platform":
        details.append("Make tenant isolation an explicit architecture control, not only an application convention.")
    return " ".join(details)


def _cost_guidance(pattern: ArchitecturePatternProfile, sources: list[RetrievedSource]) -> str:
    services = {source.service for source in sources if source.service}
    details = [
        "Balance right-sized baseline capacity with autoscaling, lifecycle controls, and observability so cost reductions do not remove resilience or security controls.",
    ]
    if "Cost Management" in services:
        details.append("Use Cost Management, budgets, and tags for service, environment, and tenant or workload attribution.")
    if "CDN" in services or "Object Storage" in services:
        details.append("Offload static artifacts and durable objects to Object Storage/CDN when access patterns justify it.")
    if pattern.name == "ai_inference_platform":
        details.append("Treat GPU or specialized shapes as measured capacity decisions, not defaults.")
    return " ".join(details)


def _observability_guidance(pattern: ArchitecturePatternProfile, sources: list[RetrievedSource]) -> str:
    services = {source.service for source in sources if source.service}
    details = [
        "Instrument logs, metrics, alarms, dashboards, and runbooks across ingress, application, data, security, and deployment signals.",
    ]
    if "Logging" in services:
        details.append("Use Logging evidence for application, audit, and platform event capture.")
    if "Monitoring" in services:
        details.append("Use Monitoring evidence for latency, error, saturation, backup, failover, and cost guardrail alarms.")
    if pattern.name == "ai_inference_platform":
        details.append("Include inference latency, queue depth, model error rate, and rollout health.")
    if pattern.name == "analytics_data_lake_platform":
        details.append("Include pipeline lag, freshness, failed batches, query performance, and storage growth.")
    return " ".join(details)


def _migration_guidance(sources: list[RetrievedSource]) -> str:
    mappings = {
        source_name: target
        for source in sources
        for source_name, target in source.migration_mappings.items()
    }
    mapping_text = (
        " Explicit mappings from retrieved metadata: "
        + "; ".join(f"{source} -> {target}" for source, target in mappings.items())
        + "."
        if mappings
        else ""
    )
    return (
        "Use phased migration waves for network/IAM foundation, platform services, data migration, validation, DNS/cutover, and rollback."
        f"{mapping_text} Validate compatibility before accepting any one-for-one service replacement."
    )


def ensure_standard_sections(answer: str, *, profile: IntentProfile, context_note: str) -> str:
    missing = [section for section in STANDARD_RESPONSE_SECTIONS if section not in answer]
    if not missing:
        return answer
    section_checklist = "\n".join(f"- {section}" for section in STANDARD_RESPONSE_SECTIONS)
    return (
        f"{answer}\n\nStandard architecture response sections expected for intent "
        f"{profile.intent.value}:\n{section_checklist}\n\nContext: {context_note}"
    )


def build_section_citations(sources: list[RetrievedSource]) -> list[SectionCitation]:
    section_hints: dict[str, tuple[str, ...]] = {
        "Executive Summary": (),
        "Recommended OCI Services": (),
        "Reference Architecture": ("architecture", "networking", "compute", "containers", "database", "storage", "edge"),
        "HA/DR Design": ("resilience", "database", "storage", "networking", "observability"),
        "Security Considerations": ("security", "networking", "observability"),
        "Cost Optimization": ("cost", "compute", "storage", "database", "edge"),
        "Risks & Assumptions": ("architecture", "security", "resilience", "cost"),
        "Migration Strategy": ("containers", "database", "storage", "edge", "networking"),
        "Observability": ("observability", "security", "database", "compute", "containers"),
        "Recommended Next Steps": (),
    }
    valid_sources = [source for source in sources if source.source_type != "missing_index"]
    citations: list[SectionCitation] = []
    for section in STANDARD_RESPONSE_SECTIONS:
        hints = set(section_hints.get(section, ()))
        matched = [
            source
            for source in valid_sources
            if not hints or source.service_domain in hints or source.service_category in hints or source.category in hints
        ]
        citations.append(
            SectionCitation(
                section=section,
                sources=[
                    SectionCitationSource(
                        chunk_id=source.chunk_id,
                        source_document=source.title,
                        oci_service_category=source.service_category or source.service_domain or source.category,
                        service=source.service,
                    )
                    for source in matched[:3]
                ],
            )
        )
    return citations
