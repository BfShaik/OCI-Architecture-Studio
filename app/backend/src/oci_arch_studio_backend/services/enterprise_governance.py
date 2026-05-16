from __future__ import annotations

from typing import Iterable

from oci_arch_studio_backend.models.architecture import (
    ArchitectureComparison,
    ArchitectureConsistencyFinding,
    ArchitectureDecisionReason,
    ArchitectureRiskClassification,
    AuditabilityTrace,
    ConfidenceScore,
    EnterpriseGovernanceAssessment,
    EnterpriseReviewFinding,
    ExecutiveAdvisorySummary,
    GovernanceAnnotation,
    KnowledgeTemporalContext,
    RecommendationPriority,
    ReleaseImpactSummary,
    RetrievedSource,
)
from oci_arch_studio_backend.services.architecture_reasoning_engine import ReasoningResult
from oci_arch_studio_backend.services.intents import IntentProfile


SECURITY_CONTROL_TERMS: dict[str, tuple[str, ...]] = {
    "iam": ("iam", "identity and access management", "least privilege", "dynamic group", "policy"),
    "vault": ("vault", "key", "secret", "encryption", "kms"),
    "network_segmentation": ("vcn", "subnet", "network security group", "nsg", "private endpoint", "segmentation"),
    "audit_logging": ("audit", "logging", "monitoring", "alarm", "notifications", "service connector"),
    "security_zones": ("security zone", "cloud guard", "data safe", "waf"),
}

REVIEW_CHECKS: tuple[tuple[str, str, tuple[str, ...], str, str], ...] = (
    (
        "single_point_of_failure",
        "resilience",
        ("multi-ad", "multi availability domain", "failover", "load balancer", "replication", "backup"),
        "Potential single point of failure if tiers, data stores, or ingress are not deployed across fault/availability boundaries.",
        "Validate multi-AD placement, health checks, backup/restore, and failover runbooks before production.",
    ),
    (
        "weak_dr_posture",
        "ha_dr",
        ("rto", "rpo", "disaster recovery", "full stack disaster recovery", "replication", "backup"),
        "DR posture needs explicit recovery objectives, replication scope, and tested recovery procedures.",
        "Define RTO/RPO by tier, automate backups, test failover, and capture recovery evidence.",
    ),
    (
        "missing_observability",
        "operations",
        ("logging", "monitoring", "alarm", "dashboard", "runbook", "audit"),
        "Observability coverage is incomplete for enterprise operations.",
        "Add OCI Logging, Monitoring, alarms, audit retention, and incident runbook ownership.",
    ),
    (
        "iam_weakness",
        "security",
        ("iam", "least privilege", "policy", "dynamic group", "compartment"),
        "IAM boundaries need explicit least-privilege policy and compartment design.",
        "Use compartment-scoped OCI IAM policies, dynamic groups, and periodic access review.",
    ),
    (
        "cost_governance_gap",
        "finops",
        ("cost", "budget", "rightsizing", "autoscaling", "lifecycle", "utilization"),
        "Cost controls are not explicit enough for enterprise FinOps review.",
        "Add budgets, utilization reviews, storage lifecycle policy, and capacity guardrails.",
    ),
)


