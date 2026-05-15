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
    assert body["synthesis_quality"]["overall"] >= 0
    assert body["decision_reasoning"]
    assert "why_chosen" in body["decision_reasoning"][0]
    assert body["reasoning_trace"]["profile"]
    assert body["reasoning_trace"]["service_priorities"]
    assert body["architecture_tradeoffs"]
    assert body["recommendation_confidence"]
    assert body["recommendation_confidence"][0]["reasoning_basis"]
    assert body["consistency_findings"] is not None
    assert body["enterprise_governance"]["maturity_level"]
    assert body["enterprise_governance"]["executive_summary"]["business_impact"]
    assert body["enterprise_governance"]["auditability_trace"]["synthesis_provider"]
    assert body["architecture_topology"]["topology_summary"]
    assert body["architecture_topology"]["nodes"]
    assert body["architecture_topology"]["mermaid_flow"].startswith("flowchart")
    assert body["executive_experience"]["executive_summary"]
    assert body["executive_experience"]["decision_brief"]
    assert body["executive_experience"]["implementation_sequence"]
    assert body["executive_experience"]["architecture_visualization"]["topology_summary"]
    assert body["executive_experience"]["review_artifacts"][0]["markdown_summary"].startswith(
        "# OCI Architecture Review Summary"
    )
    assert body["release_context"] is not None
    assert body["knowledge_temporal_context"]["knowledge_mode"]
    assert body["recommendations"]
    assert body["citations"]
    assert body["section_citations"]
    assert body["section_citations"][0]["section"] == "Executive Summary"
    assert "summary" in body["citations"][0]
    assert body["evidence_links"]
    assert body["confidence"]["overall"] >= 0
    assert body["confidence"]["service_relevance"] >= 0
    assert body["confidence"]["citation_coverage"] >= 0
    assert body["quality_warnings"] is not None


def test_architecture_review_optional_retrieval_debug() -> None:
    response = client.post(
        "/architecture-review",
        json={
            "question": "Migrate CloudWatch and IAM controls for a SaaS platform to OCI.",
            "retrieval_debug": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["retrieval_debug"]["detected_intent"]
    assert "Logging" in body["retrieval_debug"]["mapped_oci_services"]
    assert body["retrieval_debug"]["retrieval_scores"]
    assert body["retrieval_debug"]["selected_final_chunks"]


def test_architecture_review_optional_synthesis_debug() -> None:
    response = client.post(
        "/architecture-review",
        json={
            "question": "Design a highly available web app on OCI.",
            "synthesis_debug": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["synthesis_debug"]["selected_provider"] == "deterministic"
    assert body["synthesis_debug"]["retrieved_chunk_ids"]
    assert body["synthesis_debug"]["grounding_prompt_sections"]


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
    assert "average_synthesis_latency_ms" in body
    assert body["last_orchestration_mode"] in {"multi_agent_pilot", "supervised", "single_pass"}


def test_operations_readiness_endpoint_reports_platform_maturity_checks() -> None:
    response = client.get("/operations/readiness")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "warning", "critical"}
    assert "api_gateway" in body["checks"]
    assert "oci_devops" in body["checks"]
    assert "runtime_safeguards" in body["checks"]
    assert body["notes"]


def test_retrieval_health() -> None:
    response = client.get("/retrieval/health")

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "local_json"
    assert body["embedding_model"].startswith("local-hashing-v1")
    assert body["store"]["exists"] is True
    assert "metrics" in body


def test_knowledge_refresh_status_endpoint() -> None:
    response = client.get("/knowledge/refresh/status")

    assert response.status_code == 200
    body = response.json()
    assert "status_path" in body
    assert "last_run" in body


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
