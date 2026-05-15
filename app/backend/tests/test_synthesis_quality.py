from oci_arch_studio_backend.models.architecture import RetrievedSource
from oci_arch_studio_backend.services.synthesis_quality import SynthesisQualityScorer


def test_synthesis_quality_scores_grounded_specific_response() -> None:
    source = RetrievedSource(
        chunk_id="lb::1",
        title="OCI Load Balancer",
        source_type="oci_doc",
        source_url="https://example.com/lb",
        service="Load Balancer",
        service_domain="networking",
        workload_types=["webapp"],
        domain_tags=["ecommerce"],
        summary="Load Balancer supports public ingress.",
    )

    score = SynthesisQualityScorer().score(
        answer="Use OCI Load Balancer for ecommerce ingress and pair it with Object Storage and Monitoring.",
        recommendations=["Use Load Balancer, Monitoring, and Object Storage for the webapp."],
        sources=[source],
        question="Design an ecommerce webapp.",
    )

    assert score.grounding_quality > 0
    assert score.oci_specificity > 0
    assert score.workload_alignment > 0
    assert score.citation_coverage == 1.0


def test_synthesis_quality_scores_migration_mapping_accuracy() -> None:
    source = RetrievedSource(
        chunk_id="oke::1",
        title="OKE",
        source_type="oci_doc",
        source_url="https://example.com/oke",
        service="OCI Kubernetes Engine",
        service_domain="containers",
        migration_mappings={"EKS": "OKE"},
        summary="OKE supports Kubernetes migration.",
    )

    score = SynthesisQualityScorer().score(
        answer="Migrate EKS workloads to OKE with validation and rollback.",
        recommendations=["Map EKS to OKE before migration waves."],
        sources=[source],
        question="Migrate EKS to OCI.",
    )

    assert score.migration_accuracy == 1.0
