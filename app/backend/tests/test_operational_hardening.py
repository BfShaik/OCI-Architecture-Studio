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


def test_operations_infrastructure_endpoint_reports_runtime_visibility() -> None:
    response = client.get("/operations/infrastructure")

    assert response.status_code == 200
    body = response.json()
    assert body["environment"]["deployment_profile"] == "local_dev"
    assert body["topology"]["api_exposure"] == "direct_backend_vm"
    assert body["providers"]["retrieval"]["active_provider"] == "local_json"
    assert body["rebuildability"]["status"] in {"ok", "warning"}
    assert body["configured_resources"]["observability"]["monitoring_namespace"] == "oci_architecture_studio"
    assert any(gap["area"] == "api_exposure" for gap in body["gaps"])


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
    assert metrics["executive_summary_count"] >= 1
    assert metrics["visualization_generation_count"] >= 1
    assert metrics["review_artifact_count"] >= 1
    assert "finops_recommendation_frequency" in metrics
    assert "migration_recommendation_trends" in metrics
    assert "workload_optimization_patterns" in metrics


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
    assert readiness["checks"]["api_gateway"]["promotion_ready"] is True
    assert readiness["checks"]["api_gateway"]["active"] is True
    assert readiness["checks"]["oci_devops"]["status"] == "ok"
    assert readiness["checks"]["oci_devops"]["promotion_ready"] is True
    assert readiness["checks"]["oci_devops"]["active_deployment_path"] == "oci_devops"
    assert readiness["checks"]["runtime_safeguards"]["deterministic_synthesis_available"] is True


def test_oci_devops_partial_configuration_keeps_operator_scripts_active() -> None:
    settings = Settings(OCI_DEVOPS_PROJECT_OCID="ocid1.devopsproject.oc1..example")

    readiness = OperationalDiagnostics(settings).runtime_readiness(
        retrieval={"provider": "local_json", "store": {"exists": True, "chunk_count": 44}},
        refresh_status={"status": "succeeded"},
    )

    devops = readiness["checks"]["oci_devops"]
    assert devops["status"] == "warning"
    assert devops["configured"] is True
    assert devops["promotion_ready"] is False
    assert devops["missing_config"] == ["OCI_DEVOPS_DEPLOY_PIPELINE_OCID"]
    assert devops["active_deployment_path"] == "operator_scripts"


def test_api_gateway_partial_configuration_keeps_direct_backend_exposure() -> None:
    settings = Settings(
        DEPLOYMENT_PROFILE="oci_vm",
        OCI_API_GATEWAY_OCID="ocid1.apigateway.oc1..example",
    )

    diagnostics = OperationalDiagnostics(settings)
    readiness = diagnostics.runtime_readiness(
        retrieval={"provider": "local_json", "store": {"exists": True, "chunk_count": 44}},
        refresh_status={"status": "succeeded"},
    )
    visibility = diagnostics.infrastructure_visibility(
        retrieval={"provider": "local_json", "store": {"exists": True, "chunk_count": 44}},
        refresh_status={"status": "succeeded"},
    )

    api_gateway = readiness["checks"]["api_gateway"]
    assert api_gateway["status"] == "warning"
    assert api_gateway["configured"] is True
    assert api_gateway["active"] is False
    assert api_gateway["promotion_ready"] is False
    assert api_gateway["missing_config"] == ["OCI_API_GATEWAY_ENDPOINT"]
    assert visibility["topology"]["api_exposure"] == "direct_backend_vm"
    assert visibility["configured_resources"]["networking"]["api_gateway_promotion_ready"] is False


def test_infrastructure_visibility_distinguishes_configured_and_scaffolded_oci_resources() -> None:
    settings = Settings(
        DEPLOYMENT_PROFILE="oci_vm",
        OCI_AUTH_MODE="instance_principal",
        OCI_REGION="us-ashburn-1",
        OCI_COMPARTMENT_ID="ocid1.compartment.oc1..example",
        OCI_VAULT_CONFIG_SECRET_OCID="ocid1.vaultsecret.oc1..example",
        OCI_LOGGING_LOG_GROUP_OCID="ocid1.loggroup.oc1..example",
        OCI_NOTIFICATIONS_TOPIC_OCID="ocid1.onstopic.oc1..example",
        OCI_EVENTS_RULE_OCID="ocid1.eventrule.oc1..example",
        OCI_OBJECT_STORAGE_NAMESPACE="example_namespace",
        OCI_VECTOR_BUCKET="oci-architecture-studio-staging-knowledge-snapshots",
        OCI_API_GATEWAY_ENDPOINT="https://example.apigateway.us-ashburn-1.oci.customer-oci.com",
        OCI_DEVOPS_PROJECT_OCID="ocid1.devopsproject.oc1..example",
        OCI_DEVOPS_DEPLOY_PIPELINE_OCID="ocid1.devopsdeploypipeline.oc1..example",
    )

    visibility = OperationalDiagnostics(settings).infrastructure_visibility(
        retrieval={"provider": "oci_object_storage", "store": {"exists": True, "chunk_count": 44}},
        refresh_status={"status": "succeeded"},
    )

    assert visibility["topology"]["api_exposure"] == "oci_api_gateway"
    assert visibility["topology"]["runtime_compute"] == "oci_compute_vm"
    assert visibility["configured_resources"]["storage"]["knowledge_bucket_configured"] is True
    assert visibility["operational_workflows"]["deployment"]["provider"] == "oci_devops"
    assert visibility["configured_resources"]["runtime"]["oci_devops_promotion_ready"] is True
    assert visibility["providers"]["embeddings"]["configured_provider"] == "local"
    assert visibility["providers"]["embeddings"]["activation_ready"] is False
    assert not any(gap["area"] == "identity" for gap in visibility["gaps"])


