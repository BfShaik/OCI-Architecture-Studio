from oci_arch_studio_backend.models.architecture import RetrievedSource
from oci_arch_studio_backend.services.architecture_reasoning_engine import ArchitectureReasoningEngine
from oci_arch_studio_backend.services.intents import Intent, get_intent_profile


def test_reasoning_engine_selects_fintech_dr_profile() -> None:
    engine = ArchitectureReasoningEngine()

    result = engine.analyze(
        question="Design secure fintech DR with RTO/RPO, audit, and key controls.",
        workload_context=None,
        profile=get_intent_profile(Intent.DR),
        sources=[
            RetrievedSource(
                chunk_id="vault::1",
                title="OCI Vault",
                source_type="oci_doc",
                source_url="https://example.com/vault",
                service="Vault",
                service_domain="security",
                domain_tags=["fintech"],
                architecture_patterns=["key-management"],
                summary="Vault supports key management.",
            )
        ],
        recommendations=["Use Vault and database recovery controls for fintech DR."],
        synthesis_provider="deterministic",
    )

    assert result.profile.name == "fintech_workload"
    assert "Vault" in result.service_priorities
    assert "compliance evidence" in result.risk_emphasis
    assert any(tradeoff.dimension == "cost_vs_resilience" for tradeoff in result.tradeoffs)
    assert result.recommendation_confidence[0].score >= 0.7


def test_reasoning_engine_pre_retrieval_terms_bias_migration() -> None:
    terms = ArchitectureReasoningEngine().pre_retrieval_terms(
        question="Migrate EKS and RDS to OCI.",
        workload_context=None,
        profile=get_intent_profile(Intent.MIGRATION),
    )

    assert "migration waves" in terms
    assert "OKE" in terms
    assert "rollback" in terms
