from __future__ import annotations

from oci_arch_studio_backend.models.architecture import (
    ArchitectureComparison,
    FinOpsRecommendation,
    MigrationPhasePlan,
    ModernizationOption,
    OptimizationPlanSummary,
    RetrievedSource,
    WorkloadOptimizationSignal,
)
from oci_arch_studio_backend.services.architecture_heuristics import ArchitectureHeuristicClassifier
from oci_arch_studio_backend.services.intents import IntentProfile


class OptimizationAdvisor:
    """Deterministic FinOps, migration, and modernization advisory enrichment."""

    def build(
        self,
        *,
        question: str,
        workload_context: str | None,
        profile: IntentProfile,
        sources: list[RetrievedSource],
        base_recommendations: list[str],
    ) -> OptimizationPlanSummary:
        text = " ".join((question, workload_context or "", " ".join(base_recommendations))).lower()
        heuristics = ArchitectureHeuristicClassifier().detect(" ".join((question, workload_context or "")))
        migration_phases = self._migration_phases(text=text, profile=profile)
        modernization_options = self._modernization_options(text=text, profile=profile)
        finops = self._finops_recommendations(text=text, sources=sources)
        workload_signals = self._workload_signals(heuristics.domains, text)
        comparisons = self._optimization_comparisons(text=text, profile=profile, sources=sources)
        additions = self._recommendation_additions(
            migration_phases=migration_phases,
            modernization_options=modernization_options,
            finops=finops,
            workload_signals=workload_signals,
            comparisons=comparisons,
        )
        return OptimizationPlanSummary(
            maturity_level=self._maturity_level(migration_phases, modernization_options, finops, workload_signals),
            migration_phases=migration_phases,
            modernization_options=modernization_options,
            finops_recommendations=finops,
            workload_optimization_signals=workload_signals,
            optimization_comparisons=comparisons,
            implementation_readiness=self._implementation_readiness(text=text, profile=profile),
            recommendation_additions=additions,
        )

    def _migration_phases(self, *, text: str, profile: IntentProfile) -> list[MigrationPhasePlan]:
        if profile.intent.value not in {"migration", "modernization"} and not any(
            term in text
            for term in (
                "migration",
                "migrate",
                "vmware",
                "eks",
                "rds",
                "monolith",
                "hybrid",
                "modernize",
            )
        ):
            return []
        workload_type = self._migration_type(text)
        return [
            MigrationPhasePlan(
                phase="1. Discovery and landing zone readiness",
                objective=f"Map {workload_type} dependencies, security controls, data flows, and OCI landing-zone prerequisites before moving workloads.",
                actions=[
                    "Inventory source dependencies, identity paths, network routes, data stores, observability, and ownership.",
                    "Define OCI compartments, VCN/subnets, IAM policies, Vault secrets, Logging, Monitoring, and cost tags.",
                    "Confirm source-to-OCI service mappings and non-functional requirements before sizing target services.",
                ],
                dependencies=["source dependency inventory", "OCI IAM and network baseline", "rollback owner"],
                rollback_considerations=["Keep source environment authoritative until validation gates pass."],
                readiness_checks=["landing-zone controls approved", "baseline telemetry enabled", "migration wave plan reviewed"],
            ),
            MigrationPhasePlan(
                phase="2. Coexistence and pilot wave",
                objective="Run a low-blast-radius pilot with coexistence, data validation, and rollback gates.",
                actions=[
                    "Move a representative service or data slice first and validate latency, security, telemetry, and support handoff.",
                    "Use parallel run, blue/green, or read-only validation where the workload supports it.",
                    "Document cutover, rollback, DNS/traffic routing, and operational acceptance criteria.",
                ],
                dependencies=["pilot workload", "connectivity path", "validation dataset"],
                rollback_considerations=["Rollback should restore traffic and data authority to the source path without data loss."],
                readiness_checks=["pilot SLO met", "rollback rehearsal passed", "operational runbook accepted"],
            ),
            MigrationPhasePlan(
                phase="3. Wave migration and modernization",
                objective="Scale migration by dependency wave while selectively adopting managed OCI services.",
                actions=[
                    "Sequence waves by dependency order, data coupling, compliance scope, and team readiness.",
                    "Adopt OKE, Autonomous Database, Object Storage, Data Integration, or Functions only where readiness and fit are validated.",
                    "Track cost, performance, incident, and governance signals before decommissioning source components.",
                ],
                dependencies=["pilot acceptance", "wave backlog", "FinOps baseline"],
                rollback_considerations=["Maintain rollback windows until downstream dependencies and monitoring are stable."],
                readiness_checks=["wave exit report complete", "cost baseline reviewed", "source decommission approved"],
            ),
        ]

    def _modernization_options(self, *, text: str, profile: IntentProfile) -> list[ModernizationOption]:
        if profile.intent.value not in {"migration", "modernization", "architecture", "analytics", "ai_ml", "cost"} and not any(
            term in text for term in ("modernize", "monolith", "serverless", "event-driven", "replatform", "refactor")
        ):
            return []
        options = [
            ModernizationOption(
                approach="Lift-and-shift first",
                fit="Use when speed, compatibility, or risk containment matters more than immediate platform optimization.",
                tradeoffs=["fastest path", "least application change", "may preserve inefficient operating model"],
                operational_implications=["requires VM/OS patching ownership", "needs post-migration rightsizing"],
                readiness_requirements=["source dependency map", "target compute sizing", "rollback runbook"],
            ),
            ModernizationOption(
                approach="Replatform to managed OCI services",
                fit="Use when managed database, OKE, Object Storage, Logging, Monitoring, or Data Integration can reduce operational burden.",
                tradeoffs=["reduces toil", "requires compatibility testing", "can change operational controls"],
                operational_implications=["moves patching/scaling responsibility toward OCI-managed services", "requires new IAM and runbook model"],
                readiness_requirements=["compatibility validation", "data migration test", "team support model"],
            ),
            ModernizationOption(
                approach="Refactor selectively",
                fit="Use for bounded components where serverless, event-driven, or data-platform redesign creates measurable business value.",
                tradeoffs=["largest long-term optimization", "highest delivery complexity", "requires product and team readiness"],
                operational_implications=["changes deployment, telemetry, incident, and ownership boundaries"],
                readiness_requirements=["domain boundaries", "SLOs", "delivery capacity", "rollback or coexistence strategy"],
            ),
        ]
        if "analytics" in text or profile.intent.value == "analytics":
            options.append(
                ModernizationOption(
                    approach="Data-platform modernization",
                    fit="Use Object Storage zones plus managed ingestion/query services when pipeline scale, lifecycle, and governance are the bottleneck.",
                    tradeoffs=["improves storage economics", "requires data governance", "needs replay/freshness controls"],
                    operational_implications=["adds pipeline ownership, data quality checks, and access governance"],
                    readiness_requirements=["data classification", "throughput baseline", "pipeline replay test"],
                )
            )
        return options

    def _finops_recommendations(self, *, text: str, sources: list[RetrievedSource]) -> list[FinOpsRecommendation]:
        source_ids = self._source_ids(sources, ("cost", "compute", "object storage", "monitoring", "autonomous"))
        should_include = any(
            term in text
            for term in (
                "cost",
                "budget",
                "optimize",
                "rightsizing",
                "autoscaling",
                "gpu",
                "inference",
                "storage",
                "dr",
                "multi-region",
                "dev/test",
            )
        )
        if not should_include:
            return []
        recommendations = [
            FinOpsRecommendation(
                lever="Rightsizing and utilization",
                recommendation="Use OCI Monitoring and Cost Analysis/Budgets review cycles to right-size Compute, OKE node pools, and database capacity after baseline telemetry exists.",
                expected_cost_implication="Reduces over-provisioned steady-state spend while preserving headroom for measured peaks.",
                performance_tradeoff="Aggressive downsizing can create latency or saturation risk without SLO and utilization evidence.",
                operational_savings="Improves review cadence by tying capacity decisions to metrics instead of static estimates.",
                source_chunk_ids=source_ids,
            ),
            FinOpsRecommendation(
                lever="Autoscaling and environment sizing",
                recommendation="Use autoscaling for variable traffic and explicitly separate production, staging, and dev/test sizing policies.",
                expected_cost_implication="Limits idle capacity in non-production and absorbs demand spikes without permanent overbuild.",
                performance_tradeoff="Autoscaling needs warm-up, alarm, and quota validation to avoid slow scale-out under burst.",
                operational_savings="Reduces manual capacity changes and makes scaling behavior reviewable.",
                source_chunk_ids=source_ids,
            ),
            FinOpsRecommendation(
                lever="Storage and data lifecycle",
                recommendation="Use Object Storage lifecycle/tiering and data-retention policies for logs, artifacts, backups, analytics zones, and model artifacts.",
                expected_cost_implication="Controls long-term storage growth and separates hot, retained, and archival data costs.",
                performance_tradeoff="Lifecycle movement can affect restore/query latency if retention classes are chosen too aggressively.",
                operational_savings="Makes retention and recovery expectations explicit for platform and compliance teams.",
                source_chunk_ids=source_ids,
            ),
        ]
        if "gpu" in text or "inference" in text or "ai" in text:
            recommendations.append(
                FinOpsRecommendation(
                    lever="GPU and inference cost control",
                    recommendation="Treat GPU or high-performance shapes as measured inference capacity with concurrency, latency, batching, and utilization thresholds.",
                    expected_cost_implication="Avoids persistent premium capacity when CPU, smaller GPU shapes, batching, or autoscaling can meet SLOs.",
                    performance_tradeoff="Cost reductions can increase latency or reduce concurrency if not tested with production-like traffic.",
                    operational_savings="Creates a repeatable capacity model for model rollout and scale events.",
                    source_chunk_ids=source_ids,
                )
            )
        if "dr" in text or "multi-region" in text or "rto" in text or "rpo" in text:
            recommendations.append(
                FinOpsRecommendation(
                    lever="DR cost tiering",
                    recommendation="Tier DR patterns by business criticality: active/active only for justified paths, active/passive or backup/restore for lower tiers.",
                    expected_cost_implication="Prevents every component from carrying the highest cross-region steady-state cost.",
                    performance_tradeoff="Lower-cost tiers have longer recovery time or more manual recovery steps.",
                    operational_savings="Makes resilience spend explainable during architecture and budget review.",
                    source_chunk_ids=source_ids,
                )
            )
        return recommendations[:5]

    def _workload_signals(self, domains: tuple[str, ...], text: str) -> list[WorkloadOptimizationSignal]:
        selected = set(domain.lower() for domain in domains)
        if not selected:
            for domain, tokens in {
                "ecommerce": ("ecommerce", "checkout", "storefront"),
                "fintech": ("fintech", "payment", "pci", "regulated"),
                "saas": ("saas", "tenant"),
                "analytics": ("analytics", "data lake", "pipeline"),
                "ai/ml": ("ai", "inference", "gpu"),
                "observability": ("observability", "logging", "monitoring"),
            }.items():
                if any(token in text for token in tokens):
                    selected.add(domain)
        signals: list[WorkloadOptimizationSignal] = []
        mapping = {
            "ecommerce": WorkloadOptimizationSignal(
                workload="ecommerce",
                service_priorities=["Load Balancer", "CDN", "Object Storage", "WAF", "Monitoring"],
                scaling_guidance="Scale stateless web/API tiers and offload static product media to Object Storage/CDN before adding database capacity.",
                governance_weighting="Protect checkout, payment, and customer-data paths with stronger controls than browse-only paths.",
                cost_performance_tradeoff="CDN/offload reduces origin cost but cache invalidation and checkout consistency need explicit design.",
            ),
            "fintech": WorkloadOptimizationSignal(
                workload="fintech",
                service_priorities=["IAM", "Vault", "Logging", "Monitoring", "Full Stack Disaster Recovery", "Database Services"],
                scaling_guidance="Prioritize secure, auditable scaling and tested recovery over lowest-cost capacity decisions.",
                governance_weighting="DR evidence, encryption, audit retention, and least privilege carry higher weight than generic optimization.",
                cost_performance_tradeoff="Higher resilience/security spend is justified for regulated transaction paths but should be tiered by criticality.",
            ),
            "saas": WorkloadOptimizationSignal(
                workload="saas",
                service_priorities=["OKE", "Load Balancer", "IAM", "Vault", "Monitoring", "Cost Management"],
                scaling_guidance="Scale shared services separately from tenant workloads and track noisy-neighbor risk.",
                governance_weighting="Tenant isolation, data residency, and cost allocation are first-class review criteria.",
                cost_performance_tradeoff="Shared infrastructure improves utilization but needs guardrails for tenant blast radius and chargeback.",
            ),
            "analytics": WorkloadOptimizationSignal(
                workload="analytics",
                service_priorities=["Object Storage", "Data Integration", "Autonomous Database", "Logging", "Monitoring"],
                scaling_guidance="Optimize storage zones, pipeline throughput, replay, and query-serving tiers independently.",
                governance_weighting="Data classification, lifecycle, lineage, and access controls should gate platform expansion.",
                cost_performance_tradeoff="Storage tiering lowers cost but can affect query/restore latency for older data.",
            ),
            "ai/ml": WorkloadOptimizationSignal(
                workload="ai/ml inference",
                service_priorities=["Compute", "OKE", "Object Storage", "Vault", "Monitoring", "Cost Management"],
                scaling_guidance="Scale inference by measured concurrency, latency, batching, model size, and utilization.",
                governance_weighting="Model artifact access, rollout safety, and private endpoint design should be explicit.",
                cost_performance_tradeoff="GPU spend can improve latency but needs utilization thresholds and fallback shape options.",
            ),
            "observability": WorkloadOptimizationSignal(
                workload="observability",
                service_priorities=["Logging", "Monitoring", "Events", "Notifications", "Audit"],
                scaling_guidance="Scale retention, alarms, dashboards, and incident routing based on signal value and workload criticality.",
                governance_weighting="Audit evidence, alert ownership, and retention policy should be reviewable.",
                cost_performance_tradeoff="Longer retention improves auditability but should use explicit lifecycle and filtering policies.",
            ),
        }
        for domain in selected:
            signal = mapping.get(domain)
            if signal:
                signals.append(signal)
        return signals[:4]

    def _optimization_comparisons(
        self,
        *,
        text: str,
        profile: IntentProfile,
        sources: list[RetrievedSource],
    ) -> list[ArchitectureComparison]:
        source_ids = self._source_ids(sources, ())
        comparisons: list[ArchitectureComparison] = [
            ArchitectureComparison(
                decision="Cost-optimized vs resilience-optimized architecture",
                preferred_option="Use tiered resilience so critical paths get stronger protection and lower-tier components use cheaper recovery patterns.",
                alternatives=["Uniform active/active everywhere", "Lowest-cost single-region baseline"],
                pros=["Balances business criticality and spend", "Makes DR cost explicit", "Improves reviewability"],
                cons=["Requires workload tiering and RTO/RPO ownership"],
                governance_implications=["Budget owners and service owners must approve resilience tiers."],
                cost_implications="Controls cross-region and standby-capacity cost while preserving critical recovery posture.",
                operational_complexity="moderate",
                source_chunk_ids=source_ids[:3],
            )
        ]
        if any(term in text for term in ("managed", "self-managed", "database", "kubernetes", "oke", "vmware", "rds")):
            comparisons.append(
                ArchitectureComparison(
                    decision="Managed vs self-managed services",
                    preferred_option="Prefer managed OCI services when compatibility and governance requirements fit.",
                    alternatives=["Self-managed Compute or OKE-hosted services for special compatibility/control needs"],
                    pros=["Reduces patching and operational toil", "Improves standardization", "Accelerates migration waves"],
                    cons=["Requires compatibility validation and may constrain low-level tuning"],
                    governance_implications=["Service ownership shifts from platform operation to policy, configuration, and data governance."],
                    cost_implications="Managed service unit cost can be higher, but operational savings and reduced risk can improve total cost.",
                    operational_complexity="low_to_moderate",
                    source_chunk_ids=source_ids[:3],
                )
            )
        if any(term in text for term in ("serverless", "function", "container", "oke", "event-driven")):
            comparisons.append(
                ArchitectureComparison(
                    decision="Serverless vs containerized workloads",
                    preferred_option="Use Functions for stateless event-driven tasks and OKE for long-running services or platform workloads.",
                    alternatives=["Compute for simple persistent services"],
                    pros=["Aligns runtime model to workload behavior", "Avoids overbuilding platforms for small jobs"],
                    cons=["Requires clear state boundaries and deployment ownership"],
                    governance_implications=["Separate event permissions, image governance, runtime identity, and observability expectations."],
                    cost_implications="Functions can lower idle cost; OKE can be more predictable for steady high utilization.",
                    operational_complexity="context_dependent",
                    source_chunk_ids=source_ids[:3],
                )
            )
        if profile.intent.value in {"dr", "saas_platform"} or any(term in text for term in ("multi-region", "single-region", "rto", "rpo")):
            comparisons.append(
                ArchitectureComparison(
                    decision="Single-region vs multi-region deployment",
                    preferred_option="Use single-region plus backups for lower tiers and multi-region only where RTO/RPO or business continuity requires it.",
                    alternatives=["Multi-region active/active for critical paths", "Backup/restore for lower criticality"],
                    pros=["Aligns resilience spend to business value", "Keeps operational model simpler where possible"],
                    cons=["Requires explicit failover and data-residency decisions"],
                    governance_implications=["Architecture review should approve RTO/RPO, region choice, failover authority, and data placement."],
                    cost_implications="Multi-region increases steady-state, replication, networking, and test costs.",
                    operational_complexity="moderate_to_high",
                    source_chunk_ids=source_ids[:3],
                )
            )
        return comparisons[:4]

    def _recommendation_additions(
        self,
        *,
        migration_phases: list[MigrationPhasePlan],
        modernization_options: list[ModernizationOption],
        finops: list[FinOpsRecommendation],
        workload_signals: list[WorkloadOptimizationSignal],
        comparisons: list[ArchitectureComparison],
    ) -> list[str]:
        additions: list[str] = []
        if migration_phases:
            additions.append(
                "Use phased migration waves with discovery, coexistence/pilot validation, rollback rehearsals, and wave exit criteria before decommissioning source systems."
            )
        if modernization_options:
            additions.append(
                "Choose modernization approach per component: lift-and-shift for speed, replatform to managed OCI services for operational savings, and refactor only where measurable value and team readiness exist."
            )
        if finops:
            additions.extend(item.recommendation for item in finops[:3])
        if workload_signals:
            additions.append(
                "Apply workload-specific optimization signals for service priority, scaling strategy, governance weighting, and cost/performance tradeoffs instead of generic OCI sizing."
            )
        if comparisons:
            additions.append(
                "Use optimization comparisons to document cost-vs-resilience, managed-vs-self-managed, and runtime deployment tradeoffs before implementation."
            )
        return list(dict.fromkeys(additions))[:7]

    def _implementation_readiness(self, *, text: str, profile: IntentProfile) -> list[str]:
        checks = [
            "Implementation readiness: confirm workload owner, budget owner, operating team, and migration/change approver.",
            "Define telemetry baseline for utilization, latency, saturation, error rate, backup, and cost before optimization.",
            "Validate deterministic fallback, rollback, and operational runbook paths before production promotion.",
        ]
        if profile.intent.value in {"migration", "modernization"} or "migrat" in text:
            checks.extend(
                [
                    "Approve dependency map, coexistence plan, migration waves, and cutover rollback criteria.",
                    "Run pilot wave validation before scaling migration to higher-criticality systems.",
                ]
            )
        if any(term in text for term in ("cost", "budget", "optimize", "rightsizing")):
            checks.append("Create OCI Budgets/Cost Analysis review cadence and tag policy before rightsizing decisions.")
        return checks[:6]

    def _migration_type(self, text: str) -> str:
        if "vmware" in text:
            return "VMware"
        if "eks" in text or "kubernetes" in text:
            return "Kubernetes"
        if "rds" in text or "database" in text:
            return "database modernization"
        if "monolith" in text:
            return "monolith decomposition"
        if "hybrid" in text:
            return "hybrid-cloud"
        if "analytics" in text or "data" in text:
            return "data-platform"
        if "ai" in text or "inference" in text:
            return "AI/ML onboarding"
        return "migration"

    def _maturity_level(
        self,
        migration_phases: list[MigrationPhasePlan],
        modernization_options: list[ModernizationOption],
        finops: list[FinOpsRecommendation],
        workload_signals: list[WorkloadOptimizationSignal],
    ) -> str:
        score = sum(bool(item) for item in (migration_phases, modernization_options, finops, workload_signals))
        if score >= 3:
            return "implementation_ready"
        if score == 2:
            return "optimization_review_ready"
        if score == 1:
            return "targeted_guidance"
        return "baseline_advisory"

    def _source_ids(self, sources: list[RetrievedSource], terms: tuple[str, ...]) -> list[str]:
        if not terms:
            return list(dict.fromkeys(source.chunk_id for source in sources if source.chunk_id))
        matched = [
            source.chunk_id
            for source in sources
            if source.chunk_id
            and any(
                term in " ".join((source.title, source.summary, source.service or "", source.service_domain or "")).lower()
                for term in terms
            )
        ]
        return list(dict.fromkeys(matched))[:4] or [
            source.chunk_id for source in sources[:3] if source.chunk_id
        ]