def test_embedding_visibility_reports_genai_activation_readiness() -> None:
    settings = Settings(
        EMBEDDING_PROVIDER="oci_genai",
        OCI_GENAI_COMPARTMENT_ID="ocid1.compartment.oc1..example",
        OCI_GENAI_EMBEDDING_MODEL_ID="cohere.embed-english-v3.0",
        OCI_GENAI_EMBEDDING_DIMENSIONS=1024,
        OCI_VECTOR_DIMENSIONS=1024,
    )

    visibility = OperationalDiagnostics(settings).infrastructure_visibility(
        retrieval={"provider": "local_json", "store": {"exists": True, "chunk_count": 44}},
        refresh_status={"status": "succeeded"},
    )

    embeddings = visibility["providers"]["embeddings"]
    assert embeddings["configured_provider"] == "oci_genai"
    assert embeddings["oci_genai_embeddings_configured"] is True
    assert embeddings["activation_ready"] is True
    assert embeddings["expected_dimensions"] == 1024
    assert embeddings["vector_dimensions"] == 1024
    assert embeddings["missing_config"] == []


def test_embedding_visibility_reports_missing_genai_config() -> None:
    settings = Settings(EMBEDDING_PROVIDER="oci_genai")

    visibility = OperationalDiagnostics(settings).infrastructure_visibility(
        retrieval={"provider": "local_json", "store": {"exists": True, "chunk_count": 44}},
        refresh_status={"status": "succeeded"},
    )

    embeddings = visibility["providers"]["embeddings"]
    assert embeddings["activation_ready"] is False
    assert embeddings["missing_config"] == [
        "OCI_GENAI_COMPARTMENT_ID",
        "OCI_GENAI_EMBEDDING_MODEL_ID",
    ]


def test_scheduler_diagnostics_use_configured_function_and_schedule_ocids() -> None:
    settings = Settings(
        DEPLOYMENT_PROFILE="oci_vm",
        OCI_KNOWLEDGE_REFRESH_FUNCTION_OCID="ocid1.fnfunc.oc1..example",
        OCI_KNOWLEDGE_REFRESH_RELEASE_SCHEDULE_OCID="ocid1.resourceschedulerschedule.oc1..release",
        OCI_KNOWLEDGE_REFRESH_STABLE_DOCS_SCHEDULE_OCID="ocid1.resourceschedulerschedule.oc1..docs",
    )

    visibility = OperationalDiagnostics(settings).infrastructure_visibility(
        retrieval={"provider": "local_json", "store": {"exists": True, "chunk_count": 44}},
        refresh_status={"status": "succeeded"},
    )

    scheduler = visibility["operational_workflows"]["scheduler"]
    workflows = visibility["configured_resources"]["workflows"]
    assert scheduler["configured"] is True
    assert scheduler["function_ocid_configured"] is True
    assert workflows["release_schedule_configured"] is True
    assert visibility["rebuildability"]["checklist"]["refresh_scheduler_iac"] is True
    assert not any(gap["area"] == "operations" for gap in visibility["gaps"])


def test_object_storage_retrieval_degrades_to_local_fallback_when_config_missing() -> None:
    settings = Settings(RETRIEVAL_PROVIDER="oci_object_storage", RETRIEVAL_FALLBACK_ENABLED=True)

    diagnostics = build_retriever(settings).diagnostics()

    assert diagnostics["provider"] == "oci_object_storage"
    assert diagnostics["store"]["fallback_enabled"] is True
    assert diagnostics["store"]["fallback_active"] is True
    assert diagnostics["store"]["fallback"]["exists"] is True
