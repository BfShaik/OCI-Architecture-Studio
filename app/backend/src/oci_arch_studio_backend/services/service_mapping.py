from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class ServiceMapping:
    source_service: str
    target_services: tuple[str, ...]
    retrieval_terms: tuple[str, ...]
    source_aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class QueryServiceMapping:
    mappings: tuple[ServiceMapping, ...]

    @property
    def mapped_services(self) -> tuple[str, ...]:
        services: list[str] = []
        for mapping in self.mappings:
            services.extend(mapping.target_services)
        return tuple(dict.fromkeys(services))

    @property
    def retrieval_terms(self) -> tuple[str, ...]:
        terms: list[str] = []
        for mapping in self.mappings:
            terms.extend(mapping.retrieval_terms)
        return tuple(dict.fromkeys(terms))

    def summary(self) -> str:
        if not self.mappings:
            return "No source cloud service mappings detected."
        return "; ".join(
            f"{mapping.source_service} -> {', '.join(mapping.target_services)}"
            for mapping in self.mappings
        )


AWS_TO_OCI_MAPPINGS: tuple[ServiceMapping, ...] = (
    ServiceMapping(
        source_service="EKS",
        target_services=("OCI Kubernetes Engine",),
        retrieval_terms=("OKE", "OCI Kubernetes Engine", "Kubernetes", "container platform", "node pools"),
        source_aliases=("Elastic Kubernetes Service", "Kubernetes"),
    ),
    ServiceMapping(
        source_service="EKS ALB",
        target_services=("Load Balancer",),
        retrieval_terms=("OCI Load Balancer", "Kubernetes ingress", "public ingress", "backend health checks"),
        source_aliases=("AWS Load Balancer Controller", "ALB", "AWS ALB", "ALB ingress", "Application Load Balancer"),
    ),
    ServiceMapping(
        source_service="ECR",
        target_services=("Container Registry",),
        retrieval_terms=("Container Registry", "container registry", "image migration", "container image security"),
        source_aliases=("Elastic Container Registry",),
    ),
    ServiceMapping(
        source_service="RDS",
        target_services=("Database Migration", "Database Services", "Autonomous Database"),
        retrieval_terms=("OCI Base Database", "Autonomous Database", "Database Migration", "database engine compatibility"),
    ),
    ServiceMapping(
        source_service="S3",
        target_services=("Object Storage",),
        retrieval_terms=("Object Storage", "S3-compatible", "buckets", "static assets", "backups"),
    ),
    ServiceMapping(
        source_service="CloudFront",
        target_services=("CDN",),
        retrieval_terms=("OCI CDN", "edge delivery", "origin offload", "static asset delivery"),
    ),
    ServiceMapping(
        source_service="Route53",
        target_services=("OCI DNS",),
        retrieval_terms=("OCI DNS", "DNS cutover", "traffic management", "failover"),
        source_aliases=("Route 53", "route fifty three"),
    ),
    ServiceMapping(
        source_service="Fargate",
        target_services=("OKE Virtual Nodes", "OCI Kubernetes Engine"),
        retrieval_terms=("OKE Virtual Nodes", "serverless containers", "container workload migration"),
    ),
    ServiceMapping(
        source_service="Lambda",
        target_services=("OCI Functions",),
        retrieval_terms=("OCI Functions", "serverless functions", "event-driven workloads", "function migration"),
        source_aliases=("AWS Lambda",),
    ),
    ServiceMapping(
        source_service="VPC",
        target_services=("Virtual Cloud Network",),
        retrieval_terms=("VCN", "Virtual Cloud Network", "private subnets", "network security groups", "routing"),
        source_aliases=("AWS VPC",),
    ),
    ServiceMapping(
        source_service="Security Groups",
        target_services=("Network Security Groups",),
        retrieval_terms=("Network Security Groups", "NSG", "east-west controls", "network isolation"),
        source_aliases=("security group", "SG"),
    ),
    ServiceMapping(
        source_service="CloudWatch",
        target_services=("Logging", "Monitoring"),
        retrieval_terms=("OCI Logging", "OCI Monitoring", "metrics", "alarms", "audit logs"),
    ),
    ServiceMapping(
        source_service="AWS IAM",
        target_services=("Identity and Access Management",),
        retrieval_terms=("OCI IAM", "identity domains", "policies", "least privilege", "compartments"),
        source_aliases=("IAM", "AWS Identity and Access Management"),
    ),
    ServiceMapping(
        source_service="KMS",
        target_services=("Vault",),
        retrieval_terms=("OCI Vault", "key management", "encryption keys", "secrets"),
        source_aliases=("AWS KMS", "Secrets Manager", "Parameter Store"),
    ),
    ServiceMapping(
        source_service="GuardDuty",
        target_services=("Cloud Guard",),
        retrieval_terms=("Cloud Guard", "posture management", "threat detection"),
        source_aliases=("Security Hub",),
    ),
    ServiceMapping(
        source_service="SageMaker",
        target_services=("OCI Data Science", "Compute", "Object Storage"),
        retrieval_terms=("OCI Data Science", "AI inference", "model artifacts", "GPU", "model deployment"),
    ),
    ServiceMapping(
        source_service="Glue",
        target_services=("OCI Data Integration", "Object Storage"),
        retrieval_terms=("OCI Data Integration", "data pipelines", "ETL", "Object Storage", "data lake"),
    ),
    ServiceMapping(
        source_service="Kinesis",
        target_services=("OCI Streaming", "Logging", "Monitoring"),
        retrieval_terms=("OCI Streaming", "streaming ingestion", "pipeline scaling", "monitoring"),
    ),
    ServiceMapping(
        source_service="Redshift",
        target_services=("Autonomous Database", "Object Storage"),
        retrieval_terms=("Autonomous Database", "analytics", "data warehouse", "Object Storage"),
    ),
)


class OciServiceMapper:
    def map_text(self, text: str) -> QueryServiceMapping:
        normalized = text.lower()
        detected = tuple(
            mapping
            for mapping in AWS_TO_OCI_MAPPINGS
            if self._matches_mapping(normalized, mapping)
        )
        return QueryServiceMapping(mappings=detected)

    def _matches_mapping(self, normalized_text: str, mapping: ServiceMapping) -> bool:
        return any(
            re.search(rf"(?<![a-z0-9]){re.escape(alias.lower())}(?![a-z0-9])", normalized_text)
            for alias in (mapping.source_service, *mapping.source_aliases)
        )
