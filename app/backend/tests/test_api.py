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
    assert body["recommendations"]
    assert body["citations"]
    assert "summary" in body["citations"][0]


def test_retrieval_health() -> None:
    response = client.get("/retrieval/health")

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "local_json"
    assert body["embedding_model"].startswith("local-hashing-v1")
    assert body["store"]["exists"] is True
    assert "metrics" in body
