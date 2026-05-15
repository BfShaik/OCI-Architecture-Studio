import re
from dataclasses import dataclass
from enum import StrEnum


class Intent(StrEnum):
    PRODUCT_OVERVIEW = "product_overview"
    ARCHITECTURE = "architecture"
    MIGRATION = "migration"
    DR = "dr"
    COST = "cost"
    OBSERVABILITY = "observability"
    AI_ML = "ai_ml"
    SECURITY = "security"
    MODERNIZATION = "modernization"
    SAAS_PLATFORM = "saas_platform"
    ANALYTICS = "analytics"
    RELEASE_AWARENESS = "release_awareness"
    GENERAL = "general"


@dataclass(frozen=True)
class IntentProfile:
    intent: Intent
    prompt_template: str
    retrieval_terms: tuple[str, ...]
    focus: str
    recommendations: tuple[str, ...]
    assumptions: tuple[str, ...]
    risks: tuple[str, ...]
    next_steps: tuple[str, ...]


INTENT_PROFILES: dict[Intent, IntentProfile] = {
    Intent.PRODUCT_OVERVIEW: IntentProfile(
        intent=Intent.PRODUCT_OVERVIEW,
        prompt_template="prompts/architecture-review.product-overview.v0.md",
        retrieval_terms=(
            "OCI Architecture Studio",
            "architecture guidance",
            "migration advisory",
            "cost optimization",
            "release-aware knowledge",
            "RAG",
            "evaluations",
        ),
        focus="product capabilities, scope, grounding, and evaluation-driven OCI advisory workflows",
        recommendations=(
            "OCI Architecture Studio is an enterprise OCI architecture intelligence platform, not a generic chatbot.",
            "It helps with OCI architecture guidance, migration advisory, cost optimization, and release-aware OCI knowledge synchronization.",
            "It is designed around grounded retrieval, structured recommendations, prompt/version control, and regression evals so advice can be reviewed.",
            "The current implementation is an early local RAG foundation; production release intelligence and full OCI corpus coverage are future phases.",
        ),
        assumptions=(
            "The user is asking about the product itself, not for a target OCI workload design.",
            "The answer should describe platform scope without inventing unavailable features.",
        ),
        risks=(
            "Overstating current implementation maturity could misrepresent the product.",
            "Using generic chatbot language would obscure the enterprise OCI advisory scope.",
        ),
        next_steps=(
            "Keep product overview answers aligned with README, PRD, roadmap, and golden prompts.",
            "Add product documentation retrieval once docs are indexed alongside OCI source content.",
            "Create product-overview evals that catch generic or invented capability claims.",
        ),
    ),
    Intent.ARCHITECTURE: IntentProfile(
        intent=Intent.ARCHITECTURE,
        prompt_template="prompts/architecture-review.architecture.v0.md",
        retrieval_terms=(
            "high availability",
            "reference architecture",
            "load balancer",
            "VCN",
            "compute",
            "database",
            "Object Storage",
            "CDN",
            "ecommerce",
            "static assets",
        ),
        focus="availability, tier separation, traffic flow, data durability, operations, and service placement",
        recommendations=(
            "Use a multi-tier OCI design with public ingress, private application subnets, and a protected data tier.",
            "Place load balancing, compute capacity, and database services across availability and fault boundaries appropriate to the region.",
            "For ecommerce workloads, call out storefront, checkout, session/state, payment integration, catalog media on Object Storage or CDN, observability, and recovery requirements.",
            "Validate network, load balancing, compute, and database choices against retrieved OCI source context before production design.",
        ),
        assumptions=(
            "The platform needs public HTTPS ingress and private application/data tiers.",
            "Traffic volume, payment scope, and RTO/RPO targets still need confirmation.",
        ),
        risks=(
            "A generic HA design can miss checkout consistency, payment isolation, fraud controls, and peak-sale scaling needs.",
            "The current local corpus is small, so production service choices need review against full OCI documentation.",
        ),
        next_steps=(
            "Capture traffic, order volume, RTO/RPO, compliance, and integration requirements.",
            "Add OCI sources for WAF, autoscaling, and database HA.",
            "Create an ecommerce architecture eval that checks ingress, app tier, data tier, observability, and cost tradeoffs.",
        ),
    ),
    Intent.MIGRATION: IntentProfile(
        intent=Intent.MIGRATION,
        prompt_template="prompts/architecture-review.migration.v0.md",
        retrieval_terms=("migration", "EKS", "Kubernetes", "OKE", "RDS", "Oracle Database", "cutover"),
        focus="source-to-target mapping, dependency discovery, network connectivity, data migration, testing, and cutover",
        recommendations=(
            "Map EKS workloads to OCI Kubernetes Engine or an OCI compute pattern based on cluster features, ingress, storage, and operational ownership.",
            "Map RDS to the appropriate OCI database target, such as Oracle Base Database Service, Autonomous Database, MySQL HeatWave, or another managed database option after engine/version discovery.",
            "Plan migration waves around dependency mapping, image registry strategy, IAM changes, private networking, DNS, secrets, and rollback paths.",
            "Run parallel validation for data replication, application health checks, performance, and cutover before decommissioning AWS resources.",
        ),
        assumptions=(
            "The source platform includes Kubernetes workloads on EKS and relational data on RDS.",
            "The target database service depends on the current RDS engine, version, extensions, and operational requirements.",
        ),
        risks=(
            "A direct lift-and-shift can miss Kubernetes storage classes, ingress behavior, IAM mappings, and database compatibility gaps.",
            "Cutover risk remains high until replication, DNS, rollback, and performance tests are proven.",
        ),
        next_steps=(
            "Inventory EKS workloads, controllers, ingress, persistent volumes, secrets, and RDS engines.",
            "Add OCI sources for OKE, database migration, private connectivity, and container registry.",
            "Create migration evals that require explicit EKS-to-OKE and RDS-to-OCI database mapping.",
        ),
    ),
    Intent.DR: IntentProfile(
        intent=Intent.DR,
        prompt_template="prompts/architecture-review.dr.v0.md",
        retrieval_terms=("disaster recovery", "DR", "RTO", "RPO", "backup", "replication", "Data Guard", "cross-region", "fintech", "logging", "monitoring", "audit"),
        focus="RTO/RPO, cross-region design, database protection, failover, security, auditability, and operational runbooks",
        recommendations=(
            "Define fintech RTO/RPO tiers first, then map each application and data component to active-active, active-passive, backup/restore, or pilot-light DR.",
            "Prioritize resilient database protection with backups, replication, and Data Guard-style patterns where appropriate for the selected OCI database service.",
            "Design cross-region networking, DNS/failover, Vault-backed secrets, IAM, Logging, Monitoring, and runbooks as part of the DR architecture.",
            "Test DR with scheduled exercises that validate failover, data integrity, audit evidence, and return-to-primary procedures.",
        ),
        assumptions=(
            "The fintech workload has regulated data, audit requirements, and strict recovery expectations.",
            "Exact RTO/RPO, region pair, data residency, and database engine are not yet specified.",
            "Unsupported or invented OCI services must be rejected unless grounded in official OCI documentation.",
        ),
        risks=(
            "DR recommendations without RTO/RPO tiers can overbuild low-criticality systems or underprotect critical payment flows.",
            "Compliance evidence, key management, and operational runbooks can become blockers if added late.",
            "Conflicting requirements such as cheapest possible, globally active, zero downtime, no backups, and no monitoring must be resolved before design approval.",
        ),
        next_steps=(
            "Define application criticality tiers, RTO/RPO targets, and data residency constraints.",
            "Add OCI sources for Full Stack Disaster Recovery, Data Guard, backups, DNS, Vault, Logging, and Monitoring.",
            "Create a fintech DR eval that checks RTO/RPO, replication, failover, security, and audit controls.",
        ),
    ),
    Intent.COST: IntentProfile(
        intent=Intent.COST,
        prompt_template="prompts/architecture-review.cost.v0.md",
        retrieval_terms=("cost optimization", "right sizing", "autoscaling", "budgets", "usage", "compute", "storage"),
        focus="right-sizing, elasticity, managed-service fit, storage tiering, budget controls, and measurable tradeoffs",
        recommendations=(
            "Start with a lean web architecture and scale only bottlenecked tiers using right-sized compute, autoscaling, Object Storage for suitable static assets, and managed services where they reduce operational cost.",
            "Avoid over-provisioning shapes, database editions, and always-on capacity before demand is measured.",
            "Track cost drivers with budgets, tagging, usage monitoring, and environment lifecycle policies for dev/test workloads.",
            "Evaluate static assets, logs, backups, and artifacts for lower-cost storage patterns where performance requirements allow.",
        ),
        assumptions=(
            "The web app can start with modest capacity and grow based on measured demand.",
            "Performance, availability, and compliance requirements may constrain the cheapest possible service choices.",
            "There is not enough context for a production cost design until traffic, environments, data, backup, and security requirements are known.",
        ),
        risks=(
            "Cost optimization can reduce resilience if HA, backup, and monitoring requirements are not protected.",
            "A small corpus cannot yet validate all SKU, pricing, or licensing implications.",
        ),
        next_steps=(
            "Collect traffic, utilization, storage, backup, and database sizing estimates.",
            "Add OCI sources for Cost Analysis, Budgets, autoscaling, Object Storage, and database pricing considerations.",
            "Create a cost eval that requires concrete cost levers and tradeoffs, not only general architecture guidance.",
        ),
    ),
    Intent.OBSERVABILITY: IntentProfile(
        intent=Intent.OBSERVABILITY,
        prompt_template="prompts/architecture-review.general.v0.md",
        retrieval_terms=(
            "observability",
            "logging",
            "monitoring",
            "metrics",
            "alarms",
            "audit trails",
            "dashboards",
            "operational visibility",
        ),
        focus="logs, metrics, alarms, audit trails, dashboards, runbooks, and operational readiness",
        recommendations=(
            "Centralize OCI Logging and Monitoring coverage across application, infrastructure, database, and security signals.",
            "Tie alarms to service-level indicators such as latency, errors, saturation, availability, backup health, and security findings.",
            "Control log retention and access so observability supports incident response and audit without exposing sensitive data.",
            "Use observability requirements to validate architecture readiness before production cutover.",
        ),
        assumptions=(
            "The workload needs enterprise operational visibility but exact SLOs and retention requirements are not specified.",
            "Monitoring and logging controls must be validated against organization policy and compliance needs.",
        ),
        risks=(
            "Dashboards without alarms and runbooks can create visibility without operational response.",
            "Missing audit logs can block incident response, compliance evidence, and DR validation.",
            "Over-retention or unfiltered logs can increase cost and expose sensitive data.",
        ),
        next_steps=(
            "Define SLOs, alert thresholds, log retention, dashboard audiences, and incident-response ownership.",
            "Add or verify OCI sources for Logging, Monitoring, alarms, Audit, Notifications, and service-specific telemetry.",
            "Create observability evals that require logs, metrics, alarms, runbooks, security audit, and retention tradeoffs.",
        ),
    ),
    Intent.AI_ML: IntentProfile(
        intent=Intent.AI_ML,
        prompt_template="prompts/architecture-review.architecture.v0.md",
        retrieval_terms=(
            "AI inference",
            "model artifacts",
            "private API",
            "Object Storage",
            "compute",
            "Kubernetes",
            "logging",
            "monitoring",
            "cost-aware scaling",
        ),
        focus="AI/ML inference service placement, private access, model artifact handling, observability, security, and scaling tradeoffs",
        recommendations=(
            "Store model artifacts in durable, access-controlled Object Storage and validate rollout and rollback controls.",
            "Run inference serving on Compute or OCI Kubernetes Engine only after throughput, latency, and operational ownership are understood.",
            "Keep internal inference APIs on private networks where possible and protect secrets, keys, and data access with IAM and Vault-backed controls.",
            "Monitor inference latency, error rate, saturation, deployment health, and cost drivers before scaling capacity.",
        ),
        assumptions=(
            "The current corpus may not include dedicated OCI AI service evidence, so recommendations should stay grounded in retrieved compute, storage, networking, security, and observability sources.",
            "Traffic shape, model size, accelerator needs, and data sensitivity are not yet specified.",
        ),
        risks=(
            "GPU, accelerator, or specialized serving recommendations require sizing evidence and current OCI service validation.",
            "Sensitive prompts, inputs, outputs, and model artifacts can create data protection and retention risk.",
            "Always-on inference capacity can become costly without autoscaling and utilization monitoring.",
        ),
        next_steps=(
            "Capture latency, throughput, concurrency, model size, artifact lifecycle, data sensitivity, and deployment requirements.",
            "Add OCI AI/ML and model-serving sources before making specialized service claims.",
            "Create an AI inference eval that checks private access, artifact security, observability, and cost-aware scaling.",
        ),
    ),
    Intent.MODERNIZATION: IntentProfile(
        intent=Intent.MODERNIZATION,
        prompt_template="prompts/architecture-review.migration.v0.md",
        retrieval_terms=(
            "modernization",
            "container platform",
            "managed database",
            "migration waves",
            "OKE",
            "Autonomous Database",
            "observability",
            "security",
        ),
        focus="incremental modernization, managed-service fit, container platform choices, operational ownership, migration waves, and rollback",
        recommendations=(
            "Separate lift-and-shift migration decisions from modernization decisions so risk can be managed in waves.",
            "Use OKE, managed database options, Object Storage, and observability controls where they reduce operational burden and fit workload constraints.",
            "Prioritize dependency discovery, compatibility validation, IAM/network changes, and rollback paths before changing runtime architecture.",
            "Modernize only the components with clear reliability, cost, security, or operational benefits.",
        ),
        assumptions=(
            "The workload may be moving from an existing platform and needs incremental change rather than a full rewrite.",
            "Current runtime, database engine, dependencies, and operational constraints still need discovery.",
        ),
        risks=(
            "Modernization can expand scope and delay migration if it is not separated into measurable waves.",
            "Managed-service fit depends on compatibility, licensing, operational ownership, and performance requirements.",
        ),
        next_steps=(
            "Inventory source runtime, data stores, dependencies, deployment process, and operational pain points.",
            "Define modernization candidates and acceptance criteria by migration wave.",
            "Run migration and modernization evals for explicit source-to-target mapping and rollback coverage.",
        ),
    ),
    Intent.SAAS_PLATFORM: IntentProfile(
        intent=Intent.SAAS_PLATFORM,
        prompt_template="prompts/architecture-review.architecture.v0.md",
        retrieval_terms=(
            "SaaS platform",
            "tenant isolation",
            "multi region",
            "shared services",
            "database resilience",
            "cost allocation",
            "observability",
        ),
        focus="tenant isolation, shared platform services, multi-region resilience, observability, cost allocation, and migration-aware platform growth",
        recommendations=(
            "Define the tenant isolation model before choosing network, database, IAM, and operational boundaries.",
            "Separate public ingress, shared platform services, tenant workloads, data tiers, and observability controls.",
            "Use tagging, budgets, and cost reporting patterns to support tenant, environment, and shared-service cost visibility.",
            "Treat multi-region expansion as an HA/DR and data-placement decision with explicit consistency, failover, and residency assumptions.",
        ),
        assumptions=(
            "Tenant count, isolation tier, region strategy, data residency, and source-platform context are not fully specified.",
            "Multi-region SaaS may need AWS-to-OCI migration mapping if the source services are mentioned.",
        ),
        risks=(
            "Weak tenant isolation can create security, compliance, and noisy-neighbor risk.",
            "Multi-region data consistency, failover, and operational runbooks can dominate platform complexity.",
            "Shared-service costs can become opaque without tagging and allocation controls.",
        ),
        next_steps=(
            "Define tenant isolation, data residency, region strategy, RTO/RPO, and cost allocation requirements.",
            "Add SaaS-specific evals that require isolation, multi-region tradeoffs, observability, and cost controls.",
            "Run migration mapping when AWS-origin services are present.",
        ),
    ),
    Intent.ANALYTICS: IntentProfile(
        intent=Intent.ANALYTICS,
        prompt_template="prompts/architecture-review.architecture.v0.md",
        retrieval_terms=(
            "analytics",
            "data platform",
            "Object Storage",
            "database",
            "data tier",
            "lifecycle management",
            "monitoring",
            "cost optimization",
        ),
        focus="data ingestion, storage, database/service fit, lifecycle controls, governance, observability, and cost-aware analytics architecture",
        recommendations=(
            "Separate raw, curated, and serving data concerns before selecting storage and database services.",
            "Use Object Storage lifecycle controls and managed database choices where they fit retention, query, and operational requirements.",
            "Protect data access with IAM, encryption, private networking, logging, and audit-ready controls.",
            "Monitor ingestion, freshness, query performance, storage growth, and cost drivers.",
        ),
        assumptions=(
            "The analytics workload requirements, data volume, query pattern, and governance scope are not yet specified.",
            "The current corpus may not contain specialized analytics services, so guidance must stay bounded by retrieved evidence.",
        ),
        risks=(
            "Analytics designs can overfit storage or database choices before query, retention, and governance needs are clear.",
            "Cost and performance risks rise quickly if data lifecycle and monitoring are omitted.",
        ),
        next_steps=(
            "Capture source systems, volume, latency, query patterns, governance, retention, and consumers.",
            "Add OCI analytics-specific sources before recommending specialized analytics services.",
            "Create analytics evals that require data lifecycle, security, observability, and cost tradeoffs.",
        ),
    ),
    Intent.SECURITY: IntentProfile(
        intent=Intent.SECURITY,
        prompt_template="prompts/architecture-review.security.v0.md",
        retrieval_terms=("security", "IAM", "Vault", "Cloud Guard", "network security groups", "logging", "encryption"),
        focus="identity, network isolation, encryption, secrets, detection, logging, and least privilege",
        recommendations=(
            "Start with least-privilege IAM, compartment boundaries, and explicit separation of duties.",
            "Use private subnets, network security groups, and controlled ingress/egress paths for application and data tiers.",
            "Protect secrets and keys with managed key/secrets services and require encryption for data in transit and at rest.",
            "Enable logging, monitoring, and security posture checks so architecture controls are observable and auditable.",
        ),
        assumptions=(
            "The workload has enterprise security requirements but exact compliance scope is not specified.",
            "Identity, network, and data protection controls must be validated against organization policy.",
        ),
        risks=(
            "Security guidance can be incomplete without compliance, data classification, and identity-provider details.",
            "Network controls alone do not cover secrets, audit, detection, or operational access.",
        ),
        next_steps=(
            "Define data classification, compliance scope, identity provider, and operational access model.",
            "Add OCI sources for IAM, Vault, Cloud Guard, Security Zones, Logging, and Audit.",
            "Create a security eval that checks identity, network, encryption, detection, and auditability.",
        ),
    ),
    Intent.RELEASE_AWARENESS: IntentProfile(
        intent=Intent.RELEASE_AWARENESS,
        prompt_template="prompts/architecture-review.release-awareness.v0.md",
        retrieval_terms=(
            "latest OCI update",
            "release notes",
            "service update",
            "current release",
            "architecture impact",
            "knowledge refresh",
        ),
        focus="current release context, architecture impact analysis, freshness boundaries, and non-hallucination",
        recommendations=(
            "Ask for the specific OCI release note, service update, date, or affected service before declaring architectural impact.",
            "Separate what the local RAG index can currently support from what must be verified against latest OCI release sources.",
            "Assess impact by checking whether the affected service, including Load Balancer when relevant, changes service limits, availability, security posture, pricing, migration path, or operational behavior.",
            "Refresh the OCI knowledge index and rerun relevant architecture, migration, DR, cost, or security evals before changing a recommendation.",
        ),
        assumptions=(
            "The prompt references a latest update but does not provide the actual release note or service name.",
            "The local index is a snapshot and should not be treated as current release truth.",
        ),
        risks=(
            "Answering without current release context can produce stale or hallucinated guidance.",
            "A release can affect only a narrow service, region, limit, price, or feature, so broad impact claims need evidence.",
        ),
        next_steps=(
            "Provide the OCI release note URL, service name, date, or update summary.",
            "Run the ingestion pipeline against approved current OCI release sources.",
            "Compare pre-update and post-update recommendations and record affected assumptions, risks, and service choices.",
        ),
    ),
    Intent.GENERAL: IntentProfile(
        intent=Intent.GENERAL,
        prompt_template="prompts/architecture-review.general.v0.md",
        retrieval_terms=("OCI", "architecture", "well architected", "networking", "compute"),
        focus="general OCI architecture tradeoffs and assumptions",
        recommendations=(
            "Clarify the workload goal, users, data, integration points, and non-functional requirements.",
            "Use retrieved OCI context to identify candidate services and the assumptions behind each recommendation.",
            "Separate architecture decisions from implementation details until requirements and constraints are clear.",
            "Escalate gaps where the local corpus does not provide enough grounded context.",
        ),
        assumptions=(
            "The request does not strongly match a specialized intent.",
            "More context is needed before making production service choices.",
        ),
        risks=(
            "A broad question can produce broad guidance unless the workload goal is narrowed.",
            "Missing requirements can lead to service choices that do not fit cost, security, or resilience needs.",
        ),
        next_steps=(
            "Ask for workload, constraints, and success criteria.",
            "Expand the corpus for the most common OCI design areas.",
            "Add evals for ambiguous general questions.",
        ),
    ),
}


