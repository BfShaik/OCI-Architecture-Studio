from __future__ import annotations

import re

from oci_arch_studio_backend.models.architecture import (
    ArchitectureTopologyNode,
    ArchitectureTopologyRelationship,
    ArchitectureTopologySummary,
    RetrievedSource,
)
from oci_arch_studio_backend.services.intents import IntentProfile


SERVICE_ROLES: tuple[tuple[str, str], ...] = (
    ("api gateway", "ingress"),
    ("waf", "edge-security"),
    ("cdn", "edge-delivery"),
    ("dns", "traffic-management"),
    ("load balancer", "ingress"),
    ("oke", "application-runtime"),
    ("kubernetes engine", "application-runtime"),
    ("compute", "application-runtime"),
    ("functions", "serverless-runtime"),
    ("object storage", "storage"),
    ("database", "data"),
    ("autonomous database", "data"),
    ("base database", "data"),
    ("vault", "security"),
    ("iam", "identity"),
    ("identity", "identity"),
    ("logging", "observability"),
    ("monitoring", "observability"),
    ("audit", "audit"),
    ("notifications", "operations"),
    ("events", "operations"),
    ("full stack disaster recovery", "dr-orchestration"),
    ("database migration", "migration"),
    ("data integration", "data-pipeline"),
    ("streaming", "event-stream"),
)


