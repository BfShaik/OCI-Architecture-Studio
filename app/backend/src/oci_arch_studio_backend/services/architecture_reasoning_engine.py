from __future__ import annotations

from dataclasses import dataclass

from oci_arch_studio_backend.models.architecture import RetrievedSource
from oci_arch_studio_backend.services.architecture_heuristics import ArchitectureHeuristicClassifier
from oci_arch_studio_backend.services.intents import IntentProfile


@dataclass(frozen=True)
class ReasoningProfile:
    name: str
    triggers: tuple[str, ...]
    intents: tuple[str, ...]
    retrieval_terms: tuple[str, ...]
    service_priorities: tuple[str, ...]
    architecture_patterns: tuple[str, ...]
    workload_types: tuple[str, ...]
    risk_emphasis: tuple[str, ...]
    tradeoff_dimensions: tuple[str, ...]
    recommendation_guidance: tuple[str, ...]


@dataclass(frozen=True)
class ArchitectureTradeoff:
    dimension: str
    decision: str
    benefit: str
    cost_or_risk: str
    guidance: str
    source_chunk_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class RecommendationConfidence:
    recommendation: str
    score: float
    level: str
    reasoning_basis: str
    source_chunk_ids: tuple[str, ...] = ()
    known_limitations: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReasoningResult:
    profile: ReasoningProfile
    heuristics_triggered: tuple[str, ...]
    pattern_hints: tuple[str, ...]
    retrieval_terms: tuple[str, ...]
    service_priorities: tuple[str, ...]
    risk_emphasis: tuple[str, ...]
    tradeoffs: tuple[ArchitectureTradeoff, ...]
    recommendation_confidence: tuple[RecommendationConfidence, ...]