class EnterpriseGovernanceAdvisor:
    """Deterministic governance and advisory metadata for enterprise review.

    The advisor intentionally stays heuristic and explainable. It does not enforce policy
    or orchestrate external governance systems; it annotates the generated advisory with
    review signals that architects and operators can inspect.
    """

    def assess(
        self,
        *,
        question: str,
        workload_context: str | None,
        profile: IntentProfile,
        sources: list[RetrievedSource],
        recommendations: list[str],
        decision_reasoning: list[ArchitectureDecisionReason],
        reasoning_result: ReasoningResult,
        consistency_findings: list[ArchitectureConsistencyFinding],
        release_context: ReleaseImpactSummary | None,
        temporal_context: KnowledgeTemporalContext | None,
        confidence: ConfidenceScore | None,
        synthesis_provider: str,
        synthesis_fallback_used: bool,
        quality_warnings: list[str],
        unsupported_claims: list[str],
    ) -> EnterpriseGovernanceAssessment:
        text = self._text(question, workload_context, recommendations, sources)
        source_ids = self._source_ids(sources)
        domain_signals = self._domain_signals(text, profile, sources)
        governance_annotations = self._governance_annotations(
            recommendations=recommendations,
            decision_reasoning=decision_reasoning,
            domains=domain_signals,
            source_ids=source_ids,
        )
        security_checks = self._security_posture_checks(text, recommendations, source_ids)
        review_findings = self._enterprise_review_findings(
            text=text,
            profile=profile,
            consistency_findings=consistency_findings,
            source_ids=source_ids,
        )
        risks = self._risk_classifications(
            profile=profile,
            domains=domain_signals,
            confidence=confidence,
            review_findings=review_findings,
            quality_warnings=quality_warnings,
            unsupported_claims=unsupported_claims,
            source_ids=source_ids,
        )
        priorities = self._priorities(recommendations, risks)
        comparisons = self._comparisons(text, profile, sources, recommendations, source_ids)
        audit_trace = AuditabilityTrace(
            retrieval_source_chunk_ids=source_ids,
            reasoning_profile=reasoning_result.profile.name,
            heuristics_applied=list(reasoning_result.heuristics_triggered),
            release_influence=self._release_influence(release_context, temporal_context),
            synthesis_provider=synthesis_provider,
            fallback_events=(["synthesis_fallback"] if synthesis_fallback_used else []),
            confidence_level=confidence.level if confidence else None,
            evaluation_signals={
                "quality_warning_count": len(quality_warnings),
                "unsupported_claim_count": len(unsupported_claims),
                "consistency_finding_count": len(consistency_findings),
                "risk_count": len(risks),
                "evidence_chunk_count": len(source_ids),
            },
        )
        return EnterpriseGovernanceAssessment(
            maturity_level=self._maturity_level(confidence, risks, review_findings),
            executive_summary=self._executive_summary(
                profile=profile,
                domains=domain_signals,
                risks=risks,
                priorities=priorities,
                confidence=confidence,
            ),
            governance_annotations=governance_annotations,
            security_posture_checks=security_checks,
            risk_classifications=risks,
            recommendation_priorities=priorities,
            architecture_comparisons=comparisons,
            enterprise_review_findings=review_findings,
            auditability_trace=audit_trace,
            notes=self._notes(confidence, synthesis_provider, temporal_context),
        )

    def _governance_annotations(
        self,
        *,
        recommendations: list[str],
        decision_reasoning: list[ArchitectureDecisionReason],
        domains: set[str],
        source_ids: list[str],
    ) -> list[GovernanceAnnotation]:
        annotations: list[GovernanceAnnotation] = []
        reason_sources = {
            index: list(reason.source_chunk_ids)
            for index, reason in enumerate(decision_reasoning)
        }
        for index, recommendation in enumerate(recommendations[:8]):
            text = recommendation.lower()
            control_area = "architecture_governance"
            policy_signal = "production_control"
            guidance = "Document design ownership, validation evidence, rollout gates, and operational acceptance before production."
            confidence = 0.62
            if any(term in text for term in ("iam", "vault", "encrypt", "security", "audit", "private")):
                control_area = "security"
                policy_signal = "least_privilege_and_data_protection"
                guidance = "Validate OCI IAM policy scope, Vault/key ownership, encryption requirements, and audit retention."
                confidence = 0.78
            elif any(term in text for term in ("rto", "rpo", "dr", "failover", "backup", "replication")):
                control_area = "resilience"
                policy_signal = "ha_dr_evidence"
                guidance = "Tie the recommendation to RTO/RPO, failover authority, backup validation, and recovery test evidence."
                confidence = 0.76
            elif any(term in text for term in ("cost", "budget", "rightsizing", "autoscaling", "lifecycle")):
                control_area = "finops"
                policy_signal = "cost_accountability"
                guidance = "Track utilization, budgets, storage lifecycle, and scaling limits as explicit FinOps controls."
                confidence = 0.72
            elif any(term in text for term in ("logging", "monitoring", "alarm", "runbook", "observability")):
                control_area = "operations"
                policy_signal = "supportability"
                guidance = "Confirm telemetry, alarm routing, retention, incident ownership, and runbook coverage."
                confidence = 0.74
            elif any(term in text for term in ("migration", "cutover", "rollback", "wave", "coexist")):
                control_area = "migration_governance"
                policy_signal = "change_control"
                guidance = "Use migration waves with readiness gates, cutover rehearsals, rollback criteria, and coexistence controls."
                confidence = 0.75

            if "fintech" in domains or "regulated" in domains:
                guidance += " Regulated workload evidence should be retained for audit review."
                confidence = min(confidence + 0.05, 0.92)
            annotations.append(
                GovernanceAnnotation(
                    recommendation_index=index,
                    control_area=control_area,
                    policy_signal=policy_signal,
                    guidance=guidance,
                    confidence=round(confidence, 3),
                    source_chunk_ids=reason_sources.get(index) or source_ids[:3],
                )
            )
        return annotations

    def _security_posture_checks(
        self,
        text: str,
        recommendations: list[str],
        source_ids: list[str],
    ) -> list[GovernanceAnnotation]:
        combined = f"{text} {' '.join(recommendations)}".lower()
        checks: list[GovernanceAnnotation] = []
        for area, terms in SECURITY_CONTROL_TERMS.items():
            present = any(term in combined for term in terms)
            checks.append(
                GovernanceAnnotation(
                    control_area=area,
                    policy_signal="covered" if present else "needs_review",
                    guidance=(
                        self._security_guidance(area)
                        if present
                        else f"Add explicit {area.replace('_', ' ')} guidance before enterprise approval."
                    ),
                    confidence=0.82 if present else 0.48,
                    source_chunk_ids=source_ids[:3] if present else [],
                )
            )
        return checks

    def _risk_classifications(
        self,
        *,
        profile: IntentProfile,
        domains: set[str],
        confidence: ConfidenceScore | None,
        review_findings: list[EnterpriseReviewFinding],
        quality_warnings: list[str],
        unsupported_claims: list[str],
        source_ids: list[str],
    ) -> list[ArchitectureRiskClassification]:
        risks: list[ArchitectureRiskClassification] = []
        if "fintech" in domains or "regulated" in domains:
            risks.append(
                self._risk(
                    "security-regulatory-review",
                    "elevated security risk",
                    "security",
                    "Regulated workload signals require stronger IAM, encryption, audit, and data-protection evidence.",
                    ["security", "data", "operations"],
                    "Security sign-off may block rollout if audit, key-management, and access boundaries are not explicit.",
                    "Use OCI IAM least privilege, Vault-managed keys/secrets, Logging/Audit retention, and documented evidence gates.",
                    source_ids,
                )
            )
        if profile.intent.value in {"migration", "modernization"}:
            risks.append(
                self._risk(
                    "migration-cutover-risk",
                    "elevated migration risk",
                    "migration",
                    "Migration guidance needs compatibility validation, sequencing, cutover rehearsal, and rollback criteria.",
                    ["migration", "application", "data"],
                    "Cutover defects can extend coexistence windows or force rollback.",
                    "Use phased waves, data validation, blue/green or parallel run where feasible, and explicit rollback checkpoints.",
                    source_ids,
                )
            )
        if profile.intent.value in {"dr", "saas_platform"} or "ha_dr" in {finding.impacted_area for finding in review_findings}:
            risks.append(
                self._risk(
                    "resilience-validation-risk",
                    "elevated operational risk",
                    "ha_dr",
                    "Availability and DR claims require tested recovery procedures and observable failover behavior.",
                    ["availability", "data", "operations"],
                    "Untested failover can create longer outages than the stated RTO/RPO.",
                    "Run DR tests, capture evidence, monitor replication health, and maintain return-to-primary runbooks.",
                    source_ids,
                )
            )
        if any(finding.impacted_area == "finops" for finding in review_findings):
            risks.append(
                self._risk(
                    "cost-control-risk",
                    "elevated cost risk",
                    "finops",
                    "Cost-control guidance is incomplete for scale, storage growth, or managed-service usage.",
                    ["cost", "capacity", "operations"],
                    "Spend may grow faster than forecast if utilization, lifecycle, and scaling controls are not measured.",
                    "Add budgets, cost analysis review, right-sizing cadence, and storage lifecycle rules.",
                    source_ids,
                )
            )
        if unsupported_claims or (confidence and confidence.level == "low"):
            risks.append(
                self._risk(
                    "evidence-confidence-risk",
                    "moderate risk",
                    "advisory_confidence",
                    "One or more recommendations have limited evidence, unsupported requested claims, or low confidence.",
                    ["governance", "architecture_review"],
                    "Architecture review should treat these items as provisional until validated against OCI sources and workload requirements.",
                    "Gather missing requirements, refresh sources if needed, and require citation-backed approval for affected recommendations.",
                    source_ids,
                )
            )
        if not risks and quality_warnings:
            risks.append(
                self._risk(
                    "quality-warning-risk",
                    "low risk",
                    "review_quality",
                    "Quality warnings exist but do not currently indicate an elevated risk category.",
                    ["architecture_review"],
                    "Reviewers should confirm the warnings before promotion.",
                    "Resolve or acknowledge each quality warning in the implementation plan.",
                    source_ids,
                )
            )
        return risks or [
            self._risk(
                "baseline-governance-risk",
                "low risk",
                "governance",
                "No elevated deterministic governance risk was detected from the available prompt, evidence, and recommendations.",
                ["architecture_review"],
                "Residual risk remains because this is heuristic advisory metadata.",
                "Have the responsible architect validate requirements, controls, and source freshness before implementation.",
                source_ids,
            )
        ]

    def _priorities(
        self,
        recommendations: list[str],
        risks: list[ArchitectureRiskClassification],
    ) -> list[RecommendationPriority]:
        elevated_categories = {risk.category for risk in risks if risk.level.startswith("elevated")}
        priorities: list[RecommendationPriority] = []
        for index, recommendation in enumerate(recommendations[:8]):
            text = recommendation.lower()
            priority = "recommended later"
            phase = "phase_2_hardening"
            rationale = "Useful after the critical production guardrails and migration readiness work are stable."
            if any(term in text for term in ("iam", "vault", "security", "audit", "backup", "rto", "rpo", "monitoring", "logging")):
                priority = "recommended immediately"
                phase = "phase_0_guardrails"
                rationale = "Security, observability, and resilience controls should be in place before production traffic."
            elif any(term in text for term in ("migration", "cutover", "rollback", "wave")) or "migration" in elevated_categories:
                priority = "recommended immediately"
                phase = "phase_1_migration_readiness"
                rationale = "Migration sequencing and rollback controls reduce cutover risk."
            elif any(term in text for term in ("cost", "budget", "rightsizing", "lifecycle", "autoscaling")):
                priority = "optional optimizations"
                phase = "phase_3_finops_optimization"
                rationale = "FinOps controls should be measured once baseline telemetry and traffic patterns exist."
            elif any(term in text for term in ("multi-region", "active-active", "advanced", "global")):
                priority = "advanced enterprise enhancements"
                phase = "phase_4_resilience_expansion"
                rationale = "Advanced resilience should follow validated requirements, operating model, and cost approval."
            rationale = f"R{index + 1}: {rationale}"
            priorities.append(
                RecommendationPriority(
                    recommendation_index=index,
                    priority=priority,
                    implementation_phase=phase,
                    rationale=rationale,
                )
            )
        return priorities

    def _comparisons(
        self,
        text: str,
        profile: IntentProfile,
        sources: list[RetrievedSource],
        recommendations: list[str],
        source_ids: list[str],
    ) -> list[ArchitectureComparison]:
        combined = f"{text} {' '.join(recommendations)}".lower()
        comparisons: list[ArchitectureComparison] = []
        if any(term in combined for term in ("kubernetes", "oke", "eks", "container")):
            comparisons.append(
                ArchitectureComparison(
                    decision="OKE vs Compute-based deployment",
                    preferred_option="OKE for containerized workloads with platform scaling and rollout requirements.",
                    alternatives=["Compute instances for simpler VM-oriented applications", "OCI Functions for event-driven units of work"],
                    pros=["Managed Kubernetes control plane", "Clear modernization path from EKS", "Supports autoscaling and rollout controls"],
                    cons=["Requires Kubernetes operations maturity", "Cluster governance and network policy need explicit ownership"],
                    governance_implications=["Define namespace, IAM, image registry, network policy, and patching ownership."],
                    cost_implications="OKE can reduce platform toil but needs utilization and node-pool right-sizing controls.",
                    operational_complexity="moderate",
                    source_chunk_ids=self._matched_source_ids(sources, ("oke", "kubernetes"), source_ids),
                )
            )
        if any(term in combined for term in ("database", "rds", "autonomous", "base database")):
            comparisons.append(
                ArchitectureComparison(
                    decision="Autonomous Database vs Base Database Service",
                    preferred_option="Autonomous Database when managed operations and automation fit compatibility requirements.",
                    alternatives=["Base Database Service for deeper operational control", "MySQL HeatWave for MySQL-oriented workloads"],
                    pros=["Reduced patching and tuning burden", "Managed backup and scaling features", "Strong enterprise database posture"],
                    cons=["Compatibility and operational-control requirements must be validated before migration."],
                    governance_implications=["Classify data, validate backup/restore, encryption, access policy, and audit retention."],
                    cost_implications="Autonomous can lower operations cost, while Base DB may fit workloads needing more control.",
                    operational_complexity="low_to_moderate",
                    source_chunk_ids=self._matched_source_ids(sources, ("database", "autonomous", "base database", "rds"), source_ids),
                )
            )
        if any(term in combined for term in ("function", "serverless", "kubernetes", "oke")):
            comparisons.append(
                ArchitectureComparison(
                    decision="Functions vs Kubernetes",
                    preferred_option="OCI Functions for stateless event-driven jobs; OKE for long-running services and platform workloads.",
                    alternatives=["Compute for simple persistent services"],
                    pros=["Functions reduce runtime management for scheduled or event-driven work", "OKE supports richer service networking and rollout patterns"],
                    cons=["Functions are not a fit for persistent local state; OKE has higher platform operations overhead."],
                    governance_implications=["Separate stateless job ownership from persistent service ownership and define deployment controls."],
                    cost_implications="Functions align cost to execution; OKE needs capacity management but can be more predictable at steady load.",
                    operational_complexity="context_dependent",
                    source_chunk_ids=source_ids[:3],
                )
            )
        if profile.intent.value in {"dr", "saas_platform"} or "multi-region" in combined:
            comparisons.append(
                ArchitectureComparison(
                    decision="Active/passive DR vs multi-region active/active",
                    preferred_option="Active/passive unless latency, uptime, or tenancy requirements justify active/active complexity.",
                    alternatives=["Backup/restore for lower-tier workloads", "Active/active for validated high-criticality paths"],
                    pros=["Active/passive is easier to govern and test", "Active/active can reduce regional recovery time for critical services"],
                    cons=["Active/active increases consistency, cost, routing, and operational complexity."],
                    governance_implications=["Require RTO/RPO approval, failover authority, test evidence, and return-to-primary procedures."],
                    cost_implications="Resilience cost rises with warm capacity, replication, traffic management, and DR testing.",
                    operational_complexity="moderate_to_high",
                    source_chunk_ids=self._matched_source_ids(sources, ("disaster", "recovery", "dr", "replication"), source_ids),
                )
            )
        return comparisons[:4]

    def _enterprise_review_findings(
        self,
        *,
        text: str,
        profile: IntentProfile,
        consistency_findings: list[ArchitectureConsistencyFinding],
        source_ids: list[str],
    ) -> list[EnterpriseReviewFinding]:
        normalized = text.lower()
        findings: list[EnterpriseReviewFinding] = []
        for check, area, terms, message, mitigation in REVIEW_CHECKS:
            if check == "weak_dr_posture" and profile.intent.value not in {"dr", "saas_platform", "architecture"}:
                continue
            present = any(term in normalized for term in terms)
            if present:
                continue
            severity = "warning" if area in {"resilience", "security", "operations"} else "info"
            findings.append(
                EnterpriseReviewFinding(
                    check=check,
                    severity=severity,
                    finding=message,
                    impacted_area=area,
                    mitigation=mitigation,
                    source_chunk_ids=source_ids[:3],
                )
            )
        for finding in consistency_findings:
            if finding.severity in {"warning", "error"}:
                findings.append(
                    EnterpriseReviewFinding(
                        check=f"consistency_{finding.check}",
                        severity=finding.severity,
                        finding=finding.message,
                        impacted_area="architecture_consistency",
                        mitigation=finding.recommendation,
                        source_chunk_ids=list(finding.source_chunk_ids),
                    )
                )
        return findings[:8]

    def _executive_summary(
        self,
        *,
        profile: IntentProfile,
        domains: set[str],
        risks: list[ArchitectureRiskClassification],
        priorities: list[RecommendationPriority],
        confidence: ConfidenceScore | None,
    ) -> ExecutiveAdvisorySummary:
        elevated = [risk for risk in risks if risk.level.startswith("elevated")]
        immediate_count = sum(1 for item in priorities if item.priority == "recommended immediately")
        domain_text = ", ".join(sorted(domains)) if domains else profile.intent.value
        confidence_text = confidence.level if confidence else "unknown"
        return ExecutiveAdvisorySummary(
            business_impact=(
                f"The advisory is framed for {domain_text} and should help reviewers connect OCI service choices "
                "to resilience, security, migration, and operating-model outcomes."
            ),
            governance_posture=(
                f"Governance posture is {self._posture(elevated, confidence)} with {immediate_count} immediate control "
                f"item(s) and {confidence_text} advisory confidence."
            ),
            risk_summary=(
                "Elevated risks require review before production promotion."
                if elevated
                else "No elevated deterministic governance risk was detected, but architect review is still required."
            ),
            implementation_guidance=(
                "Sequence guardrails first, then migration/readiness work, then FinOps and advanced resilience optimizations."
            ),
        )

    def _maturity_level(
        self,
        confidence: ConfidenceScore | None,
        risks: list[ArchitectureRiskClassification],
        findings: list[EnterpriseReviewFinding],
    ) -> str:
        elevated = any(risk.level.startswith("elevated") for risk in risks)
        warning_findings = any(finding.severity in {"warning", "error"} for finding in findings)
        if confidence and confidence.level == "high" and not elevated and not warning_findings:
            return "enterprise_review_ready"
        if confidence and confidence.level == "low":
            return "needs_architecture_review"
        if elevated or warning_findings:
            return "needs_governance_review"
        return "mvp_advisory_ready"

    def _notes(
        self,
        confidence: ConfidenceScore | None,
        synthesis_provider: str,
        temporal_context: KnowledgeTemporalContext | None,
    ) -> list[str]:
        notes = [
            "Governance assessment is deterministic advisory metadata, not an automated policy decision.",
            f"Synthesis provider observed by the governance layer: {synthesis_provider}.",
        ]
        if confidence and confidence.level != "high":
            notes.append("Confidence is not high; keep recommendations in architecture-review status until validated.")
        if temporal_context and temporal_context.knowledge_mode:
            notes.append(f"Knowledge temporal mode: {temporal_context.knowledge_mode}.")
        return notes

    def _risk(
        self,
        risk_id: str,
        level: str,
        category: str,
        summary: str,
        impacted_areas: list[str],
        implication: str,
        mitigation: str,
        source_ids: list[str],
    ) -> ArchitectureRiskClassification:
        return ArchitectureRiskClassification(
            risk_id=risk_id,
            level=level,
            category=category,
            summary=summary,
            impacted_areas=impacted_areas,
            operational_implication=implication,
            mitigation=mitigation,
            source_chunk_ids=source_ids[:3],
        )

    def _release_influence(
        self,
        release_context: ReleaseImpactSummary | None,
        temporal_context: KnowledgeTemporalContext | None,
    ) -> list[str]:
        influence: list[str] = []
        if release_context:
            influence.extend(release_context.architecture_affecting_services[:5])
            influence.extend(release_context.impact_categories[:5])
            if release_context.matched_release_count:
                influence.append(f"matched_release_count={release_context.matched_release_count}")
        if temporal_context and temporal_context.current_knowledge_as_of:
            influence.append(f"knowledge_as_of={temporal_context.current_knowledge_as_of}")
        return list(dict.fromkeys(influence))

    def _source_ids(self, sources: Iterable[RetrievedSource]) -> list[str]:
        return list(dict.fromkeys(source.chunk_id for source in sources if source.chunk_id))

    def _matched_source_ids(
        self,
        sources: list[RetrievedSource],
        terms: tuple[str, ...],
        fallback: list[str],
    ) -> list[str]:
        matched = [
            source.chunk_id
            for source in sources
            if source.chunk_id
            and any(
                term in " ".join((source.title, source.summary, source.service or "", source.category or "")).lower()
                for term in terms
            )
        ]
        return list(dict.fromkeys(matched))[:3] or fallback[:3]

    def _domain_signals(
        self,
        text: str,
        profile: IntentProfile,
        sources: list[RetrievedSource],
    ) -> set[str]:
        normalized = text.lower()
        domains = set()
        for domain in ("fintech", "regulated", "ecommerce", "saas", "ai/ml", "analytics", "observability"):
            if domain in normalized:
                domains.add(domain)
        if profile.intent.value == "saas_platform":
            domains.add("saas")
        for source in sources:
            domains.update(tag.lower() for tag in source.domain_tags)
            domains.update(tag.lower() for tag in source.workload_types)
        if "regulated-workload" in domains:
            domains.add("regulated")
        return domains

    def _text(
        self,
        question: str,
        workload_context: str | None,
        recommendations: list[str],
        sources: list[RetrievedSource],
    ) -> str:
        return " ".join(
            [
                question,
                workload_context or "",
                " ".join(recommendations),
                " ".join(source.title for source in sources),
                " ".join(source.summary for source in sources),
            ]
        )

    def _posture(
        self,
        elevated: list[ArchitectureRiskClassification],
        confidence: ConfidenceScore | None,
    ) -> str:
        if elevated:
            return "review_required"
        if confidence and confidence.level == "high":
            return "review_ready"
        return "provisional"

    def _security_guidance(self, area: str) -> str:
        guidance = {
            "iam": "OCI IAM boundaries are present; validate least-privilege policies, compartments, groups, and dynamic groups.",
            "vault": "Vault/encryption controls are present; validate key rotation, secret ownership, and recovery procedures.",
            "network_segmentation": "Network segmentation is present; validate private routing, NSGs, subnet boundaries, and ingress controls.",
            "audit_logging": "Logging/audit controls are present; validate retention, alarm routing, dashboards, and incident ownership.",
            "security_zones": "Security-zone or security service signals are present; validate Cloud Guard/Data Safe/WAF coverage where applicable.",
        }
        return guidance.get(area, "Validate this security control before production.")
