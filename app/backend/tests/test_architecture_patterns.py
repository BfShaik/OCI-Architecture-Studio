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


def test_pattern_selector_treats_isv_hosting_as_saas_platform() -> None:
    pattern = ArchitecturePatternSelector().select(
        question="Design an ISV solution in OCI for hosting their software with networking and compartment topology.",
        workload_context=None,
        profile=get_intent_profile(Intent.SAAS_PLATFORM),
        sources=[],
    )

    assert pattern.name == "saas_multi_region_platform"
    assert "Identity and Access Management" in pattern.service_priorities
    assert "Virtual Cloud Network" in pattern.service_priorities


def test_pattern_selector_supports_secure_landing_zone() -> None:
    pattern = ArchitecturePatternSelector().select(
        question="Design a secure enterprise landing zone with compartments and guardrails.",
        workload_context=None,
        profile=get_intent_profile(Intent.SECURITY),
        sources=[],
    )

    assert pattern.name == "secure_enterprise_landing_zone"
    assert "Identity and Access Management" in pattern.service_priorities


def test_pattern_selector_supports_event_driven_systems() -> None:
    pattern = ArchitecturePatternSelector().select(
        question="Design an event-driven workload with streaming and asynchronous handlers.",
        workload_context=None,
        profile=get_intent_profile(Intent.ARCHITECTURE),
        sources=[],
    )

    assert pattern.name == "event_driven_system"
    assert "Streaming" in pattern.service_priorities
