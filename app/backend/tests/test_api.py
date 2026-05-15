from fastapi.testclient import TestClient

from oci_arch_studio_backend.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_architecture_review() -> None:
    response = client.post(
        "/architecture-review",
        json={"question": "How should I host a highly available web app on OCI?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"]
    assert body["synthesis_provider"]
    assert body["orchestration_mode"] in {"multi_agent_pilot", "supervised", "single_pass"}
    assert body["routing_decision"]
    assert "validation_critic" in body["active_agents"]
    assert body["agent_contributions"]
    assert body["aggregation_decision"]
    assert body["critic_findings"]
    assert body["synthesis_warnings"] is not None
    assert body["recommendations"]
    assert body["citations"]
    assert "summary" in body["citations"][0]
    assert body["evidence_links"]
    assert body["confidence"]["overall"] >= 0
    assert body["quality_warnings"] is not None


def test_architecture_review_flags_low_context_uncertainty() -> None:
    response = client.post(
        "/architecture-review",
        json={"question": "Make it enterprise grade on OCI."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["not_enough_evidence"] is True
    assert body["low_confidence"] is True
    assert body["confidence"]["level"] == "low"
    assert any("Not enough context" in warning for warning in body["quality_warnings"])


def test_advisory_quality_metrics_endpoint() -> None:
    client.post(
        "/architecture-review",
        json={"question": "Design a highly available ecommerce platform on OCI."},
    )

    response = client.get("/advisory/quality")

    assert response.status_code == 200
    body = response.json()
    assert body["request_count"] >= 1
    assert "average_citation_coverage" in body
    assert body["last_orchestration_mode"] in {"multi_agent_pilot", "supervised", "single_pass"}


def test_retrieval_health() -> None:
    response = client.get("/retrieval/health")

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "local_json"
    assert body["embedding_model"].startswith("local-hashing-v1")
    assert body["store"]["exists"] is True
    assert "metrics" in body


def test_orchestration_health() -> None:
    client.post(
        "/architecture-review",
        json={"question": "Migrate EKS + RDS to OCI."},
    )

    response = client.get("/orchestration/health")

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "multi_agent_pilot"
    assert "supervisor" in body["active_agents"]
    assert body["last_agent_count"] >= 3
    assert body["request_count"] >= 1
