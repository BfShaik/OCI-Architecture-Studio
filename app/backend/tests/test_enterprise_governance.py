from oci_arch_studio_backend.models.architecture import (
    ArchitectureDecisionReason,
    ConfidenceScore,
    RetrievedSource,
)
from oci_arch_studio_backend.services.enterprise_governance import EnterpriseGovernanceAdvisor
from oci_arch_studio_backend.services.architecture_reasoning_engine import ArchitectureReasoningEngine
from oci_arch_studio_backend.services.intents import Intent, get_intent_profile


def _source() -> RetrievedSource:
    return RetrievedSource(
        chunk_id="oci-vault::security::1",
        title="OCI Vault and IAM",
        source_type="oci_doc",
        url="https://example.com/vault",
        source_url="https://example.com/vault",
        service="Vault",
        service_domain="security",
        service_category="security",
        domain_tags=["fintech"],
        workload_types=["regulated-workload"],
        architecture_patterns=["secure-enterprise-landing-zone"],
        summary="OCI Vault, IAM, Logging, and Audit support enterprise security controls.",
        relevance_score=0.88,
    )


def _confidence(level: str = "medium") -> ConfidenceScore:
    return ConfidenceScore(
        retrieval=0.8,
        evidence=0.75,
        freshness=0.9,
        release_awareness=1.0,
        recommendation=0.75,
        service_relevance=0.8,
        workload_alignment=0.82,
        migration_mapping=0.7,
        citation_coverage=0.85,
        overall=0.78 if level == "high" else 0.68,
        level=level,
        notes=[],
    )


def test_enterprise_governance_flags_regulated_security_and_audit_controls() -> None:
    profile = get_intent_profile(Intent.DR)
    sources = [_source()]
    recommendations = [
        "Use OCI IAM least privilege, Vault encryption, Logging, Audit, and tested RTO/RPO controls.",
        "Run DR failover tests and retain evidence for regulated fintech review.",
    ]
    reasoning_result = ArchitectureReasoningEngine().analyze(
        question="Design secure fintech DR on OCI.",
        workload_context=None,
        profile=profile,
        sources=sources,
        recommendations=recommendations,
        synthesis_provider="deterministic",
    )

    assessment = EnterpriseGovernanceAdvisor().assess(
        question="Design secure fintech DR on OCI.",
        workload_context=None,
        profile=profile,
        sources=sources,
        recommendations=recommendations,
        decision_reasoning=[
            ArchitectureDecisionReason(
                recommendation=recommendations[0],
                service="Vault",
                why_chosen="Protects keys and secrets for regulated workloads.",
                source_chunk_ids=["oci-vault::security::1"],
                confidence=0.82,
            )
        ],
        reasoning_result=reasoning_result,
        consistency_findings=[],
        release_context=None,
        temporal_context=None,
        confidence=_confidence(),
        synthesis_provider="deterministic",
        synthesis_fallback_used=False,
        quality_warnings=[],
        unsupported_claims=[],
    )

    assert assessment.governance_annotations
    assert assessment.security_posture_checks
    assert any(risk.category == "security" for risk in assessment.risk_classifications)
    assert any(item.priority == "recommended immediately" for item in assessment.recommendation_priorities)
    assert assessment.auditability_trace.retrieval_source_chunk_ids == ["oci-vault::security::1"]


def test_enterprise_governance_adds_migration_comparison_and_cutover_risk() -> None:
    profile = get_intent_profile(Intent.MIGRATION)
    sources = [
        RetrievedSource(
            chunk_id="oke::migration::1",
            title="OCI Kubernetes Engine migration",
            source_type="oci_doc",
            url="https://example.com/oke",
            service="OKE",
            service_domain="compute",
            architecture_patterns=["kubernetes-modernization"],
            summary="OKE supports Kubernetes modernization and migration waves.",
        )
    ]
    recommendations = ["Migrate EKS workloads to OKE using migration waves, cutover rehearsal, and rollback gates."]
    reasoning_result = ArchitectureReasoningEngine().analyze(
        question="Migrate EKS to OCI.",
        workload_context=None,
        profile=profile,
        sources=sources,
        recommendations=recommendations,
        synthesis_provider="deterministic",
    )

    assessment = EnterpriseGovernanceAdvisor().assess(
        question="Migrate EKS to OCI.",
        workload_context=None,
        profile=profile,
        sources=sources,
        recommendations=recommendations,
        decision_reasoning=[],
        reasoning_result=reasoning_result,
        consistency_findings=[],
        release_context=None,
        temporal_context=None,
        confidence=_confidence("high"),
        synthesis_provider="deterministic",
        synthesis_fallback_used=False,
        quality_warnings=[],
        unsupported_claims=[],
    )

    assert any(risk.category == "migration" for risk in assessment.risk_classifications)
    assert any("OKE vs Compute" in comparison.decision for comparison in assessment.architecture_comparisons)
    assert assessment.auditability_trace.reasoning_profile == "migration_architecture"
