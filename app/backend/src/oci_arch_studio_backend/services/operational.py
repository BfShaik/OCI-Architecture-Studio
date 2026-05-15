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
        "scheduler": "oci_resource_scheduler_to_oci_functions",
        "observability": "oci_logging_monitoring_notifications",
        "fallback": "deterministic_local_json",
    },
    "oke": {
        "runtime": "oci_kubernetes_engine",
        "auth": "workload_identity_or_instance_principal",
        "secrets": "oci_vault_or_kubernetes_secret_reference",
        "scheduler": "oci_resource_scheduler_to_oci_functions",
        "observability": "oci_logging_monitoring_notifications",
        "fallback": "deterministic_local_json",
    },
    "oci_functions": {
        "runtime": "oci_functions",
        "auth": "resource_principal",
        "secrets": "oci_vault",
        "scheduler": "oci_resource_scheduler",
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

        if response.get("low_confidence"):
            self.metrics.fallback_events["low_confidence_response"] += 1
        confidence = response.get("confidence") or {}
        level = str(confidence.get("level") or "unknown")
        self.metrics.confidence_distribution[level] += 1

        intent = str(response.get("intent") or "unknown")
        self.metrics.workload_usage[intent] += 1

        findings = HallucinationDetector().detect(response)
        for finding in findings:
            self.metrics.hallucination_findings[f"{finding.severity}:{finding.category}"] += 1

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
        if profile in {"oci_vm", "oke", "oci_functions"} and self.settings.oci_auth_mode == "config_file":
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
            "retrieval_metrics": retrieval_metrics.snapshot(),
            "advisory_metrics": advisory_quality_metrics.snapshot(),
            "operational_metrics": operational_metrics.snapshot(),
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
