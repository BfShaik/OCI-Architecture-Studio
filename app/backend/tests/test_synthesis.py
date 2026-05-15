import pytest

from oci_arch_studio_backend.services.intents import Intent, get_intent_profile
from oci_arch_studio_backend.models.architecture import RetrievedSource
from oci_arch_studio_backend.services.synthesis import (
    DeterministicAdvisorySynthesizer,
    OciGenAiAdvisorySynthesizer,
    OciGenAiSynthesisConfig,
    SynthesisRequest,
    build_synthesizer,
)


def test_deterministic_synthesizer_preserves_profile_contract() -> None:
    profile = get_intent_profile(Intent.ARCHITECTURE)
    synthesizer = DeterministicAdvisorySynthesizer()

    result = synthesizer.synthesize(
        SynthesisRequest(
            question="Design a highly available web app on OCI.",
            workload_context=None,
            profile=profile,
            sources=[],
            context_note="Retrieved test context.",
        )
    )

    assert result.provider == "deterministic"
    assert result.model == "profile-v0"
    assert result.latency_ms == 0.0
    assert result.recommendations == list(profile.recommendations)
    assert result.quality is not None
    assert "Retrieved test context" in result.answer
    assert "1. Executive Summary" in result.answer
    assert "10. Recommended Next Steps" in result.answer


def test_oci_genai_synthesizer_fails_closed_to_deterministic() -> None:
    profile = get_intent_profile(Intent.COST)

    class FailingGenAiSynthesizer(OciGenAiAdvisorySynthesizer):
        def _invoke_model(self, request: SynthesisRequest) -> str:
            raise RuntimeError("simulated model outage")

    synthesizer = FailingGenAiSynthesizer(
        OciGenAiSynthesisConfig(
            region="us-ashburn-1",
            profile="DEFAULT",
            auth_mode="config_file",
            compartment_id="ocid1.compartment.oc1..example",
            model_id="cohere.command-r-plus",
        )
    )

    result = synthesizer.synthesize(
        SynthesisRequest(
            question="Build a cost-optimized web app on OCI.",
            workload_context=None,
            profile=profile,
            sources=[],
            context_note="No network call should be required for fallback test.",
            debug_enabled=True,
        )
    )

    assert result.provider == "deterministic"
    assert result.used_fallback is True
    assert result.latency_ms is not None
    assert result.debug is not None
    assert result.debug.fallback_used is True
    assert result.debug.fallback_reason is not None
    assert any("fallback" in warning.lower() for warning in result.warnings)


def test_oci_genai_synthesizer_uses_grounded_json_response() -> None:
    profile = get_intent_profile(Intent.ARCHITECTURE)

    class SuccessfulGenAiSynthesizer(OciGenAiAdvisorySynthesizer):
        def _invoke_model(self, request: SynthesisRequest) -> str:
            self._last_grounding_prompt = self.prompt_builder.build(
                question=request.question,
                workload_context=request.workload_context,
                profile=request.profile,
                sources=request.sources,
                context_note=request.context_note,
            )
            self._last_token_usage = {"input_tokens": 120, "output_tokens": 80, "total_tokens": 200}
            return """
            {
              "answer": "1. Executive Summary\\nUse retrieved OCI evidence.\\n\\n2. Recommended OCI Services\\nUse Load Balancer.\\n\\n3. Reference Architecture\\nPrivate app tier.\\n\\n4. HA/DR Design\\nUse backups.\\n\\n5. Security Considerations\\nUse IAM.\\n\\n6. Cost Optimization\\nRight-size.\\n\\n7. Risks & Assumptions\\nValidate SLOs.\\n\\n8. Migration Strategy\\nNo migration assumed.\\n\\n9. Observability\\nUse Monitoring.\\n\\n10. Recommended Next Steps\\nValidate.",
              "recommendations": ["Use OCI Load Balancer based on lb::1."],
              "assumptions": ["Traffic profile is unknown."],
              "risks": ["Evidence is limited."],
              "next_steps": ["Validate HA requirements."],
              "quality_warnings": []
            }
            """

    synthesizer = SuccessfulGenAiSynthesizer(
        OciGenAiSynthesisConfig(
            region="us-ashburn-1",
            profile="DEFAULT",
            auth_mode="config_file",
            compartment_id="ocid1.compartment.oc1..example",
            model_id="cohere.command-r-plus",
        )
    )

    result = synthesizer.synthesize(
        SynthesisRequest(
            question="Design a highly available web app on OCI.",
            workload_context=None,
            profile=profile,
            sources=[
                RetrievedSource(
                    chunk_id="lb::1",
                    title="OCI Load Balancer",
                    source_type="oci_doc",
                    source_url="https://example.com/lb",
                    service="Load Balancer",
                    service_domain="networking",
                    summary="Load Balancer supports ingress.",
                )
            ],
            context_note="Retrieved Load Balancer context.",
            debug_enabled=True,
        )
    )

    assert result.provider == "oci_genai"
    assert result.used_fallback is False
    assert result.recommendations == ["Use OCI Load Balancer based on lb::1."]
    assert result.debug is not None
    assert "retrieved_oci_chunks" in result.debug.grounding_prompt_sections
    assert result.debug.token_usage["total_tokens"] == 200


def test_deterministic_synthesizer_adds_domain_heuristics() -> None:
    profile = get_intent_profile(Intent.ARCHITECTURE)
    result = DeterministicAdvisorySynthesizer().synthesize(
        SynthesisRequest(
            question="Design an ecommerce platform on OCI.",
            workload_context=None,
            profile=profile,
            sources=[],
            context_note="Retrieved ecommerce context.",
        )
    )

    assert any("For ecommerce" in recommendation for recommendation in result.recommendations)
    assert "checkout consistency" in result.answer


def test_deterministic_synthesizer_uses_retrieved_services_and_pattern_moves() -> None:
    profile = get_intent_profile(Intent.DR)
    result = DeterministicAdvisorySynthesizer().synthesize(
        SynthesisRequest(
            question="Design secure fintech DR on OCI.",
            workload_context=None,
            profile=profile,
            sources=[
                RetrievedSource(
                    chunk_id="dr::1",
                    title="Full Stack DR",
                    source_type="oci_doc",
                    source_url="https://example.com/dr",
                    service="Full Stack Disaster Recovery",
                    service_domain="resilience",
                    architecture_patterns=["disaster-recovery"],
                    domain_tags=["fintech"],
                    summary="Full Stack Disaster Recovery coordinates failover runbooks.",
                ),
                RetrievedSource(
                    chunk_id="vault::1",
                    title="Vault",
                    source_type="oci_doc",
                    source_url="https://example.com/vault",
                    service="Vault",
                    service_domain="security",
                    summary="Vault manages keys and secrets.",
                ),
            ],
            context_note="Retrieved DR and Vault context.",
        )
    )

    assert "fintech_disaster_recovery_platform" in result.answer
    assert "Full Stack Disaster Recovery" in result.answer
    assert "Vault-backed key and secret controls" in result.answer
    assert result.quality is not None


def test_build_synthesizer_requires_genai_settings() -> None:
    with pytest.raises(ValueError, match="OCI_GENAI_COMPARTMENT_ID"):
        build_synthesizer(
            provider="oci_genai",
            region="us-ashburn-1",
            profile="DEFAULT",
            auth_mode="config_file",
            compartment_id=None,
            model_id=None,
            endpoint=None,
            max_tokens=1200,
            temperature=0.1,
        )
