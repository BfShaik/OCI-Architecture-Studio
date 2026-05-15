from fastapi.testclient import TestClient

from oci_arch_studio_backend.core.config import Settings
from oci_arch_studio_backend.main import app
from oci_arch_studio_backend.services.operational import OperationalDiagnostics
from oci_arch_studio_backend.services.retrieval import build_retriever


client = TestClient(app)


def test_operations_profile_endpoint_reports_local_profile() -> None:
    response = client.get("/operations/profile")

    assert response.status_code == 200
    body = response.json()
    assert body["profile"] == "local_dev"
    assert body["capabilities"]["runtime"] == "local"


def test_operations_health_endpoint_summarizes_runtime_checks() -> None:
    response = client.get("/operations/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "warning"}
    assert body["deployment"]["profile"] == "local_dev"
    assert body["checks"]["retrieval_provider"]["provider"] == "local_json"
    assert body["runtime_readiness"]["checks"]["fallback_paths"]["deterministic_synthesis"] == "available"
    assert "operational_metrics" in body
    assert "retrieval_metrics" in body


def test_operations_analytics_records_architecture_review_usage() -> None:
    client.post(
        "/architecture-review",
        json={"question": "Design a secure OCI landing zone with monitoring."},
    )

    response = client.get("/operations/analytics")

    assert response.status_code == 200
    body = response.json()
    metrics = body["observability"]["metrics"]
    assert metrics["request_count"] >= 1
    assert metrics["synthesis_provider_usage"]
    assert metrics["workload_usage"]
    assert "audit" in body["observability"]
    assert "governance_policy_triggers" in metrics
    assert "governance_risk_trends" in metrics
    assert "runtime_degradation_events" in metrics


def test_oci_vm_profile_warns_when_using_config_file_auth() -> None:
    settings = Settings(DEPLOYMENT_PROFILE="oci_vm", OCI_AUTH_MODE="config_file", OCI_REGION="us-ashburn-1")

    profile = OperationalDiagnostics(settings).deployment_profile()

    assert profile["profile"] == "oci_vm"
    assert any("instance_principal" in warning for warning in profile["warnings"])


def test_secret_status_prefers_vault_when_secret_ocid_is_configured() -> None:
    settings = Settings(
        OCI_VAULT_CONFIG_SECRET_OCID="ocid1.vaultsecret.oc1..example",
        OCI_CONNECTIVITY_CHECK_ENABLED=False,
    )

    status = OperationalDiagnostics(settings).secrets_status()

    assert status["provider"] == "oci_vault"
    assert status["validation"] == "configured_not_checked"


def test_runtime_readiness_reports_api_gateway_and_devops_configuration() -> None:
    settings = Settings(
        OCI_API_GATEWAY_ENDPOINT="https://example.apigateway.us-ashburn-1.oci.customer-oci.com",
        OCI_API_GATEWAY_OCID="ocid1.apigateway.oc1..example",
        OCI_DEVOPS_PROJECT_OCID="ocid1.devopsproject.oc1..example",
        OCI_DEVOPS_DEPLOY_PIPELINE_OCID="ocid1.devopsdeploypipeline.oc1..example",
    )

    readiness = OperationalDiagnostics(settings).runtime_readiness(
        retrieval={"provider": "local_json", "store": {"exists": True, "chunk_count": 44}},
        refresh_status={"status": "succeeded"},
    )

    assert readiness["checks"]["api_gateway"]["status"] == "ok"
    assert readiness["checks"]["oci_devops"]["status"] == "ok"
    assert readiness["checks"]["runtime_safeguards"]["deterministic_synthesis_available"] is True


def test_object_storage_retrieval_degrades_to_local_fallback_when_config_missing() -> None:
    settings = Settings(RETRIEVAL_PROVIDER="oci_object_storage", RETRIEVAL_FALLBACK_ENABLED=True)

    diagnostics = build_retriever(settings).diagnostics()

    assert diagnostics["provider"] == "oci_object_storage"
    assert diagnostics["store"]["fallback_enabled"] is True
    assert diagnostics["store"]["fallback_active"] is True
    assert diagnostics["store"]["fallback"]["exists"] is True
