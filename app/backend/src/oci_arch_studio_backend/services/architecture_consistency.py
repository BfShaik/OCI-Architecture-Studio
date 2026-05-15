from __future__ import annotations

import re

from oci_arch_studio_backend.models.architecture import ArchitectureConsistencyFinding, RetrievedSource
from oci_arch_studio_backend.services.intents import Intent, IntentProfile
from oci_arch_studio_backend.services.service_mapping import OciServiceMapper


class ArchitectureConsistencyValidator:
    """Runs lightweight pre-response checks for architecture recommendation coherence."""

    def validate(
        self,
        *,
        question: str,
        workload_context: str | None,
        profile: IntentProfile,
        answer: str,
        recommendations: list[str],
        sources: list[RetrievedSource],
    ) -> list[ArchitectureConsistencyFinding]:
        combined = " ".join(part for part in (question, workload_context, answer, *recommendations) if part)
        normalized = combined.lower()
        findings: list[ArchitectureConsistencyFinding] = []
        findings.extend(self._conflicting_requirements(normalized))
        findings.extend(self._migration_mapping_gaps(question, workload_context, sources))
        findings.extend(self._ha_dr_alignment(profile, normalized, sources))
        findings.extend(self._observability_coverage(normalized, sources))
        findings.extend(self._security_coverage(normalized, sources))
        findings.extend(self._unsupported_combinations(normalized))
        return findings

    def _conflicting_requirements(self, normalized: str) -> list[ArchitectureConsistencyFinding]:
        findings: list[ArchitectureConsistencyFinding] = []
        conflict_checks = (
            (
                "conflicting_availability_claim",
                ("zero downtime", "guarantee"),
                "Zero-downtime guarantees conflict with realistic OCI HA/DR guidance.",
                "Express availability as SLO, RTO, RPO, failover, and tested recovery targets instead of a guarantee.",
            ),
            (
                "missing_backup_conflict",
                ("no backup", "no backups"),
                "The request conflicts with enterprise recovery expectations by excluding backups.",
                "Retain backup, restore, and replication controls appropriate to the data tier.",
            ),
            (
                "missing_monitoring_conflict",
                ("no monitoring", "without monitoring"),
                "The request conflicts with operational readiness by excluding monitoring.",
                "Keep logs, metrics, alarms, dashboards, and runbooks in scope.",
            ),
        )
        for check, tokens, message, recommendation in conflict_checks:
            if any(token in normalized for token in tokens):
                findings.append(
                    ArchitectureConsistencyFinding(
                        check=check,
                        severity="warning",
                        message=message,
                        recommendation=recommendation,
                    )
                )
        return findings

    def _migration_mapping_gaps(
        self,
        question: str,
        workload_context: str | None,
        sources: list[RetrievedSource],
    ) -> list[ArchitectureConsistencyFinding]:
        mapping = OciServiceMapper().map_text(" ".join(part for part in (question, workload_context) if part))
        if not mapping.mappings:
            return []
        mapped_targets = set(mapping.mapped_services)
        source_services = {source.service for source in sources if source.service}
        missing_targets = sorted(service for service in mapped_targets if service not in source_services)
        if not missing_targets:
            return []
        return [
            ArchitectureConsistencyFinding(
                check="migration_mapping_coverage",
                severity="info",
                message="Some detected source-service mappings are not represented in the final retrieved OCI evidence.",
                recommendation=(
                    "Validate mapped services before final design: "
                    + ", ".join(missing_targets[:6])
                    + "."
                ),
            )
        ]

    def _ha_dr_alignment(
        self,
        profile: IntentProfile,
        normalized: str,
        sources: list[RetrievedSource],
    ) -> list[ArchitectureConsistencyFinding]:
        needs_dr = (
            profile.intent in {Intent.DR, Intent.SAAS_PLATFORM}
            or any(token in normalized for token in ("fintech", "regulated", "multi-region", "rto", "rpo", "disaster recovery"))
        )
        if not needs_dr:
            return []
        source_text = self._source_text(sources)
        has_data_protection = any(
            token in f"{normalized} {source_text}"
            for token in ("backup", "replication", "data guard", "full stack disaster recovery", "rto", "rpo")
        )
        if has_data_protection:
            return []
        return [
            ArchitectureConsistencyFinding(
                check="ha_dr_data_alignment",
                severity="warning",
                message="The architecture needs DR treatment, but retrieved/synthesized guidance does not clearly align database recovery, backups, or replication.",
                recommendation="Add explicit data-tier RTO/RPO, backup/restore, replication, failover, and return-to-primary validation.",
                source_chunk_ids=self._chunk_ids(sources),
            )
        ]

    def _observability_coverage(
        self,
        normalized: str,
        sources: list[RetrievedSource],
    ) -> list[ArchitectureConsistencyFinding]:
        service_names = {source.service for source in sources if source.service}
        has_observability = {"Logging", "Monitoring"} & service_names or all(
            token in normalized for token in ("logging", "monitoring")
        )
        if has_observability:
            return []
        return [
            ArchitectureConsistencyFinding(
                check="observability_coverage",
                severity="info",
                message="No strong Logging or Monitoring evidence is present in the selected architecture context.",
                recommendation="Add logs, metrics, alarms, dashboards, and runbook coverage before treating the design as implementation-ready.",
            )
        ]

    def _security_coverage(
        self,
        normalized: str,
        sources: list[RetrievedSource],
    ) -> list[ArchitectureConsistencyFinding]:
        service_names = {source.service for source in sources if source.service}
        security_services = {"Vault", "Identity and Access Management", "Network Security Groups", "Web Application Firewall"}
        has_security = bool(security_services & service_names) or any(
            token in normalized
            for token in ("least-privilege", "iam", "vault", "nsg", "private subnet", "compartment")
        )
        if has_security:
            return []
        return [
            ArchitectureConsistencyFinding(
                check="security_coverage",
                severity="warning",
                message="Security boundaries are not sufficiently represented in the selected evidence or recommendations.",
                recommendation="Define IAM, compartments, private networking, encryption, and audit controls explicitly.",
            )
        ]

    def _unsupported_combinations(self, normalized: str) -> list[ArchitectureConsistencyFinding]:
        if re.search(r"\b(serverless|functions|fargate)\b", normalized) and re.search(
            r"\b(persistent state|stateful database|local state)\b",
            normalized,
        ):
            return [
                ArchitectureConsistencyFinding(
                    check="serverless_state_conflict",
                    severity="warning",
                    message="Serverless compute guidance appears near persistent-state requirements.",
                    recommendation="Keep persistent state in managed data services and validate any serverless workload boundaries.",
                )
            ]
        return []

    def _source_text(self, sources: list[RetrievedSource]) -> str:
        return " ".join(
            " ".join(
                (
                    source.title,
                    source.summary,
                    source.service or "",
                    source.service_domain or "",
                    source.service_category or "",
                    " ".join(source.ha_dr_tags),
                )
            ).lower()
            for source in sources
        )

    def _chunk_ids(self, sources: list[RetrievedSource]) -> list[str]:
        return [source.chunk_id for source in sources[:4] if source.chunk_id]
