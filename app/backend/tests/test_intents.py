import pytest

from oci_arch_studio_backend.services.intents import Intent, IntentClassifier


@pytest.mark.parametrize(
    ("prompt", "expected"),
    [
        ("What does OCI Architecture Studio do?", Intent.PRODUCT_OVERVIEW),
        ("highly available ecommerce platform on OCI", Intent.ARCHITECTURE),
        ("migrate EKS + RDS to OCI", Intent.MIGRATION),
        ("fintech DR design", Intent.DR),
        ("cost-optimized web app on OCI", Intent.COST),
        ("centralized logging monitoring alarms and dashboards on OCI", Intent.OBSERVABILITY),
        ("private AI inference platform with model artifacts", Intent.AI_ML),
        ("secure private application on OCI", Intent.SECURITY),
        ("modernize a legacy web app onto managed OCI services", Intent.MODERNIZATION),
        ("multi-region SaaS platform with tenant isolation", Intent.SAAS_PLATFORM),
        ("analytics data platform on OCI", Intent.ANALYTICS),
        ("How does the latest OCI update affect this architecture?", Intent.RELEASE_AWARENESS),
    ],
)
def test_intent_classifier(prompt: str, expected: Intent) -> None:
    assert IntentClassifier().classify(prompt) == expected
