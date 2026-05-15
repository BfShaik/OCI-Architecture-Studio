from __future__ import annotations

from dataclasses import dataclass

from oci_arch_studio_backend.models.architecture import RetrievedSource
from oci_arch_studio_backend.services.intents import IntentProfile


@dataclass(frozen=True)
class ArchitecturePatternProfile:
    name: str
    triggers: tuple[str, ...]
    service_priorities: tuple[str, ...]
    design_moves: tuple[str, ...]
    risks: tuple[str, ...]
    next_steps: tuple[str, ...]


PATTERN_PROFILES: tuple[ArchitecturePatternProfile, ...] = (
    ArchitecturePatternProfile(
        name="highly_available_web_application",
        triggers=("web app", "webapp", "ecommerce", "storefront", "checkout", "highly available"),
        service_priorities=("Load Balancer", "Web Application Firewall", "Compute", "OCI Kubernetes Engine", "Database Services", "Object Storage", "CDN", "Logging", "Monitoring"),
        design_moves=(
            "Segment the VCN into public ingress, private application, and private data tiers; expose only the load balancer and keep application/database endpoints private.",
            "Use Load Balancer health checks with horizontally scalable Compute or OKE capacity, and offload static assets to Object Storage plus CDN where evidence supports it.",
            "Protect checkout and identity paths with WAF, least-privilege IAM, TLS, logging, and monitoring tied to latency, error, and order-flow SLOs.",
        ),
        risks=(
            "Peak traffic can exhaust app or database capacity if autoscaling and connection limits are not tested.",
            "Checkout consistency, payment integrations, and media delivery need separate failure-mode validation.",
        ),
        next_steps=(
            "Confirm traffic profile, RTO/RPO, payment scope, catalog media volume, and deployment model.",
            "Run load, failover, and backup-restore tests before production approval.",
        ),
    ),
    ArchitecturePatternProfile(
        name="kubernetes_modernization_platform",
        triggers=("kubernetes", "oke", "eks", "container", "modernization", "modernize"),
        service_priorities=("OCI Kubernetes Engine", "Load Balancer", "Network Security Groups", "Identity and Access Management", "Logging", "Monitoring", "Object Storage", "Database Migration"),
        design_moves=(
            "Map Kubernetes workloads to OKE with explicit decisions for ingress, node pools or virtual nodes, persistent storage, image registry, secrets, and controller compatibility.",
            "Place worker nodes in private subnets, use NSGs for east-west controls, and separate platform namespaces from application namespaces.",
            "Migrate by waves: base network/IAM, container image pipeline, stateless services, stateful services, data dependencies, DNS cutover, and rollback.",
        ),
        risks=(
            "Kubernetes lift-and-shift can fail on storage classes, ingress controllers, IAM bindings, secrets, and unsupported operators.",
            "Cutover risk remains high until rollback, health checks, and dependency tests pass.",
        ),
        next_steps=(
            "Inventory workloads, controllers, ingresses, persistent volumes, secrets, and service accounts.",
            "Create a canary migration wave with measurable success and rollback criteria.",
        ),
    ),
    ArchitecturePatternProfile(
        name="fintech_disaster_recovery_platform",
        triggers=("fintech", "payment", "regulated", "rto", "rpo", "disaster recovery", "dr"),
        service_priorities=("Full Stack Disaster Recovery", "Database Services", "Autonomous Database", "Vault", "Identity and Access Management", "Logging", "Monitoring", "Object Storage", "Virtual Cloud Network"),
        design_moves=(
            "Define RTO/RPO tiers first, then assign each application and data component to active-active, active-passive, pilot-light, or backup/restore posture.",
            "Use database backup, replication, and Data Guard-style protection where the selected database service supports it; validate failover and return-to-primary runbooks.",
            "Treat Vault, IAM, audit logs, monitoring alarms, and compliance evidence as part of the DR design rather than after-the-fact controls.",
        ),
        risks=(
            "Payment state, key availability, and audit evidence can become DR blockers if not tested together.",
            "Active-active can increase cost and consistency risk without explicit business justification.",
        ),
        next_steps=(
            "Set tiered RTO/RPO targets, data residency constraints, failover authority, and audit evidence requirements.",
            "Run scheduled DR exercises that verify data integrity, key access, observability, and recovery procedures.",
        ),
    ),
    ArchitecturePatternProfile(
        name="ai_inference_platform",
        triggers=("ai", "ai/ml", "inference", "model", "gpu", "sagemaker"),
        service_priorities=("Compute", "OCI Kubernetes Engine", "Object Storage", "Load Balancer", "Virtual Cloud Network", "Vault", "Logging", "Monitoring", "Cost Management"),
        design_moves=(
            "Store model artifacts in Object Storage with IAM-controlled access, artifact versioning assumptions, and rollout/rollback gates.",
            "Keep inference APIs private unless public access is explicitly required; front them with controlled ingress and monitor latency, error rate, saturation, and model-serving health.",
            "Choose Compute, GPU shapes, or OKE only after throughput, latency, model size, and utilization requirements are known; avoid always-on overcapacity by default.",
        ),
        risks=(
            "GPU and specialized serving choices can become expensive or wrong without measured concurrency, latency, and model-size inputs.",
            "Prompt/input/output retention and model artifact access can create security and compliance risk.",
        ),
        next_steps=(
            "Capture latency SLOs, request concurrency, model size, artifact lifecycle, data sensitivity, and scaling policy.",
            "Prototype one model-serving path and measure saturation before committing capacity.",
        ),
    ),
    ArchitecturePatternProfile(
        name="analytics_data_lake_platform",
        triggers=("analytics", "data lake", "data platform", "pipeline", "warehouse", "glue", "redshift"),
        service_priorities=("Object Storage", "Autonomous Database", "Database Services", "Logging", "Monitoring", "Identity and Access Management", "Cost Management"),
        design_moves=(
            "Separate raw, curated, and serving zones; use Object Storage lifecycle controls and database services according to query, retention, and governance needs.",
            "Design ingestion and transformation pipelines around throughput, replay, schema evolution, observability, and failure isolation.",
            "Apply IAM, encryption, logging, and retention policies to each data zone so governance and cost controls are visible.",
        ),
        risks=(
            "Storage growth, query sprawl, and pipeline retries can create uncontrolled cost without lifecycle and monitoring controls.",
            "Analytics service choices are provisional until data volume, freshness, query patterns, and governance requirements are known.",
        ),
        next_steps=(
            "Document source systems, data volume, freshness targets, retention, consumers, and query patterns.",
            "Add specialized OCI analytics sources before making detailed service commitments beyond the retrieved evidence.",
        ),
    ),
    ArchitecturePatternProfile(
        name="saas_multi_region_platform",
        triggers=("saas", "tenant", "multi-tenant", "multi tenant", "multi-region", "multi region"),
        service_priorities=("Load Balancer", "OCI Kubernetes Engine", "Compute", "Database Services", "Autonomous Database", "Object Storage", "CDN", "Identity and Access Management", "Vault", "Logging", "Monitoring", "Cost Management"),
        design_moves=(
            "Define tenant isolation before choosing compartment, VCN, namespace, database, and operational boundaries.",
            "Separate shared platform services from tenant workloads; design cost tags, budgets, and observability around tenant and environment boundaries.",
            "Treat multi-region as an HA/DR decision with explicit traffic failover, data placement, consistency, residency, and runbook assumptions.",
        ),
        risks=(
            "Weak tenant isolation can create security, compliance, and noisy-neighbor risk.",
            "Multi-region data replication and failover can increase cost and operational complexity without clear RTO/RPO and residency requirements.",
        ),
        next_steps=(
            "Choose tenant isolation tier, region strategy, data residency model, and cost allocation method.",
            "Validate failover, tenant-level observability, and shared-service blast-radius controls.",
        ),
    ),
)


class ArchitecturePatternSelector:
    def select(
        self,
        *,
        question: str,
        workload_context: str | None,
        profile: IntentProfile,
        sources: list[RetrievedSource],
    ) -> ArchitecturePatternProfile:
        haystack = " ".join(
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
        scored = [
            (sum(1 for trigger in pattern.triggers if trigger.lower() in haystack), pattern)
            for pattern in PATTERN_PROFILES
        ]
        scored.sort(key=lambda item: item[0], reverse=True)
        if scored and scored[0][0] > 0:
            return scored[0][1]
        return PATTERN_PROFILES[0]
