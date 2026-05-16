from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from oci_arch_studio_backend.core.config import Settings
from oci_arch_studio_backend.services.advisory_metrics import advisory_quality_metrics
from oci_arch_studio_backend.services.evaluation_intelligence import HallucinationDetector
from oci_arch_studio_backend.services.retrieval_metrics import retrieval_metrics


DEPLOYMENT_PROFILE_CAPABILITIES: dict[str, dict[str, object]] = {
    "local_dev": {
        "runtime": "local",
        "auth": "config_file",
        "secrets": "environment_or_dotenv",
        "scheduler": "manual_local_commands",
        "observability": "stdout_and_local_health_endpoints",
        "fallback": "deterministic_local",
    },
    "oci_vm": {
        "runtime": "oci_compute",
        "auth": "instance_principal",
        "secrets": "oci_vault",
        "scheduler": "backend_vm_cron",
        "observability": "oci_logging_monitoring_notifications",
        "fallback": "deterministic_local_json",
    },
    "oke": {
        "runtime": "oci_kubernetes_engine",
        "auth": "workload_identity_or_instance_principal",
        "secrets": "oci_vault_or_kubernetes_secret_reference",
        "scheduler": "operator_managed_or_vm_cron",
        "observability": "oci_logging_monitoring_notifications",
        "fallback": "deterministic_local_json",
    },
}


@dataclass
class OperationalMetrics:
    request_count: int = 0
    provider_usage: Counter[str] = field(default_factory=Counter)
    synthesis_provider_usage: Counter[str] = field(default_factory=Counter)
    workload_usage: Counter[str] = field(default_factory=Counter)
    confidence_distribution: Counter[str] = field(default_factory=Counter)
    fallback_events: Counter[str] = field(default_factory=Counter)
    hallucination_findings: Counter[str] = field(default_factory=Counter)
    governance_policy_triggers: Counter[str] = field(default_factory=Counter)
    governance_risk_trends: Counter[str] = field(default_factory=Counter)
    runtime_degradation_events: Counter[str] = field(default_factory=Counter)
    architecture_comparison_usage: Counter[str] = field(default_factory=Counter)
    recommendation_category_trends: Counter[str] = field(default_factory=Counter)
    architecture_pattern_usage: Counter[str] = field(default_factory=Counter)
    migration_recommendation_trends: Counter[str] = field(default_factory=Counter)
    modernization_recommendation_trends: Counter[str] = field(default_factory=Counter)
    finops_recommendation_frequency: Counter[str] = field(default_factory=Counter)
    workload_optimization_patterns: Counter[str] = field(default_factory=Counter)
    executive_summary_count: int = 0
    visualization_generation_count: int = 0
    review_artifact_count: int = 0
    total_response_latency_ms: float = 0.0
    last_response_latency_ms: float | None = None
    last_event_at: str | None = None

    @property
    def average_response_latency_ms(self) -> float:
        if self.request_count == 0:
            return 0.0
        return round(self.total_response_latency_ms / self.request_count, 2)

    def as_dict(self) -> dict[str, object]:
        return {
            "request_count": self.request_count,
            "provider_usage": dict(self.provider_usage),
            "synthesis_provider_usage": dict(self.synthesis_provider_usage),
            "workload_usage": dict(self.workload_usage),
            "confidence_distribution": dict(self.confidence_distribution),
            "fallback_events": dict(self.fallback_events),
            "hallucination_findings": dict(self.hallucination_findings),
            "governance_policy_triggers": dict(self.governance_policy_triggers),
            "governance_risk_trends": dict(self.governance_risk_trends),
            "runtime_degradation_events": dict(self.runtime_degradation_events),
            "architecture_comparison_usage": dict(self.architecture_comparison_usage),
            "recommendation_category_trends": dict(self.recommendation_category_trends),
            "architecture_pattern_usage": dict(self.architecture_pattern_usage),
            "migration_recommendation_trends": dict(self.migration_recommendation_trends),
            "modernization_recommendation_trends": dict(self.modernization_recommendation_trends),
            "finops_recommendation_frequency": dict(self.finops_recommendation_frequency),
            "workload_optimization_patterns": dict(self.workload_optimization_patterns),
            "executive_summary_count": self.executive_summary_count,
            "visualization_generation_count": self.visualization_generation_count,
            "review_artifact_count": self.review_artifact_count,
            "average_response_latency_ms": self.average_response_latency_ms,
            "last_response_latency_ms": self.last_response_latency_ms,
            "last_event_at": self.last_event_at,
        }


