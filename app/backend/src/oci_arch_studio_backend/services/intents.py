from dataclasses import dataclass
from enum import StrEnum


class Intent(StrEnum):
    PRODUCT_OVERVIEW = "product_overview"
    ARCHITECTURE = "architecture"
    MIGRATION = "migration"
    DR = "dr"
    COST = "cost"
    SECURITY = "security"
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
        retrieval_terms=("disaster recovery", "DR", "RTO", "RPO", "backup", "replication", "Data Guard", "cross-region", "fintech"),
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
        if any(token in normalized for token in ("migrate", "migration", "eks", "rds", "aws")):
            return Intent.MIGRATION
        if any(token in normalized for token in ("dr", "disaster recovery", "rto", "rpo", "failover", "fintech")):
            return Intent.DR
        if any(token in normalized for token in ("cost", "cost-optimized", "budget", "right-size", "right sized", "cheap")):
            return Intent.COST
        if any(token in normalized for token in ("security", "secure", "iam", "vault", "encryption", "compliance")):
            return Intent.SECURITY
        if any(token in normalized for token in ("design", "architecture", "architect", "highly available", "ecommerce", "platform")):
            return Intent.ARCHITECTURE
        return Intent.GENERAL


def get_intent_profile(intent: Intent) -> IntentProfile:
    return INTENT_PROFILES[intent]
