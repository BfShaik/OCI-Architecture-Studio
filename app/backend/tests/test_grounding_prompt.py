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
