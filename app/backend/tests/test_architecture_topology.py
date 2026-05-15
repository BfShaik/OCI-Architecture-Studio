from oci_arch_studio_backend.models.architecture import RetrievedSource
from oci_arch_studio_backend.services.architecture_topology import ArchitectureTopologyBuilder
from oci_arch_studio_backend.services.intents import Intent, get_intent_profile


def test_architecture_topology_builds_service_nodes_and_relationships() -> None:
    topology = ArchitectureTopologyBuilder().build(
        question="Design a multi-region SaaS platform on OCI.",
        workload_context="Needs tenant isolation, failover, and observability.",
        profile=get_intent_profile(Intent.SAAS_PLATFORM),
        sources=[
            RetrievedSource(
                chunk_id="lb::1",
                title="OCI Load Balancer",
                source_type="oci_doc",
                url="https://example.com/lb",
                service="Load Balancer",
                service_domain="networking",
                summary="Load Balancer provides ingress.",
            ),
            RetrievedSource(
                chunk_id="oke::1",
                title="OCI Kubernetes Engine",
                source_type="oci_doc",
                url="https://example.com/oke",
                service="OCI Kubernetes Engine",
                service_domain="containers",
                summary="OKE runs containerized applications.",
            ),
            RetrievedSource(
                chunk_id="db::1",
                title="Database Services",
                source_type="oci_doc",
                url="https://example.com/db",
                service="Database Services",
                service_domain="database",
                summary="Database services support data tiers.",
            ),
        ],
        recommendations=["Use Load Balancer, OKE, Database Services, Logging, and Monitoring."],
    )

    roles = {node.role for node in topology.nodes}
    assert "ingress" in roles
    assert "application-runtime" in roles
    assert "data" in roles
    assert topology.service_dependencies
    assert topology.mermaid_flow is not None
    assert "flowchart LR" in topology.mermaid_flow
    assert "multi-region" in topology.ha_dr_topology.lower() or "rto/rpo" in topology.ha_dr_topology.lower()
