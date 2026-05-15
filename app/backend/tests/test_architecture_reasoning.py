from oci_arch_studio_backend.models.architecture import EvidenceLink, RetrievedSource
from oci_arch_studio_backend.services.architecture_reasoning import ArchitectureDecisionReasoner
from oci_arch_studio_backend.services.intents import Intent, get_intent_profile


def test_decision_reasoning_links_recommendation_to_sources() -> None:
    source = RetrievedSource(
        chunk_id="oke::1",
        title="OCI Kubernetes Engine",
        source_type="oci_doc",
        source_url="https://example.com/oke",
        service="OCI Kubernetes Engine",
        service_domain="containers",
        workload_types=["migration"],
        domain_tags=["SaaS"],
        summary="OKE supports Kubernetes migration.",
    )

    reasons = ArchitectureDecisionReasoner().build(
        question="Migrate EKS to OCI for a SaaS platform.",
        workload_context=None,
        profile=get_intent_profile(Intent.MIGRATION),
        recommendations=["Use OCI Kubernetes Engine for the Kubernetes migration."],
        evidence_links=[
            EvidenceLink(
                recommendation_index=0,
                support_level="strong",
                source_chunk_ids=["oke::1"],
                source_titles=["OCI Kubernetes Engine"],
                rationale="Supported by OKE evidence.",
            )
        ],
        sources=[source],
    )

    assert reasons[0].service == "OCI Kubernetes Engine"
    assert reasons[0].source_chunk_ids == ["oke::1"]
    assert reasons[0].confidence >= 0.9
    assert reasons[0].tradeoffs