class OperationalMetricsRecorder:
    def __init__(self) -> None:
        self.metrics = OperationalMetrics()

    def start(self) -> float:
        return perf_counter()

    def record_response(
        self,
        *,
        started_at: float,
        response: dict[str, Any],
    ) -> None:
        latency_ms = round((perf_counter() - started_at) * 1000, 2)
        self.metrics.request_count += 1
        self.metrics.total_response_latency_ms += latency_ms
        self.metrics.last_response_latency_ms = latency_ms
        self.metrics.last_event_at = now_iso()

        retrieval_debug = response.get("retrieval_debug") or {}
        provider = retrieval_debug.get("provider") or retrieval_metrics.snapshot().get("last_provider") or "unknown"
        self.metrics.provider_usage[str(provider)] += 1

        synthesis_provider = str(response.get("synthesis_provider") or "unknown")
        self.metrics.synthesis_provider_usage[synthesis_provider] += 1
        if response.get("synthesis_fallback_used"):
            self.metrics.fallback_events["synthesis"] += 1
            self.metrics.runtime_degradation_events["synthesis_fallback"] += 1

        if response.get("low_confidence"):
            self.metrics.fallback_events["low_confidence_response"] += 1
            self.metrics.runtime_degradation_events["low_confidence_response"] += 1
        confidence = response.get("confidence") or {}
        level = str(confidence.get("level") or "unknown")
        self.metrics.confidence_distribution[level] += 1

        intent = str(response.get("intent") or "unknown")
        self.metrics.workload_usage[intent] += 1

        findings = HallucinationDetector().detect(response)
        for finding in findings:
            self.metrics.hallucination_findings[f"{finding.severity}:{finding.category}"] += 1

        governance = response.get("enterprise_governance") or {}
        if isinstance(governance, dict):
            for annotation in governance.get("governance_annotations", []):
                if isinstance(annotation, dict):
                    trigger = annotation.get("policy_signal")
                    if trigger:
                        self.metrics.governance_policy_triggers[str(trigger)] += 1
            for risk in governance.get("risk_classifications", []):
                if isinstance(risk, dict):
                    level = str(risk.get("level") or "unknown")
                    category = str(risk.get("category") or "unknown")
                    self.metrics.governance_risk_trends[f"{level}:{category}"] += 1
            for priority in governance.get("recommendation_priorities", []):
                if isinstance(priority, dict):
                    self.metrics.recommendation_category_trends[str(priority.get("priority") or "unknown")] += 1
            for comparison in governance.get("architecture_comparisons", []):
                if isinstance(comparison, dict):
                    self.metrics.architecture_comparison_usage[str(comparison.get("decision") or "unknown")] += 1

        topology = response.get("architecture_topology") or {}
        if isinstance(topology, dict) and topology.get("mermaid_flow"):
            self.metrics.visualization_generation_count += 1
            for node in topology.get("nodes", []):
                if isinstance(node, dict):
                    pattern = node.get("role") or node.get("category")
                    if pattern:
                        self.metrics.architecture_pattern_usage[str(pattern)] += 1

        executive = response.get("executive_experience") or {}
        if isinstance(executive, dict):
            if executive.get("executive_summary"):
                self.metrics.executive_summary_count += 1
            artifacts = executive.get("review_artifacts", [])
            if isinstance(artifacts, list):
                self.metrics.review_artifact_count += len(artifacts)

        optimization = response.get("optimization_plan") or {}
        if isinstance(optimization, dict):
            for phase in optimization.get("migration_phases", []):
                if isinstance(phase, dict):
                    self.metrics.migration_recommendation_trends[str(phase.get("phase") or "unknown")] += 1
            for option in optimization.get("modernization_options", []):
                if isinstance(option, dict):
                    self.metrics.modernization_recommendation_trends[str(option.get("approach") or "unknown")] += 1
            for item in optimization.get("finops_recommendations", []):
                if isinstance(item, dict):
                    self.metrics.finops_recommendation_frequency[str(item.get("lever") or "unknown")] += 1
            for signal in optimization.get("workload_optimization_signals", []):
                if isinstance(signal, dict):
                    self.metrics.workload_optimization_patterns[str(signal.get("workload") or "unknown")] += 1
            for comparison in optimization.get("optimization_comparisons", []):
                if isinstance(comparison, dict):
                    self.metrics.architecture_comparison_usage[str(comparison.get("decision") or "unknown")] += 1

    def snapshot(self) -> dict[str, object]:
        return self.metrics.as_dict()


operational_metrics = OperationalMetricsRecorder()


