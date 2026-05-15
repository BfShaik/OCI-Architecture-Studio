from oci_arch_studio_backend.models.architecture import RetrievedSource
from oci_arch_studio_backend.services.advisory_quality import AdvisoryQualityAnalyzer
from oci_arch_studio_backend.services.intents import Intent, get_intent_profile


def test_advisory_quality_links_recommendations_to_evidence() -> None:
    analyzer = AdvisoryQualityAnalyzer()
    profile = get_intent_profile(Intent.ARCHITECTURE)
    source = RetrievedSource(
        chunk_id="lb::1",
        title="OCI Load Balancer",
        source_type="oci_doc",
        source_url="https://example.com/load-balancer",
        service="Load Balancer",
        service_domain="networking",
        intent_tags=["architecture"],
        architecture_patterns=["public-ingress"],
        freshness_score=0.9,
        trust_level="official",
        summary="OCI Load Balancer supports public ingress, backend health checks, and highly available web entry points.",
        relevance_score=0.42,
    )

    result = analyzer.assess(
        question="Design a highly available web app on OCI.",
        profile=profile,
        base_recommendations=["Use OCI Load Balancer for public ingress."],
        sources=[source],
        release_store=None,
    )

    assert result.evidence_links[0].support_level in {"strong", "partial"}
    assert result.evidence_links[0].source_chunk_ids == ["lb::1"]
    assert "Evidence:" in result.recommendations[0]
    assert result.confidence.overall > 0.6


def test_advisory_quality_flags_unsupported_requested_services() -> None:
    analyzer = AdvisoryQualityAnalyzer()
    profile = get_intent_profile(Intent.ARCHITECTURE)

    result = analyzer.assess(
        question="Use OCI AutoPilot Architect for this design.",
        profile=profile,
        base_recommendations=["Clarify the required architecture controls."],
        sources=[],
        release_store=None,
    )

    assert result.unsupported_claims
    assert result.not_enough_evidence is True
    assert result.low_confidence is True
    assert result.confidence.level == "low"