class IntentClassifier:
    def classify(self, text: str) -> Intent:
        normalized = text.lower()

        if "oci architecture studio" in normalized and any(
            token in normalized for token in ("what", "do", "does", "purpose", "explain")
        ):
            return Intent.PRODUCT_OVERVIEW
        if any(
            token in normalized
            for token in (
                "latest",
                "release",
                "update",
                "new oci",
                "recent change",
                "changed",
                "current",
            )
        ):
            return Intent.RELEASE_AWARENESS
        if any(token in normalized for token in ("migrate", "migration")) or re.search(r"\b(eks|rds|aws)\b", normalized):
            return Intent.MIGRATION
        if any(token in normalized for token in ("ai/ml", "ai inference", "model", "inference", "ml platform", "machine learning")):
            return Intent.AI_ML
        if any(token in normalized for token in ("saas", "tenant", "multi-tenant", "multi tenant", "multi-region", "multi region")):
            return Intent.SAAS_PLATFORM
        if any(token in normalized for token in ("analytics", "data platform", "data lake", "warehouse", "reporting", "pipeline scaling")):
            return Intent.ANALYTICS
        if any(token in normalized for token in ("dr", "disaster recovery", "rto", "rpo", "failover", "fintech")):
            return Intent.DR
        if any(token in normalized for token in ("cost", "cost-optimized", "budget", "right-size", "right sized", "cheap")):
            return Intent.COST
        if any(token in normalized for token in ("observability", "logging", "monitoring", "metrics", "alarms", "dashboard", "audit trail")):
            return Intent.OBSERVABILITY
        if any(token in normalized for token in ("security", "secure", "iam", "vault", "encryption", "compliance")):
            return Intent.SECURITY
        if any(token in normalized for token in ("modernize", "modernization", "refactor", "replatform", "managed database")):
            return Intent.MODERNIZATION
        if any(token in normalized for token in ("design", "architecture", "architect", "highly available", "ecommerce", "platform")):
            return Intent.ARCHITECTURE
        return Intent.GENERAL


def get_intent_profile(intent: Intent) -> IntentProfile:
    return INTENT_PROFILES[intent]
