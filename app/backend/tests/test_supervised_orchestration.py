from oci_arch_studio_backend.models.architecture import RetrievedSource
from oci_arch_studio_backend.services.advisory_quality import AdvisoryQualityAnalyzer
from oci_arch_studio_backend.services.intents import Intent, get_intent_profile
from oci_arch_studio_backend.services.supervised_orchestration import (
    SupervisedAgentOrchestrator,
)
from oci_arch_studio_backend.services.synthesis import SynthesisResult


def test_supervisor_routes_migration_to_specialist_and_critic() -> None:
    profile = get_intent_profile(Intent.MIGRATION)
    source = RetrievedSource(
        chunk_id="oke::1",
        title="OCI Kubernetes Engine",
        source_type="oci_doc",
        source_url="https://example.com/oke",
        service="OKE",
        service_domain="containers",
        intent_tags=["migration"],
        freshness_score=0.9,
        trust_level="official",
        summary="OCI Kubernetes Engine supports managed Kubernetes clusters for container workloads.",
        relevance_score=0.4,
    )

    orchestrator = SupervisedAgentOrchestrator(mode="supervised")
    plan = orchestrator.plan(
        question="Migrate EKS to OCI.",
        profile=profile,
        sources=[source],
        context_note="Retrieved one source.",
    )

    assert plan.mode == "supervised"
    assert plan.active_agents == ["supervisor", "migration_advisor", "validation_critic"]
    assert "migration_advisor" in plan.routing_decision
    assert "Supervised routing" in plan.context_note


def test_critic_flags_low_evidence_findings() -> None:
    profile = get_intent_profile(Intent.COST)
    quality = AdvisoryQualityAnalyzer().assess(
        question="Make it cheap.",
        profile=profile,
        base_recommendations=["Clarify cost and performance requirements."],
        sources=[],
        release_store=None,
    )
    synthesis = SynthesisResult(
        answer="Test answer",
        recommendations=["Clarify cost and performance requirements."],
        assumptions=[],
        risks=[],
        next_steps=[],
        provider="deterministic",
        model="profile-v0",
    )

    critique = SupervisedAgentOrchestrator(mode="supervised").critique(
        synthesis=synthesis,
        quality=quality,
        sources=[],
    )

    assert any("provisional" in finding for finding in critique.findings)
    assert critique.traces[0].agent == "validation_critic"
    assert critique.warnings


def test_single_pass_mode_preserves_rollback_path() -> None:
    profile = get_intent_profile(Intent.ARCHITECTURE)
    plan = SupervisedAgentOrchestrator(mode="single_pass").plan(
        question="Design a web app on OCI.",
        profile=profile,
        sources=[],
        context_note="Retrieved context.",
    )

    assert plan.mode == "single_pass"
    assert plan.active_agents == []
    assert plan.context_note == "Retrieved context."


def test_multi_agent_pilot_selects_supporting_specialists() -> None:
    profile = get_intent_profile(Intent.MIGRATION)
    sources = [
        RetrievedSource(
            chunk_id="oke::1",
            title="OCI Kubernetes Engine",
            source_type="oci_doc",
            source_url="https://example.com/oke",
            service="OKE",
            service_domain="containers",
            intent_tags=["migration"],
            freshness_score=0.9,
            trust_level="official",
            summary="OCI Kubernetes Engine supports managed Kubernetes clusters.",
            relevance_score=0.4,
        ),
        RetrievedSource(
            chunk_id="cost::1",
            title="OCI Cost Management",
            source_type="oci_doc",
            source_url="https://example.com/cost",
            service="Cost Management",
            service_domain="cost",
            intent_tags=["cost"],
            freshness_score=0.9,
            trust_level="official",
            summary="OCI Budgets and usage monitoring support cost governance.",
            relevance_score=0.3,
        ),
    ]

    plan = SupervisedAgentOrchestrator(mode="multi_agent_pilot").plan(
        question="Migrate EKS to OCI and optimize cost.",
        profile=profile,
        sources=sources,
        context_note="Retrieved context.",
    )

    assert plan.mode == "multi_agent_pilot"
    assert "migration_advisor" in plan.active_agents
    assert "cost_advisor" in plan.active_agents
    assert "final_synthesizer" in plan.active_agents
    assert len(plan.contributions) >= 2
    assert plan.aggregation_decision
    assert "one final synthesis" in plan.routing_decision
