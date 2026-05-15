from __future__ import annotations

from oci_arch_studio_backend.models.architecture import RetrievedSource, SectionCitation, SectionCitationSource
from oci_arch_studio_backend.services.architecture_heuristics import ArchitectureHeuristicClassifier
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
    heuristics = ArchitectureHeuristicClassifier().detect(
        " ".join((question, profile.intent.value, workload_context or ""))
    )
    domain_guidance = " ".join(heuristics.recommendations) if heuristics.recommendations else profile.focus
    migration_note = (
        "Include source-to-target mapping, migration waves, validation, cutover, and rollback."
        if profile.intent.value in {"migration", "modernization", "saas_platform", "release_awareness"}
        else "No source migration path is assumed unless the workload context adds one."
    )
    lines = [
        f"1. Executive Summary\nIntent: {profile.intent.value}. {context_note}",
        f"2. Recommended OCI Services\nPrimary retrieved service candidates: {service_summary}.",
        f"3. Reference Architecture\nUse the {profile.prompt_template} focus area to shape {profile.focus}. {domain_guidance}",
        "4. HA/DR Design\nTie availability and recovery choices to explicit RTO/RPO, fault-domain, AD, region, backup, and failover assumptions.",
        "5. Security Considerations\nApply least privilege, private networking, encryption, secrets management, audit logging, and compliance evidence where required.",
        "6. Cost Optimization\nRightsize capacity, use autoscaling and lifecycle controls where supported, and preserve required resilience and monitoring.",
        "7. Risks & Assumptions\nTreat unstated workload, traffic, data, compliance, and recovery requirements as assumptions that must be validated.",
        f"8. Migration Strategy\n{migration_note}",
        "9. Observability\nInclude logs, metrics, alarms, dashboards, and operational runbooks for application, infrastructure, database, and security signals.",
        "10. Recommended Next Steps\nConfirm requirements, validate evidence coverage, fill corpus gaps, and rerun golden evals before production approval.",
    ]
    if workload_context:
        lines[0] = f"{lines[0]} Workload context: {workload_context}"
    return "\n\n".join(lines)


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
