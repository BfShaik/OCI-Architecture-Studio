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
        ("secure private application on OCI", Intent.SECURITY),
        ("How does the latest OCI update affect this architecture?", Intent.RELEASE_AWARENESS),
    ],
)
def test_intent_classifier(prompt: str, expected: Intent) -> None:
    assert IntentClassifier().classify(prompt) == expected