class OperationalDiagnostics:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def deployment_profile(self) -> dict[str, object]:
        profile = self.settings.deployment_profile
        capabilities = DEPLOYMENT_PROFILE_CAPABILITIES.get(profile, DEPLOYMENT_PROFILE_CAPABILITIES["local_dev"])
        warnings: list[str] = []
        if profile not in DEPLOYMENT_PROFILE_CAPABILITIES:
            warnings.append(f"Unknown deployment profile '{profile}', using local_dev capability assumptions.")
        if profile in {"oci_vm", "oke"} and self.settings.oci_auth_mode == "config_file":
            warnings.append("OCI runtime profile should normally use instance_principal, resource_principal, or workload identity.")
        if profile != "local_dev" and not self.settings.oci_region:
            warnings.append("OCI_REGION is not configured for an OCI runtime profile.")
        return {
            "profile": profile,
            "app_env": self.settings.app_env,
            "capabilities": capabilities,
            "warnings": warnings,
        }

    def secrets_status(self) -> dict[str, object]:
        configured = bool(self.settings.oci_vault_config_secret_ocid)
        status = {
            "provider": "oci_vault" if configured else "local_environment",
            "configured": configured,
            "secret_ocid_configured": configured,
            "auth_mode": self.settings.oci_auth_mode,
            "plaintext_secret_fields_present": self._plaintext_secret_fields_present(),
            "validation": "not_checked",
            "error": None,
        }
        if configured and self.settings.oci_connectivity_check_enabled:
            try:
                self._read_secret_bundle_metadata(self.settings.oci_vault_config_secret_ocid or "")
                status["validation"] = "reachable"
            except Exception as exc:
                status["validation"] = "failed"
                status["error"] = str(exc)
        elif configured:
            status["validation"] = "configured_not_checked"
        return status

    def observability_status(self) -> dict[str, object]:
        return {
            "logging": {
                "provider": "oci_logging" if self.settings.oci_logging_log_group_ocid else "stdout",
                "log_group_ocid_configured": bool(self.settings.oci_logging_log_group_ocid),
            },
            "audit": {
                "provider": "oci_audit",
                "mode": "platform_native",
                "message": "OCI Audit is treated as a native tenancy service; advisory trace events remain in-process until log export is enabled.",
            },
            "monitoring": {
                "provider": "oci_monitoring",
                "namespace": self.settings.oci_monitoring_namespace,
                "connectivity_check_enabled": self.settings.oci_connectivity_check_enabled,
            },
            "notifications": {
                "provider": "oci_notifications" if self.settings.oci_notifications_topic_ocid else "not_configured",
                "topic_ocid_configured": bool(self.settings.oci_notifications_topic_ocid),
            },
            "events": {
                "provider": "oci_events" if self.settings.oci_events_rule_ocid else "not_configured",
                "rule_ocid_configured": bool(self.settings.oci_events_rule_ocid),
            },
            "metrics": operational_metrics.snapshot(),
        }

    def runtime_status(
        self,
        *,
        retrieval: dict[str, object],
        refresh_status: dict[str, object],
    ) -> dict[str, object]:
        checks = {
            "retrieval_provider": self._check_retrieval(retrieval),
            "vector_index": self._check_vector_index(retrieval),
            "release_freshness": self._check_release_freshness(refresh_status),
            "synthesis_provider": self._check_synthesis_provider(),
            "oci_connectivity": self._check_oci_connectivity(),
            "secrets": self.secrets_status(),
        }
        summary_status = "ok"
        if any(check.get("status") == "critical" for check in checks.values() if isinstance(check, dict)):
            summary_status = "critical"
        elif any(check.get("status") == "warning" for check in checks.values() if isinstance(check, dict)):
            summary_status = "warning"
        return {
            "status": summary_status,
            "generated_at": now_iso(),
            "deployment": self.deployment_profile(),
            "checks": checks,
            "runtime_readiness": self.runtime_readiness(retrieval=retrieval, refresh_status=refresh_status),
            "retrieval_metrics": retrieval_metrics.snapshot(),
            "advisory_metrics": advisory_quality_metrics.snapshot(),
            "operational_metrics": operational_metrics.snapshot(),
        }

    def infrastructure_visibility(
        self,
        *,
        retrieval: dict[str, object],
        refresh_status: dict[str, object],
    ) -> dict[str, object]:
        """Return an operator-readable view of OCI runtime topology and IaC maturity."""
        api_gateway = self._check_api_gateway()
        devops = self._check_oci_devops()
        scheduler = self._scheduler_status()
        configured_resources = self._configured_runtime_resources(api_gateway=api_gateway, devops=devops)
        gaps = self._infrastructure_gaps(
            api_gateway=api_gateway,
            devops=devops,
            scheduler=scheduler,
            retrieval=retrieval,
        )
        return {
            "generated_at": now_iso(),
            "environment": {
                "app_env": self.settings.app_env,
                "deployment_profile": self.settings.deployment_profile,
                "oci_region": self.settings.oci_region,
                "oci_auth_mode": self.settings.oci_auth_mode,
            },
            "topology": self._runtime_topology(api_gateway=api_gateway),
            "configured_resources": configured_resources,
            "providers": {
                "retrieval": self._retrieval_provider_visibility(retrieval),
                "synthesis": self._synthesis_provider_visibility(),
                "embeddings": self._embedding_provider_visibility(),
            },
            "operational_workflows": {
                "release_refresh": self._check_release_freshness(refresh_status),
                "scheduler": scheduler,
                "deployment": {
                    "provider": "oci_devops" if devops.get("promotion_ready") else "operator_scripts",
                    "oci_devops_configured": bool(devops.get("configured")),
                    "oci_devops_promotion_ready": bool(devops.get("promotion_ready")),
                    "message": devops.get("message"),
                },
            },
            "rebuildability": self._rebuildability_status(configured_resources=configured_resources, gaps=gaps),
            "gaps": gaps,
            "notes": [
                "Infrastructure visibility is configuration-derived and read-only; it does not prove live OCI resource reachability unless connectivity checks are enabled.",
                "Scaffolded resources are reported separately from active runtime providers to avoid overstating staging maturity.",
            ],
        }

    def runtime_readiness(
        self,
        *,
        retrieval: dict[str, object],
        refresh_status: dict[str, object],
    ) -> dict[str, object]:
        checks = {
            "startup_environment": self._check_startup_environment(),
            "dependency_configuration": self._check_dependency_configuration(),
            "api_gateway": self._check_api_gateway(),
            "oci_devops": self._check_oci_devops(),
            "runtime_safeguards": self._check_runtime_safeguards(retrieval),
            "fallback_paths": self._check_fallback_paths(),
            "release_refresh": self._check_release_freshness(refresh_status),
        }
        critical = [
            name
            for name, check in checks.items()
            if isinstance(check, dict) and check.get("status") == "critical"
        ]
        warnings = [
            name
            for name, check in checks.items()
            if isinstance(check, dict) and check.get("status") == "warning"
        ]
        status = "critical" if critical else "warning" if warnings else "ok"
        return {
            "status": status,
            "profile": self.settings.deployment_profile,
            "checks": checks,
            "critical_checks": critical,
            "warning_checks": warnings,
            "notes": [
                "Runtime readiness is a deterministic operational diagnostic, not a production certification.",
                "OCI API Gateway and OCI DevOps checks are readiness/configuration checks until their OCIDs or endpoints are provisioned.",
            ],
        }

    def _check_retrieval(self, retrieval: dict[str, object]) -> dict[str, object]:
        store = retrieval.get("store", {}) if isinstance(retrieval.get("store"), dict) else {}
        exists = bool(store.get("exists"))
        return {
            "status": "ok" if exists else "critical",
            "provider": retrieval.get("provider"),
            "chunk_count": store.get("chunk_count", 0),
            "fallback_active": store.get("fallback_active", False),
            "warnings": retrieval.get("metrics", {}).get("warnings", []) if isinstance(retrieval.get("metrics"), dict) else [],
        }

    def _check_vector_index(self, retrieval: dict[str, object]) -> dict[str, object]:
        store = retrieval.get("store", {}) if isinstance(retrieval.get("store"), dict) else {}
        provider = str(retrieval.get("provider") or "")
        if provider != "oracle_ai_vector_search":
            return {
                "status": "ok",
                "provider": provider,
                "message": "Oracle AI Vector Search is not the active retrieval provider.",
            }
        primary = store.get("primary", {}) if isinstance(store.get("primary"), dict) else store
        fallback_active = bool(store.get("fallback_active"))
        status = "warning" if fallback_active else "ok"
        if not primary.get("exists") and not fallback_active:
            status = "critical"
        return {
            "status": status,
            "provider": provider,
            "fallback_active": fallback_active,
            "expected_dimensions": primary.get("expected_dimensions"),
            "chunk_count": store.get("chunk_count", 0),
            "last_error": primary.get("last_error"),
        }

    def _check_release_freshness(self, refresh_status: dict[str, object]) -> dict[str, object]:
        status = str(refresh_status.get("status") or "unknown")
        return {
            "status": "warning" if status in {"not_initialized", "failed"} else "ok",
            "refresh_status": status,
            "last_run": refresh_status.get("last_run"),
            "current_promoted_snapshot": refresh_status.get("current_promoted_snapshot"),
        }

    def _check_synthesis_provider(self) -> dict[str, object]:
        provider = self.settings.advisory_synthesis_provider
        missing: list[str] = []
        if provider == "oci_genai":
            for name, value in (
                ("OCI_GENAI_COMPARTMENT_ID", self.settings.oci_genai_compartment_id),
                ("OCI_GENAI_CHAT_MODEL_ID", self.settings.oci_genai_chat_model_id),
            ):
                if not value:
                    missing.append(name)
        return {
            "status": "warning" if missing else "ok",
            "provider": provider,
            "missing_config": missing,
            "fallback_mode": "deterministic_fail_closed" if provider == "oci_genai" else "deterministic_default",
        }

    def _check_startup_environment(self) -> dict[str, object]:
        required_paths = {
            "knowledge_index_path": self.settings.knowledge_index_path.exists(),
            "release_snapshot_path": self.settings.release_snapshot_path.exists(),
            "frontend_dist_path": self.settings.frontend_dist_path.exists(),
        }
        missing = [name for name, exists in required_paths.items() if not exists]
        profile = self.settings.deployment_profile
        warnings = []
        if profile != "local_dev" and self.settings.oci_auth_mode == "config_file":
            warnings.append("OCI runtime profiles should avoid config_file auth outside local development.")
        return {
            "status": "critical" if missing else "warning" if warnings else "ok",
            "profile": profile,
            "app_env": self.settings.app_env,
            "paths": required_paths,
            "missing": missing,
            "warnings": warnings,
        }

    def _check_dependency_configuration(self) -> dict[str, object]:
        missing: list[str] = []
        if self.settings.retrieval_provider == "oci_object_storage":
            for name, value in (
                ("OCI_OBJECT_STORAGE_NAMESPACE", self.settings.oci_object_storage_namespace),
                ("OCI_VECTOR_BUCKET", self.settings.oci_vector_bucket),
            ):
                if not value:
                    missing.append(name)
        if self.settings.retrieval_provider == "oracle_ai_vector_search":
            for name, value in (
                ("OCI_VECTOR_DB_DSN", self.settings.oci_vector_db_dsn),
                ("OCI_VECTOR_DB_USER", self.settings.oci_vector_db_user),
                ("OCI_VECTOR_DB_PASSWORD", self.settings.oci_vector_db_password),
            ):
                if not value:
                    missing.append(name)
            if self.settings.oci_vector_wallet_location and not self.settings.oci_vector_wallet_password:
                missing.append("OCI_VECTOR_WALLET_PASSWORD")
        if self.settings.advisory_synthesis_provider == "oci_genai":
            for name, value in (
                ("OCI_GENAI_COMPARTMENT_ID", self.settings.oci_genai_compartment_id),
                ("OCI_GENAI_CHAT_MODEL_ID", self.settings.oci_genai_chat_model_id),
            ):
                if not value:
                    missing.append(name)
        return {
            "status": "warning" if missing else "ok",
            "retrieval_provider": self.settings.retrieval_provider,
            "synthesis_provider": self.settings.advisory_synthesis_provider,
            "missing_config": missing,
        }

    def _check_api_gateway(self) -> dict[str, object]:
        endpoint_configured = bool(self.settings.oci_api_gateway_endpoint)
        gateway_ocid_configured = bool(self.settings.oci_api_gateway_ocid)
        configured = endpoint_configured or gateway_ocid_configured
        promotion_ready = endpoint_configured and gateway_ocid_configured
        missing_config: list[str] = []
        if configured and not endpoint_configured:
            missing_config.append("OCI_API_GATEWAY_ENDPOINT")
        if configured and not gateway_ocid_configured:
            missing_config.append("OCI_API_GATEWAY_OCID")
        if promotion_ready:
            message = "OCI API Gateway endpoint and OCID are configured for the API exposure layer."
        elif configured:
            message = "OCI API Gateway is partially configured; keep direct backend VM exposure until endpoint and OCID are both set."
        else:
            message = "OCI API Gateway is not configured; current staging exposes the backend VM directly."
        return {
            "status": "ok" if promotion_ready else "warning",
            "provider": "oci_api_gateway",
            "configured": configured,
            "active": endpoint_configured,
            "promotion_ready": promotion_ready,
            "endpoint_configured": endpoint_configured,
            "gateway_ocid_configured": gateway_ocid_configured,
            "missing_config": missing_config,
            "message": message,
        }

    def _check_oci_devops(self) -> dict[str, object]:
        project_configured = bool(self.settings.oci_devops_project_ocid)
        deploy_pipeline_configured = bool(self.settings.oci_devops_deploy_pipeline_ocid)
        configured = project_configured or deploy_pipeline_configured
        promotion_ready = project_configured and deploy_pipeline_configured
        missing_config: list[str] = []
        if configured and not project_configured:
            missing_config.append("OCI_DEVOPS_PROJECT_OCID")
        if configured and not deploy_pipeline_configured:
            missing_config.append("OCI_DEVOPS_DEPLOY_PIPELINE_OCID")
        if promotion_ready:
            message = "OCI DevOps project and deploy pipeline metadata are configured."
        elif configured:
            message = "OCI DevOps is partially configured; keep operator scripts as the active deployment path."
        else:
            message = "OCI DevOps is not configured; deployment currently uses operator scripts."
        return {
            "status": "ok" if promotion_ready else "warning",
            "provider": "oci_devops",
            "configured": configured,
            "promotion_ready": promotion_ready,
            "project_ocid_configured": project_configured,
            "deploy_pipeline_ocid_configured": deploy_pipeline_configured,
            "missing_config": missing_config,
            "active_deployment_path": "oci_devops" if promotion_ready else "operator_scripts",
            "message": message,
        }

    def _check_runtime_safeguards(self, retrieval: dict[str, object]) -> dict[str, object]:
        store = retrieval.get("store", {}) if isinstance(retrieval.get("store"), dict) else {}
        fallback_active = bool(store.get("fallback_active"))
        warnings = []
        if fallback_active:
            warnings.append("Retrieval fallback is active.")
        if self.settings.deployment_profile != "local_dev" and not self.settings.oci_vault_config_secret_ocid:
            warnings.append("OCI Vault config secret is not configured for this runtime profile.")
        return {
            "status": "warning" if warnings else "ok",
            "retrieval_fallback_enabled": self.settings.retrieval_fallback_enabled,
            "embedding_fallback_enabled": self.settings.embedding_fallback_enabled,
            "deterministic_synthesis_available": True,
            "warnings": warnings,
        }

    def _runtime_topology(self, *, api_gateway: dict[str, object]) -> dict[str, object]:
        profile = self.settings.deployment_profile
        api_exposure = "oci_api_gateway" if api_gateway.get("active") else "direct_backend_vm"
        if profile == "oke":
            runtime_compute = "oci_kubernetes_engine"
        elif profile == "oci_vm":
            runtime_compute = "oci_compute_vm"
        else:
            runtime_compute = "local_process"
        return {
            "api_exposure": api_exposure,
            "runtime_compute": runtime_compute,
            "network": {
                "primary": "oci_vcn_public_subnet" if profile != "local_dev" else "local_loopback",
                "ingress": "api_gateway_to_backend" if api_gateway.get("active") else "public_backend_port",
                "security_boundary": "oci_iam_dynamic_group_and_network_rules" if profile != "local_dev" else "local_dev_boundary",
            },
            "state": {
                "knowledge_snapshots": (
                    "oci_object_storage"
                    if self.settings.oci_vector_bucket and self.settings.oci_object_storage_namespace
                    else "local_filesystem"
                ),
                "release_snapshots": "local_filesystem_with_object_storage_sync_scaffold",
            },
            "observability": {
                "logs": "oci_logging" if self.settings.oci_logging_log_group_ocid else "stdout",
                "metrics": "oci_monitoring",
                "notifications": "oci_notifications" if self.settings.oci_notifications_topic_ocid else "not_configured",
                "events": "oci_events" if self.settings.oci_events_rule_ocid else "not_configured",
            },
        }

    def _configured_runtime_resources(
        self,
        *,
        api_gateway: dict[str, object],
        devops: dict[str, object],
    ) -> dict[str, object]:
        return {
            "networking": {
                "vcn": "terraform_managed_when_deployed_to_oci",
                "public_subnet": "terraform_managed_when_deployed_to_oci",
                "api_gateway_configured": bool(api_gateway.get("configured")),
                "api_gateway_active": bool(api_gateway.get("active")),
                "api_gateway_promotion_ready": bool(api_gateway.get("promotion_ready")),
            },
            "runtime": {
                "deployment_profile": self.settings.deployment_profile,
                "api_gateway_endpoint_configured": bool(self.settings.oci_api_gateway_endpoint),
                "oci_devops_configured": bool(devops.get("configured")),
                "oci_devops_promotion_ready": bool(devops.get("promotion_ready")),
            },
            "storage": {
                "object_storage_namespace_configured": bool(self.settings.oci_object_storage_namespace),
                "knowledge_bucket_configured": bool(self.settings.oci_vector_bucket),
                "knowledge_object_name": self.settings.oci_vector_object_name,
            },
            "security": {
                "vault_config_secret_configured": bool(self.settings.oci_vault_config_secret_ocid),
                "auth_mode": self.settings.oci_auth_mode,
                "compartment_configured": bool(self.settings.oci_compartment_id),
            },
            "observability": {
                "logging_configured": bool(self.settings.oci_logging_log_group_ocid),
                "monitoring_namespace": self.settings.oci_monitoring_namespace,
                "notifications_configured": bool(self.settings.oci_notifications_topic_ocid),
                "events_configured": bool(self.settings.oci_events_rule_ocid),
            },
            "workflows": {
                "knowledge_refresh_scheduler": "backend_vm_cron",
                "release_watch_mode": "live_fetch_gated_upload",
                "stable_docs_mode": "candidate_only_safe_mode",
            },
            "ai": {
                "genai_chat_configured": bool(
                    self.settings.oci_genai_compartment_id and self.settings.oci_genai_chat_model_id
                ),
                "genai_embeddings_configured": bool(
                    self.settings.oci_genai_compartment_id and self.settings.oci_genai_embedding_model_id
                ),
                "oracle_ai_vector_search_configured": bool(
                    self.settings.oci_vector_db_dsn
                    and self.settings.oci_vector_db_user
                    and self.settings.oci_vector_db_password
                ),
            },
        }

    def _retrieval_provider_visibility(self, retrieval: dict[str, object]) -> dict[str, object]:
        store = retrieval.get("store", {}) if isinstance(retrieval.get("store"), dict) else {}
        return {
            "active_provider": retrieval.get("provider") or self.settings.retrieval_provider,
            "configured_provider": self.settings.retrieval_provider,
            "chunk_count": store.get("chunk_count", 0),
            "fallback_enabled": self.settings.retrieval_fallback_enabled,
            "fallback_active": bool(store.get("fallback_active")),
            "oracle_ai_vector_search_configured": bool(
                self.settings.oci_vector_db_dsn
                and self.settings.oci_vector_db_user
                and self.settings.oci_vector_db_password
            ),
        }

    def _synthesis_provider_visibility(self) -> dict[str, object]:
        return {
            "active_provider": self.settings.advisory_synthesis_provider,
            "deterministic_fallback_available": True,
            "oci_genai_configured": bool(
                self.settings.oci_genai_compartment_id and self.settings.oci_genai_chat_model_id
            ),
        }

    def _embedding_provider_visibility(self) -> dict[str, object]:
        missing_config: list[str] = []
        if self.settings.embedding_provider == "oci_genai":
            for name, value in (
                ("OCI_GENAI_COMPARTMENT_ID", self.settings.oci_genai_compartment_id),
                ("OCI_GENAI_EMBEDDING_MODEL_ID", self.settings.oci_genai_embedding_model_id),
            ):
                if not value:
                    missing_config.append(name)
        oci_genai_configured = bool(
            self.settings.oci_genai_compartment_id and self.settings.oci_genai_embedding_model_id
        )
        activation_ready = self.settings.embedding_provider == "oci_genai" and oci_genai_configured
        return {
            "configured_provider": self.settings.embedding_provider,
            "fallback_enabled": self.settings.embedding_fallback_enabled,
            "oci_genai_embeddings_configured": oci_genai_configured,
            "activation_ready": activation_ready,
            "expected_dimensions": self.settings.oci_genai_embedding_dimensions,
            "vector_dimensions": self.settings.oci_vector_dimensions,
            "missing_config": missing_config,
            "promotion_gate": (
                "run retrieval health, retrieval regression, and vector parity before promoting OCI GenAI embeddings"
                if activation_ready
                else "keep local deterministic embeddings active until OCI GenAI embedding config and parity are available"
            ),
        }

    def _scheduler_status(self) -> dict[str, object]:
        configured = self.settings.deployment_profile == "oci_vm"
        profile_compatible = self.settings.deployment_profile in {"oci_vm", "oke"}
        return {
            "provider": "backend_vm_cron",
            "configured": configured,
            "profile_compatible": profile_compatible,
            "release_watch_mode": "live_fetch_quick_gates_promote_and_upload",
            "stable_docs_mode": "no_fetch_quick_gates_candidate_only_no_upload",
            "message": "Knowledge refresh runs from cron on the OCI backend VM."
            if configured
            else "Knowledge refresh is operator-managed for this profile; staging uses backend OCI VM cron.",
        }

    def _infrastructure_gaps(
        self,
        *,
        api_gateway: dict[str, object],
        devops: dict[str, object],
        scheduler: dict[str, object],
        retrieval: dict[str, object],
    ) -> list[dict[str, object]]:
        gaps: list[dict[str, object]] = []
        if self.settings.deployment_profile != "local_dev" and self.settings.oci_auth_mode == "config_file":
            gaps.append(
                {
                    "severity": "high",
                    "area": "identity",
                    "message": "OCI runtime profile is using config-file auth instead of instance, resource, or workload identity.",
                    "recommended_action": "Use OCI IAM dynamic groups, instance principals, resource principals, or OKE workload identity for deployed runtimes.",
                }
            )
        if not api_gateway.get("configured"):
            gaps.append(
                {
                    "severity": "medium",
                    "area": "api_exposure",
                    "message": "OCI API Gateway is not configured; the backend VM direct exposure path remains active.",
                    "recommended_action": "Promote the default-off Terraform API Gateway scaffold when ingress hardening is ready.",
                }
            )
        if not devops.get("configured"):
            gaps.append(
                {
                    "severity": "medium",
                    "area": "delivery",
                    "message": "OCI DevOps deployment metadata is not configured; deployment currently relies on operator scripts.",
                    "recommended_action": "Wire OCI DevOps project and deploy pipeline OCIDs into Terraform/env configuration when delivery automation is promoted.",
                }
            )
        if not scheduler.get("configured") and self.settings.deployment_profile != "local_dev":
            gaps.append(
                {
                    "severity": "low",
                    "area": "operations",
                    "message": "Backend VM cron refresh is not the active scheduler for this runtime profile.",
                    "recommended_action": "Use the backend OCI VM cron runner or document an operator-managed refresh handoff for this environment.",
                }
            )
        store = retrieval.get("store", {}) if isinstance(retrieval.get("store"), dict) else {}
        if store.get("fallback_active"):
            gaps.append(
                {
                    "severity": "medium",
                    "area": "retrieval",
                    "message": "Retrieval provider is using a fallback path.",
                    "recommended_action": "Validate Object Storage or Oracle AI Vector Search configuration and re-run retrieval health checks.",
                }
            )
        if self.settings.deployment_profile != "local_dev" and not self.settings.oci_vault_config_secret_ocid:
            gaps.append(
                {
                    "severity": "medium",
                    "area": "secrets",
                    "message": "OCI Vault config secret is not configured for the runtime profile.",
                    "recommended_action": "Store runtime configuration and sensitive provider settings in OCI Vault.",
                }
            )
        return gaps

    def _rebuildability_status(
        self,
        *,
        configured_resources: dict[str, object],
        gaps: list[dict[str, object]],
    ) -> dict[str, object]:
        observability = configured_resources.get("observability", {})
        storage = configured_resources.get("storage", {})
        security = configured_resources.get("security", {})
        runtime = configured_resources.get("runtime", {})
        checklist = {
            "terraform_foundation_module": True,
            "networking_iac": True,
            "compute_profile_iac": self.settings.deployment_profile in {"oci_vm", "oke"},
            "object_storage_iac": bool(storage.get("knowledge_bucket_configured")) or self.settings.deployment_profile != "local_dev",
            "vault_iac": bool(security.get("vault_config_secret_configured")) or self.settings.deployment_profile != "local_dev",
            "observability_iac": bool(observability.get("logging_configured"))
            or bool(observability.get("notifications_configured"))
            or self.settings.deployment_profile != "local_dev",
            "api_gateway_iac": bool(runtime.get("api_gateway_endpoint_configured"))
            and bool(configured_resources.get("networking", {}).get("api_gateway_promotion_ready")),
            "oci_devops_iac": bool(runtime.get("oci_devops_promotion_ready")),
            "refresh_scheduler_iac": configured_resources.get("workflows", {}).get("knowledge_refresh_scheduler")
            == "backend_vm_cron"
            or self.settings.deployment_profile != "local_dev",
        }
        critical_or_high_gaps = [gap for gap in gaps if gap.get("severity") in {"critical", "high"}]
        status = "warning" if critical_or_high_gaps or not all(checklist.values()) else "ok"
        return {
            "status": status,
            "checklist": checklist,
            "summary": (
                "Core OCI rebuildability scaffolding is present; some promoted runtime integrations remain optional or unconfigured."
                if status == "warning"
                else "Runtime configuration indicates OCI rebuildability controls are configured."
            ),
        }

    def _check_fallback_paths(self) -> dict[str, object]:
        warnings = []
        if self.settings.advisory_synthesis_provider == "oci_genai":
            warnings.append("OCI GenAI synthesis must retain deterministic fail-closed fallback.")
        return {
            "status": "ok",
            "deterministic_synthesis": "available",
            "local_retrieval_fallback": self.settings.retrieval_fallback_enabled,
            "embedding_fallback": self.settings.embedding_fallback_enabled,
            "warnings": warnings,
        }

    def _check_oci_connectivity(self) -> dict[str, object]:
        if not self.settings.oci_connectivity_check_enabled:
            return {"status": "ok", "checked": False, "message": "OCI connectivity checks are disabled."}
        try:
            import oci

            if self.settings.oci_auth_mode == "instance_principal":
                signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
                client_config = {"region": self.settings.oci_region} if self.settings.oci_region else {}
                identity = oci.identity.IdentityClient(client_config, signer=signer)
            elif self.settings.oci_auth_mode == "resource_principal":
                signer = oci.auth.signers.get_resource_principals_signer()
                client_config = {"region": self.settings.oci_region} if self.settings.oci_region else {}
                identity = oci.identity.IdentityClient(client_config, signer=signer)
            else:
                client_config = oci.config.from_file(profile_name=self.settings.oci_profile)
                identity = oci.identity.IdentityClient(client_config)
            if self.settings.oci_compartment_id:
                identity.get_compartment(self.settings.oci_compartment_id)
            return {"status": "ok", "checked": True, "auth_mode": self.settings.oci_auth_mode}
        except Exception as exc:
            return {"status": "warning", "checked": True, "auth_mode": self.settings.oci_auth_mode, "error": str(exc)}

    def _plaintext_secret_fields_present(self) -> list[str]:
        present = []
        for name, value in (
            ("OCI_VECTOR_DB_PASSWORD", self.settings.oci_vector_db_password),
            ("OCI_VECTOR_WALLET_PASSWORD", self.settings.oci_vector_wallet_password),
            ("OPENAI_API_KEY", self.settings.openai_api_key),
        ):
            if value:
                present.append(name)
        return present

    def _read_secret_bundle_metadata(self, secret_id: str) -> None:
        try:
            import oci
        except ImportError as exc:
            raise RuntimeError("OCI SDK is required to validate OCI Vault secret access.") from exc
        if self.settings.oci_auth_mode == "instance_principal":
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            client_config = {"region": self.settings.oci_region} if self.settings.oci_region else {}
            client = oci.secrets.SecretsClient(client_config, signer=signer)
        elif self.settings.oci_auth_mode == "resource_principal":
            signer = oci.auth.signers.get_resource_principals_signer()
            client_config = {"region": self.settings.oci_region} if self.settings.oci_region else {}
            client = oci.secrets.SecretsClient(client_config, signer=signer)
        else:
            client_config = oci.config.from_file(profile_name=self.settings.oci_profile)
            if self.settings.oci_region:
                client_config["region"] = self.settings.oci_region
            client = oci.secrets.SecretsClient(client_config)
        client.get_secret_bundle(secret_id)


def read_refresh_status(path: Path) -> dict[str, object]:
    if not path.exists():
        return {
            "status": "not_initialized",
            "status_path": str(path),
            "last_run": None,
            "current_promoted_snapshot": None,
        }
    with path.open("r", encoding="utf-8") as file:
        status = json.load(file)
    status["status_path"] = str(path)
    return status


def now_iso() -> str:
    return datetime.now(UTC).isoformat()
