from oci_arch_studio_backend.models.architecture import RetrievedSource
from oci_arch_studio_backend.services.intents import IntentClassifier, get_intent_profile
from oci_arch_studio_backend.services.optimization_advisor import OptimizationAdvisor


def test_optimization_advisor_builds_migration_finops_and_workload_plan() -> None:
    question = "Migrate EKS and RDS to OCI for a SaaS platform and optimize cost with rollback."
    profile = get_intent_profile(IntentClassifier().classify(question))
    sources = [
        RetrievedSource(
            chunk_id="oci-kubernetes-engine-overview::1",
            title="OCI Kubernetes Engine Overview",
            source_type="oci_doc",
            source_url="https://example.com/oke",
            service="OCI Kubernetes Engine",
            service_domain="containers",
            summary="OKE supports managed Kubernetes modernization and autoscaling.",
            relevance_score=0.8,
        ),
        RetrievedSource(
            chunk_id="oci-cost-management-overview::1",
            title="OCI Cost Management Overview",
            source_type="oci_doc",
            source_url="https://example.com/cost",
            service="Cost Management",
            service_domain="cost",
            summary="OCI Cost Analysis and Budgets support cost governance, rightsizing, and monitoring.",
            relevance_score=0.7,
        ),
    ]

    plan = OptimizationAdvisor().build(
        question=question,
        workload_context="multi-tenant SaaS, production migration",
        profile=profile,
        sources=sources,
        base_recommendations=["Map EKS to OKE and RDS to OCI database services."],
    )

    assert plan.migration_phases
    assert plan.modernization_options
    assert plan.finops_recommendations
    assert plan.workload_optimization_signals
    assert plan.optimization_comparisons
    assert any("phased migration" in item.lower() for item in plan.recommendation_additions)
