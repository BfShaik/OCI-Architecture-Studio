import pytest
from fastapi.testclient import TestClient

from oci_arch_studio_backend.main import app


client = TestClient(app)


@pytest.mark.parametrize(
    ("prompt", "intent", "expected_terms"),
    [
        (
            "What does OCI Architecture Studio do?",
            "product_overview",
            ("architecture guidance", "migration advisory", "release-aware"),
        ),
        (
            "design a highly available ecommerce platform on OCI",
            "architecture",
            ("ecommerce", "storefront", "checkout"),
        ),
        (
            "migrate EKS + RDS to OCI",
            "migration",
            ("EKS", "RDS", "OCI database"),
        ),
        (
            "recommend OCI services for fintech DR",
            "dr",
            ("RTO/RPO", "failover", "audit"),
        ),
        (
            "build a cost-optimized web app on OCI",
            "cost",
            ("right-sized", "budgets", "usage"),
        ),
        (
            "How does the latest OCI update affect this architecture?",
            "release_awareness",
            ("release note", "local RAG index", "Refresh"),
        ),
    ],
)
def test_architecture_review_is_intent_aware(
    prompt: str,
    intent: str,
    expected_terms: tuple[str, ...],
) -> None:
    response = client.post("/architecture-review", json={"question": prompt})

    assert response.status_code == 200
    body = response.json()
    joined_recommendations = " ".join(body["recommendations"])

    assert body["intent"] == intent
    assert intent.replace("_", "-") in body["prompt_template"]
    assert body["citations"]
    for term in expected_terms:
        assert term.lower() in joined_recommendations.lower()