REASONING_PROFILES: tuple[ReasoningProfile, ...] = (
    ReasoningProfile(
        name="ha_dr_architecture",
        triggers=("ha", "high availability", "dr", "disaster recovery", "rto", "rpo", "failover", "multi-region"),
        intents=("dr", "architecture", "saas_platform", "release_awareness"),
        retrieval_terms=("RTO", "RPO", "failover", "backup", "replication", "Full Stack Disaster Recovery", "Monitoring"),
        service_priorities=("Full Stack Disaster Recovery", "Database Services", "Object Storage", "Load Balancer", "DNS", "Monitoring", "Logging"),
        architecture_patterns=("multi-region-ha", "active-passive-dr", "backup-recovery", "failover-runbook"),
        workload_types=("enterprise-app", "regulated-workload", "saas-platform"),
        risk_emphasis=("RTO/RPO validation", "replication lag", "failover testing", "return-to-primary runbooks"),
        tradeoff_dimensions=("cost_vs_resilience", "latency_vs_multi_region_resilience", "simplicity_vs_scalability"),
        recommendation_guidance=(
            "Tie every HA/DR recommendation to explicit RTO/RPO, failover authority, data protection, and observability.",
        ),
    ),
    ReasoningProfile(
        name="migration_architecture",
        triggers=(
            "migration",
            "migrate",
            "aws",
            "eks",
            "rds",
            "s3",
            "cloudfront",
            "route53",
            "modernize",
            "vmware",
            "monolith",
            "hybrid",
            "coexistence",
            "rollback",
        ),
        intents=("migration", "modernization"),
        retrieval_terms=(
            "migration waves",
            "compatibility",
            "cutover",
            "rollback",
            "coexistence",
            "Compute",
            "Cost Management",
            "Logging",
            "Monitoring",
            "Database Migration",
            "OKE",
        ),
        service_priorities=(
            "OCI Kubernetes Engine",
            "Database Migration",
            "Database Services",
            "Autonomous Database",
            "Compute",
            "Object Storage",
            "Cost Management",
            "Load Balancer",
            "Logging",
            "Monitoring",
        ),
        architecture_patterns=("kubernetes-modernization", "migration-waves", "cutover", "rollback"),
        workload_types=("migration", "enterprise-app", "saas-platform"),
        risk_emphasis=("compatibility gaps", "cutover risk", "rollback readiness", "data migration validation"),
        tradeoff_dimensions=("managed_vs_self_managed", "simplicity_vs_scalability", "flexibility_vs_operational_overhead"),
        recommendation_guidance=(
            "Prefer phased migration waves with explicit compatibility checks and rollback gates over one-for-one service replacement.",
        ),
    ),
    ReasoningProfile(
        name="saas_platform",
        triggers=(
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
            "shared service",
            "multi-region",
        ),
        intents=("saas_platform", "architecture", "dr"),
        retrieval_terms=(
            "ISV hosting",
            "tenant isolation",
            "compartment strategy",
            "network topology",
            "VCN",
            "network security groups",
            "cost allocation",
            "shared services",
            "data residency",
            "multi-region",
            "observability",
        ),
        service_priorities=(
            "Identity and Access Management",
            "Virtual Cloud Network",
            "Network Security Groups",
            "Web Application Firewall",
            "API Gateway",
            "Load Balancer",
            "OCI Kubernetes Engine",
            "Database Services",
            "Autonomous Database",
            "Object Storage",
            "Vault",
            "Cloud Guard",
            "Logging",
            "Monitoring",
            "Cost Management",
        ),
        architecture_patterns=("tenant-isolation", "compartment-strategy", "landing-zone", "network-isolation", "public-ingress", "multi-region-ha", "cost-allocation"),
        workload_types=("saas-platform", "webapp", "enterprise-app"),
        risk_emphasis=("tenant isolation", "compartment blast radius", "network exposure", "noisy-neighbor risk", "data residency", "shared-service blast radius"),
        tradeoff_dimensions=("simplicity_vs_scalability", "latency_vs_multi_region_resilience", "cost_vs_resilience"),
        recommendation_guidance=(
            "Make tenancy isolation, compartment topology, network topology, shared-service boundaries, cost attribution, and region strategy explicit.",
        ),
    ),
    ReasoningProfile(
        name="fintech_workload",
        triggers=("fintech", "payment", "pci", "regulated", "audit", "compliance", "banking"),
        intents=("dr", "security", "architecture", "release_awareness"),
        retrieval_terms=("audit", "encryption", "Vault", "IAM", "Data Safe", "RTO", "RPO", "disaster recovery"),
        service_priorities=("Vault", "Identity and Access Management", "Cloud Guard", "Data Safe", "Full Stack Disaster Recovery", "Database Services", "Logging", "Monitoring"),
        architecture_patterns=("secure-enterprise-landing-zone", "active-passive-dr", "auditability", "key-management"),
        workload_types=("regulated-workload", "enterprise-app"),
        risk_emphasis=("compliance evidence", "key availability", "audit retention", "DR test evidence"),
        tradeoff_dimensions=("cost_vs_resilience", "performance_vs_complexity", "flexibility_vs_operational_overhead"),
        recommendation_guidance=(
            "Bias recommendations toward security boundaries, audited operations, encryption, and tested DR over generic topology advice.",
        ),
    ),
    ReasoningProfile(
        name="ai_ml_inference_platform",
        triggers=("ai", "ai/ml", "inference", "model", "gpu", "sagemaker"),
        intents=("ai_ml", "architecture", "cost"),
        retrieval_terms=("GPU", "model artifacts", "inference latency", "autoscaling", "model rollout", "Object Storage"),
        service_priorities=("Compute", "OCI Kubernetes Engine", "Object Storage", "Load Balancer", "Vault", "Logging", "Monitoring", "Cost Management"),
        architecture_patterns=("ai-inference-architecture", "autoscaling", "private-inference-api", "model-artifact-lifecycle"),
        workload_types=("ai-inference", "enterprise-app"),
        risk_emphasis=("GPU cost", "latency SLOs", "model artifact access", "rollout safety"),
        tradeoff_dimensions=("performance_vs_complexity", "cost_vs_resilience", "managed_vs_self_managed"),
        recommendation_guidance=(
            "Treat GPU placement and inference shape choices as measured capacity decisions tied to latency, concurrency, and utilization.",
        ),
    ),
    ReasoningProfile(
        name="analytics_data_platform",
        triggers=("analytics", "data lake", "pipeline", "warehouse", "streaming", "glue", "redshift"),
        intents=("analytics", "architecture", "cost", "dr"),
        retrieval_terms=("data lake", "pipeline scaling", "storage throughput", "data lifecycle", "query performance", "governance"),
        service_priorities=("Object Storage", "Data Integration", "GoldenGate", "Streaming", "Autonomous Database", "Logging", "Monitoring", "Cost Management"),
        architecture_patterns=("analytics-pipeline", "data-lake", "lifecycle-management", "pipeline-observability"),
        workload_types=("analytics", "enterprise-app"),
        risk_emphasis=("storage growth", "pipeline replay", "query sprawl", "data governance"),
        tradeoff_dimensions=("performance_vs_complexity", "cost_vs_resilience", "simplicity_vs_scalability"),
        recommendation_guidance=(
            "Separate raw, curated, and serving zones, and tie pipeline choices to throughput, replay, freshness, and governance.",
        ),
    ),
    ReasoningProfile(
        name="observability_platform",
        triggers=("observability", "logging", "monitoring", "metrics", "alarms", "dashboard", "runbook"),
        intents=("observability", "security", "architecture"),
        retrieval_terms=("centralized logging", "metrics", "alarms", "audit", "runbooks", "service connector"),
        service_priorities=("Logging", "Monitoring", "Audit", "Service Connector Hub", "Cloud Guard", "Events", "Notifications"),
        architecture_patterns=("observability-platform", "slo-monitoring", "auditability", "incident-runbooks"),
        workload_types=("enterprise-app", "regulated-workload", "saas-platform"),
        risk_emphasis=("missing telemetry", "alert fatigue", "retention gaps", "incident ownership"),
        tradeoff_dimensions=("simplicity_vs_scalability", "cost_vs_resilience", "flexibility_vs_operational_overhead"),
        recommendation_guidance=(
            "Separate logs, metrics, audit trails, alarm routing, retention, and runbook ownership.",
        ),
    ),
    ReasoningProfile(
        name="cost_optimized_workload",
        triggers=("cost", "budget", "optimize", "rightsizing", "savings", "dev/test", "cheap"),
        intents=("cost", "architecture"),
        retrieval_terms=("Cost Management", "budgets", "rightsizing", "lifecycle", "autoscaling", "reserved capacity"),
        service_priorities=("Cost Management", "Compute", "Object Storage", "Monitoring", "Autonomous Database", "Load Balancer"),
        architecture_patterns=("cost-optimized", "rightsizing", "lifecycle-management", "autoscaling"),
        workload_types=("cost-optimized-webapp", "webapp", "enterprise-app"),
        risk_emphasis=("underprovisioning", "lost resilience", "unmeasured utilization", "storage lifecycle mistakes"),
        tradeoff_dimensions=("cost_vs_resilience", "performance_vs_complexity", "simplicity_vs_scalability"),
        recommendation_guidance=(
            "Optimize cost through measured utilization, lifecycle controls, and autoscaling without removing resilience or security guardrails.",
        ),
    ),
)