class ArchitectureTopologyBuilder:
    """Builds lightweight topology metadata for review and future UI diagrams."""

    def build(
        self,
        *,
        question: str,
        workload_context: str | None,
        profile: IntentProfile,
        sources: list[RetrievedSource],
        recommendations: list[str],
    ) -> ArchitectureTopologySummary:
        source_ids = self._source_ids(sources)
        nodes = self._nodes(sources, recommendations)
        relationships = self._relationships(nodes, profile, source_ids)
        return ArchitectureTopologySummary(
            topology_summary=self._summary(profile, nodes, question, workload_context),
            deployment_topology=self._deployment_topology(profile, nodes),
            ha_dr_topology=self._ha_dr_topology(profile, nodes, recommendations, question, workload_context),
            service_dependencies=relationships,
            nodes=nodes,
            mermaid_flow=self._mermaid(nodes, relationships),
            operational_notes=self._operational_notes(nodes, profile),
            source_chunk_ids=source_ids[:8],
        )

    def _nodes(
        self,
        sources: list[RetrievedSource],
        recommendations: list[str],
    ) -> list[ArchitectureTopologyNode]:
        candidates: dict[str, ArchitectureTopologyNode] = {}
        for source in sources:
            label = source.service or source.title
            role = self._role(label, source.service_domain, source.service_category)
            node_id = self._node_id(label)
            candidates[node_id] = ArchitectureTopologyNode(
                node_id=node_id,
                label=label,
                service=source.service,
                category=source.service_category or source.service_domain or source.category,
                role=role,
                source_chunk_ids=[source.chunk_id] if source.chunk_id else [],
            )
        recommendation_text = " ".join(recommendations).lower()
        for service, role in SERVICE_ROLES:
            if service not in recommendation_text:
                continue
            label = self._label(service)
            node_id = self._node_id(label)
            if node_id not in candidates:
                candidates[node_id] = ArchitectureTopologyNode(
                    node_id=node_id,
                    label=label,
                    service=label,
                    category=role,
                    role=role,
                )
        return list(candidates.values())[:12]

    def _relationships(
        self,
        nodes: list[ArchitectureTopologyNode],
        profile: IntentProfile,
        source_ids: list[str],
    ) -> list[ArchitectureTopologyRelationship]:
        by_role: dict[str, ArchitectureTopologyNode] = {}
        for node in nodes:
            by_role.setdefault(node.role, node)

        relationships: list[ArchitectureTopologyRelationship] = []

        def connect(left: str, right: str, relationship: str, rationale: str) -> None:
            if left not in by_role or right not in by_role:
                return
            relationships.append(
                ArchitectureTopologyRelationship(
                    from_node=by_role[left].node_id,
                    to_node=by_role[right].node_id,
                    relationship=relationship,
                    rationale=rationale,
                    source_chunk_ids=source_ids[:3],
                )
            )

        connect("edge-delivery", "ingress", "routes_to", "Edge delivery should route through controlled ingress.")
        connect("traffic-management", "ingress", "resolves_to", "DNS or traffic management directs users to the ingress tier.")
        connect("edge-security", "ingress", "protects", "Edge security controls should protect the public entry point.")
        connect("ingress", "application-runtime", "forwards_to", "Ingress forwards validated traffic to the application runtime.")
        connect("ingress", "serverless-runtime", "invokes", "Ingress can invoke stateless serverless entry points where appropriate.")
        connect("application-runtime", "data", "reads_writes", "Application runtime depends on a governed data tier.")
        connect("serverless-runtime", "data", "reads_writes", "Serverless functions should access data through managed service boundaries.")
        connect("application-runtime", "storage", "uses", "Runtime services use Object Storage for artifacts, static assets, or durable objects.")
        connect("application-runtime", "security", "uses", "Runtime services should use Vault for secrets and key material.")
        connect("identity", "application-runtime", "authorizes", "OCI IAM policies and identity boundaries authorize runtime access.")
        connect("observability", "application-runtime", "observes", "Logging and Monitoring should cover runtime health and SLOs.")
        connect("observability", "data", "observes", "Data services need telemetry, alarms, and backup visibility.")
        connect("dr-orchestration", "application-runtime", "coordinates_recovery", "DR orchestration coordinates application recovery runbooks.")
        connect("dr-orchestration", "data", "coordinates_recovery", "DR orchestration must include data-tier recovery validation.")
        if profile.intent.value in {"migration", "modernization"}:
            connect("migration", "application-runtime", "modernizes_to", "Migration sequencing should land workloads on the target runtime.")
            connect("migration", "data", "migrates_to", "Migration sequencing should include data validation and rollback gates.")
        return relationships[:14]

    def _summary(
        self,
        profile: IntentProfile,
        nodes: list[ArchitectureTopologyNode],
        question: str,
        workload_context: str | None,
    ) -> str:
        services = ", ".join(node.label for node in nodes[:6]) or "retrieved OCI services"
        context = " ".join(part for part in (question, workload_context) if part).lower()
        if "executive" in context or "board" in context:
            return f"Executive review topology for {profile.intent.value}: {services}, with explicit governance, risk, and operating-model checkpoints."
        return f"Architecture topology for {profile.intent.value}: {services}, organized around ingress, runtime, data, security, observability, and operations."

    def _deployment_topology(self, profile: IntentProfile, nodes: list[ArchitectureTopologyNode]) -> str:
        roles = {node.role for node in nodes}
        runtime = "OKE or Compute runtime" if "application-runtime" in roles else "configured OCI runtime"
        if "serverless-runtime" in roles:
            runtime = "OCI Functions for stateless event-driven execution"
        if profile.intent.value in {"migration", "modernization"}:
            return f"Use migration waves into {runtime}, with coexistence, cutover rehearsal, rollback gates, and operational acceptance."
        return f"Deploy through the selected OCI runtime profile using {runtime}, OCI-managed identity, Vault-backed configuration, and observable ingress."

    def _ha_dr_topology(
        self,
        profile: IntentProfile,
        nodes: list[ArchitectureTopologyNode],
        recommendations: list[str],
        question: str,
        workload_context: str | None,
    ) -> str:
        text = " ".join((question, workload_context or "", " ".join(recommendations))).lower()
        if profile.intent.value == "dr" or any(term in text for term in ("rto", "rpo", "failover", "multi-region", "disaster recovery")):
            return "Model HA/DR as ingress failover plus runtime recovery plus data protection, with RTO/RPO, test evidence, and return-to-primary procedures."
        if any(node.role == "data" for node in nodes):
            return "At minimum, validate data-tier backup/restore, service health checks, and observability before production."
        return "HA/DR topology is provisional until workload criticality, RTO/RPO, and deployment regions are confirmed."

    def _operational_notes(
        self,
        nodes: list[ArchitectureTopologyNode],
        profile: IntentProfile,
    ) -> list[str]:
        roles = {node.role for node in nodes}
        notes = [
            "Keep topology metadata review-oriented; it is not a rendered network diagram.",
            "Confirm compartment, IAM, Vault, Logging, Monitoring, and incident ownership before production.",
        ]
        if "observability" not in roles:
            notes.append("Add explicit OCI Logging and Monitoring coverage to complete operational readiness.")
        if "security" not in roles and "identity" not in roles:
            notes.append("Add explicit OCI IAM and Vault/security posture controls before enterprise review.")
        if profile.intent.value in {"migration", "modernization"}:
            notes.append("Tie topology rollout to migration waves, rollback criteria, and coexistence windows.")
        return notes

    def _mermaid(
        self,
        nodes: list[ArchitectureTopologyNode],
        relationships: list[ArchitectureTopologyRelationship],
    ) -> str | None:
        if not nodes:
            return None
        lines = ["flowchart LR"]
        for node in nodes[:10]:
            lines.append(f'  {node.node_id}["{self._escape(node.label)}"]')
        for relationship in relationships[:12]:
            lines.append(
                f"  {relationship.from_node} -->|{self._escape(relationship.relationship)}| {relationship.to_node}"
            )
        return "\n".join(lines)

    def _role(
        self,
        label: str,
        service_domain: str | None,
        service_category: str | None,
    ) -> str:
        normalized = " ".join(part for part in (label, service_domain or "", service_category or "")).lower()
        for term, role in SERVICE_ROLES:
            if term in normalized:
                return role
        if "network" in normalized:
            return "network"
        if "security" in normalized:
            return "security"
        return "supporting-service"

    def _node_id(self, label: str) -> str:
        normalized = re.sub(r"[^a-zA-Z0-9]+", "_", label).strip("_").lower() or "node"
        if normalized[0].isdigit():
            normalized = f"n_{normalized}"
        return normalized[:40]

    def _label(self, service: str) -> str:
        aliases = {
            "oke": "OCI Kubernetes Engine",
            "iam": "Identity and Access Management",
            "waf": "Web Application Firewall",
        }
        return aliases.get(service, service.title())

    def _escape(self, value: str) -> str:
        return value.replace('"', "'")

    def _source_ids(self, sources: list[RetrievedSource]) -> list[str]:
        return list(dict.fromkeys(source.chunk_id for source in sources if source.chunk_id))
