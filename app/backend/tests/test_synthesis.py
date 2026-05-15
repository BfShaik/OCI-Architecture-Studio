import pytest

from oci_arch_studio_backend.services.intents import Intent, get_intent_profile
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
    assert "Retrieved test context" in result.answer


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
        )
    )

    assert result.provider == "deterministic"
    assert result.used_fallback is True
    assert result.latency_ms is not None
    assert any("fallback" in warning.lower() for warning in result.warnings)


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