DEFAULT_REASONING_PROFILE = REASONING_PROFILES[0]


class ArchitectureReasoningEngine:
    """Deterministic architecture reasoning profiles and explainability signals."""

    def select_profile(
        self,
        *,
        question: str,
        workload_context: str | None,
        profile: IntentProfile,
        sources: list[RetrievedSource] | None = None,
    ) -> ReasoningProfile:
        haystack = self._haystack(question, workload_context, profile, sources or ())
        heuristic_domains = set(
            ArchitectureHeuristicClassifier().detect(
                " ".join(part for part in (question, workload_context) if part)
            ).domains
        )
        scored: list[tuple[int, ReasoningProfile]] = []
        for candidate in REASONING_PROFILES:
            score = 0
            score += 3 if profile.intent.value in candidate.intents else 0
            score += sum(2 for trigger in candidate.triggers if trigger in haystack)
            score += sum(1 for pattern in candidate.architecture_patterns if pattern in haystack)
            score += sum(1 for service in candidate.service_priorities if service.lower() in haystack)
            score += self._domain_specificity_bonus(candidate, heuristic_domains)
            scored.append((score, candidate))
        scored.sort(key=lambda item: item[0], reverse=True)
        return scored[0][1] if scored and scored[0][0] > 0 else DEFAULT_REASONING_PROFILE

    def pre_retrieval_terms(
        self,
        *,
        question: str,
        workload_context: str | None,
        profile: IntentProfile,
    ) -> tuple[str, ...]:
        selected = self.select_profile(question=question, workload_context=workload_context, profile=profile)
        return tuple(dict.fromkeys((*selected.retrieval_terms, *selected.architecture_patterns, *selected.workload_types)))

    def analyze(
        self,
        *,
        question: str,
        workload_context: str | None,
        profile: IntentProfile,
        sources: list[RetrievedSource],
        recommendations: list[str],
        synthesis_provider: str,
    ) -> ReasoningResult:
        selected = self.select_profile(
            question=question,
            workload_context=workload_context,
            profile=profile,
            sources=sources,
        )
        heuristics = ArchitectureHeuristicClassifier().detect(
            " ".join(part for part in (question, workload_context) if part)
        )
        tradeoffs = tuple(
            self._tradeoff_for_dimension(dimension, selected, sources)
            for dimension in selected.tradeoff_dimensions
        )
        recommendation_confidence = tuple(
            self._recommendation_confidence(
                recommendation=recommendation,
                profile=selected,
                sources=sources,
                synthesis_provider=synthesis_provider,
            )
            for recommendation in recommendations[:6]
        )
        return ReasoningResult(
            profile=selected,
            heuristics_triggered=heuristics.domains,
            pattern_hints=selected.architecture_patterns,
            retrieval_terms=selected.retrieval_terms,
            service_priorities=selected.service_priorities,
            risk_emphasis=selected.risk_emphasis,
            tradeoffs=tradeoffs,
            recommendation_confidence=recommendation_confidence,
        )

    def _tradeoff_for_dimension(
        self,
        dimension: str,
        profile: ReasoningProfile,
        sources: list[RetrievedSource],
    ) -> ArchitectureTradeoff:
        source_ids = tuple(source.chunk_id for source in sources[:3] if source.chunk_id)
        details = {
            "cost_vs_resilience": ArchitectureTradeoff(
                dimension=dimension,
                decision="Increase redundancy only where RTO/RPO or business criticality justify it.",
                benefit="Improves availability and recovery confidence for critical paths.",
                cost_or_risk="Adds cross-region, replication, testing, and steady-state capacity cost.",
                guidance="Use tiered resilience: critical services get stronger DR, lower-tier services can use backup/restore or pilot-light patterns.",
                source_chunk_ids=source_ids,
            ),
            "performance_vs_complexity": ArchitectureTradeoff(
                dimension=dimension,
                decision="Choose performance-focused services or shapes only after measuring latency, throughput, and saturation targets.",
                benefit="Improves user latency, batch throughput, or inference capacity when sized correctly.",
                cost_or_risk="Adds operational complexity, tuning requirements, and overprovisioning risk.",
                guidance="Prototype the bottleneck path, set SLOs, and scale the narrowest service first.",
                source_chunk_ids=source_ids,
            ),
            "managed_vs_self_managed": ArchitectureTradeoff(
                dimension=dimension,
                decision="Prefer managed OCI services when they satisfy compatibility and control requirements.",
                benefit="Reduces patching, backup, scaling, and operational burden.",
                cost_or_risk="Can constrain low-level tuning, portability, or exact source-platform behavior.",
                guidance="Use self-managed only for validated compatibility gaps or control requirements.",
                source_chunk_ids=source_ids,
            ),
            "latency_vs_multi_region_resilience": ArchitectureTradeoff(
                dimension=dimension,
                decision="Use multi-region design only with explicit traffic, consistency, and failover requirements.",
                benefit="Improves regional survivability and business continuity.",
                cost_or_risk="Can increase latency, data consistency complexity, and runbook burden.",
                guidance="Document data placement, DNS/traffic failover, RTO/RPO, and return-to-primary before selecting active-active.",
                source_chunk_ids=source_ids,
            ),
            "simplicity_vs_scalability": ArchitectureTradeoff(
                dimension=dimension,
                decision="Start with the simplest pattern that meets near-term scale and leaves clear expansion points.",
                benefit="Reduces delivery risk and shortens validation cycles.",
                cost_or_risk="May need redesign if tenant, region, data, or traffic growth is underestimated.",
                guidance="Keep interfaces, network tiers, and data boundaries explicit so scale-out paths remain available.",
                source_chunk_ids=source_ids,
            ),
            "flexibility_vs_operational_overhead": ArchitectureTradeoff(
                dimension=dimension,
                decision="Add platform flexibility only where the workload team can operate it.",
                benefit="Supports custom deployment, scaling, or migration constraints.",
                cost_or_risk="Increases monitoring, patching, incident, and governance overhead.",
                guidance="Prefer opinionated managed paths unless a clear workload requirement demands flexibility.",
                source_chunk_ids=source_ids,
            ),
        }
        return details.get(
            dimension,
            ArchitectureTradeoff(
                dimension=dimension,
                decision=f"Apply the {profile.name} profile to this decision.",
                benefit="Keeps recommendation structure aligned to the detected workload.",
                cost_or_risk="Profile fit is heuristic and should be validated with workload requirements.",
                guidance="Confirm assumptions before implementation.",
                source_chunk_ids=source_ids,
            ),
        )

    def _recommendation_confidence(
        self,
        *,
        recommendation: str,
        profile: ReasoningProfile,
        sources: list[RetrievedSource],
        synthesis_provider: str,
    ) -> RecommendationConfidence:
        text = recommendation.lower()
        matched_sources = [
            source
            for source in sources
            if (source.service and source.service.lower() in text)
            or any(pattern.lower() in text for pattern in source.architecture_patterns)
            or any(workload.lower() in text for workload in source.workload_types)
        ]
        service_match = any(service.lower() in text for service in profile.service_priorities)
        freshness_penalty = 0.12 if any(source.is_stale for source in matched_sources) else 0.0
        provider_bonus = 0.04 if synthesis_provider == "oci_genai" else 0.0
        score = 0.48 + (0.22 if matched_sources else 0.0) + (0.16 if service_match else 0.0) + provider_bonus - freshness_penalty
        score = round(min(max(score, 0.0), 0.95), 3)
        limitations = []
        if not matched_sources:
            limitations.append("No direct retrieved chunk matched this recommendation text.")
        if any(source.is_stale for source in matched_sources):
            limitations.append("One or more supporting chunks may be stale.")
        assumptions = (
            "Workload SLOs, data sensitivity, scale, and RTO/RPO are not fully known.",
            "Profile selection is deterministic and should be reviewed by an architect.",
        )
        basis = (
            f"Profile {profile.name}; matched {len(matched_sources)} supporting chunk(s); "
            f"synthesis provider {synthesis_provider}."
        )
        return RecommendationConfidence(
            recommendation=recommendation,
            score=score,
            level=self._level(score),
            reasoning_basis=basis,
            source_chunk_ids=tuple(source.chunk_id for source in matched_sources[:3] if source.chunk_id),
            known_limitations=tuple(limitations),
            assumptions=assumptions,
        )

    def _haystack(
        self,
        question: str,
        workload_context: str | None,
        profile: IntentProfile,
        sources: tuple[RetrievedSource, ...] | list[RetrievedSource],
    ) -> str:
        return " ".join(
            (
                question,
                workload_context or "",
                profile.intent.value,
                " ".join(source.service or "" for source in sources),
                " ".join(source.service_domain or "" for source in sources),
                " ".join(" ".join(source.workload_types) for source in sources),
                " ".join(" ".join(source.domain_tags) for source in sources),
                " ".join(" ".join(source.architecture_patterns) for source in sources),
            )
        ).lower()

    def _level(self, score: float) -> str:
        if score >= 0.78:
            return "high"
        if score >= 0.58:
            return "medium"
        return "low"

    def _domain_specificity_bonus(self, profile: ReasoningProfile, domains: set[str]) -> int:
        domain_to_profile = {
            "fintech": "fintech_workload",
            "SaaS": "saas_platform",
            "AI/ML": "ai_ml_inference_platform",
            "observability": "observability_platform",
            "analytics": "analytics_data_platform",
            "ecommerce": "cost_optimized_workload",
        }
        return 6 if any(domain_to_profile.get(domain) == profile.name for domain in domains) else 0
