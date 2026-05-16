from oci_arch_studio_backend.models.architecture import RetrievedSource
from oci_arch_studio_backend.services.grounding_prompt import GroundingPromptBuilder
from oci_arch_studio_backend.services.intents import Intent, get_intent_profile


def test_grounding_prompt_includes_intent_mappings_patterns_and_chunks() -> None:
    prompt = GroundingPromptBuilder().build(
        question="Migrate EKS and CloudWatch to OCI for a SaaS platform.",
        workload_context="Multi-tenant platform with rollback requirements.",
        profile=get_intent_profile(Intent.MIGRATION),
        sources=[
            RetrievedSource(
                chunk_id="oke::1",
                title="OCI Kubernetes Engine",
                source_type="oci_doc",
                source_url="https://example.com/oke",
                service="OCI Kubernetes Engine",
                service_domain="containers",
                migration_mappings={"EKS": "OKE"},
                summary="OKE supports Kubernetes migration.",
            )
        ],
        context_note="Retrieved one OKE chunk.",
    )

    assert "Detected intent: migration" in prompt.user_prompt
    assert "EKS -> OCI Kubernetes Engine" in prompt.user_prompt
    assert "CloudWatch -> Logging, Monitoring" in prompt.user_prompt
    assert "Selected pattern:" in prompt.user_prompt
    assert "chunk_id: oke::1" in prompt.user_prompt
    assert "Return only JSON" in prompt.user_prompt
    assert "retrieved_oci_chunks" in prompt.sections


def test_grounding_prompt_requires_load_balancer_for_multi_region_saas() -> None:
    prompt = GroundingPromptBuilder().build(
        question="Design a multi-region SaaS platform with tenant isolation and failover readiness.",
        workload_context=None,
        profile=get_intent_profile(Intent.SAAS_PLATFORM),
        sources=[
            RetrievedSource(
                chunk_id="lb::1",
                title="OCI Load Balancer",
                source_type="oci_doc",
                source_url="https://example.com/lb",
                service="Load Balancer",
                service_domain="networking",
                summary="Load Balancer supports regional ingress and health checks.",
            )
        ],
        context_note="Retrieved Load Balancer context.",
    )

    assert "OCI Load Balancer or Load Balancing" in prompt.user_prompt
    assert "regional ingress, health-check, and traffic-failover layer" in prompt.user_prompt
