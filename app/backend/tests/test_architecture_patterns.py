from oci_arch_studio_backend.models.architecture import RetrievedSource
from oci_arch_studio_backend.services.architecture_patterns import ArchitecturePatternSelector
from oci_arch_studio_backend.services.intents import Intent, get_intent_profile


def test_pattern_selector_prefers_kubernetes_modernization() -> None:
    pattern = ArchitecturePatternSelector().select(
        question="Modernize EKS workloads to OKE.",
        workload_context=None,
        profile=get_intent_profile(Intent.MIGRATION),
        sources=[
            RetrievedSource(
                chunk_id="oke::1",
                title="OKE",
                source_type="oci_doc",
                service="OCI Kubernetes Engine",
                service_domain="containers",
                architecture_patterns=["container-platform"],
                workload_types=["migration"],
                summary="OKE supports Kubernetes platforms.",
            )
        ],
    )

    assert pattern.name == "kubernetes_modernization_platform"
    assert "OCI Kubernetes Engine" in pattern.service_priorities


def test_pattern_selector_prefers_saas_multi_region() -> None:
    pattern = ArchitecturePatternSelector().select(
        question="Design a multi-region SaaS platform with tenant isolation.",
        workload_context=None,
        profile=get_intent_profile(Intent.SAAS_PLATFORM),
        sources=[],
    )

    assert pattern.name == "saas_multi_region_platform"
    assert any("tenant isolation" in move.lower() for move in pattern.design_moves)
