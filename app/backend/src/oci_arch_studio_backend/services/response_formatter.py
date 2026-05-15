from __future__ import annotations

from oci_arch_studio_backend.models.architecture import RetrievedSource
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
) -> str:
    service_names = sorted({source.service for source in sources if source.service})
    service_summary = ", ".join(service_names[:8]) if service_names else "insufficient retrieved service evidence"
    migration_note = (
        "Include source-to-target mapping, migration waves, validation, cutover, and rollback."
        if profile.intent.value in {"migration", "modernization", "saas_platform", "release_awareness"}
        else "No source migration path is assumed unless the workload context adds one."
    )
    lines = [
        f"1. Executive Summary\nIntent: {profile.intent.value}. {context_note}",
        f"2. Recommended OCI Services\nPrimary retrieved service candidates: {service_summary}.",
        f"3. Reference Architecture\nUse the {profile.prompt_template} focus area to shape {profile.focus}.",
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
