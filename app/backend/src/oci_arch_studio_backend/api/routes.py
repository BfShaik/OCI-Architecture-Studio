from fastapi import APIRouter

from oci_arch_studio_backend.models.architecture import (
    ArchitectureReviewRequest,
    ArchitectureReviewResponse,
    HealthResponse,
)
from oci_arch_studio_backend.core.config import get_settings
from oci_arch_studio_backend.services.advisory_metrics import advisory_quality_metrics
from oci_arch_studio_backend.services.orchestrator import ArchitectureReviewOrchestrator
from oci_arch_studio_backend.services.operational import OperationalDiagnostics, read_refresh_status
from oci_arch_studio_backend.services.releases import ReleaseSnapshotStore
from oci_arch_studio_backend.services.retrieval import build_retriever
from oci_arch_studio_backend.services.synthesis import build_synthesizer
from oci_arch_studio_backend.services.supervised_orchestration import (
    SupervisedAgentOrchestrator,
)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service="oci-architecture-studio-api")


@router.post("/architecture-review", response_model=ArchitectureReviewResponse)
async def architecture_review(
    request: ArchitectureReviewRequest,
) -> ArchitectureReviewResponse:
    settings = get_settings()
    retriever = build_retriever(settings)
    synthesizer = build_synthesizer(
        provider=settings.advisory_synthesis_provider,
        region=settings.oci_region,
        profile=settings.oci_profile,
        auth_mode=settings.oci_auth_mode,
        compartment_id=settings.oci_genai_compartment_id,
        model_id=settings.oci_genai_chat_model_id,
        endpoint=settings.oci_genai_endpoint,
        max_tokens=settings.oci_genai_max_tokens,
        temperature=settings.oci_genai_temperature,
    )
    release_store = ReleaseSnapshotStore(snapshot_path=settings.release_snapshot_path)
    orchestrator = ArchitectureReviewOrchestrator(
        retriever=retriever,
        release_store=release_store,
        synthesizer=synthesizer,
        agent_orchestrator=SupervisedAgentOrchestrator(
            mode=settings.advisory_orchestration_mode,
        ),
        synthesis_debug_enabled=settings.synthesis_debug_enabled,
    )
    return await orchestrator.review(request)


@router.get("/retrieval/health")
async def retrieval_health() -> dict[str, object]:
    settings = get_settings()
    retriever = build_retriever(settings)
    return retriever.diagnostics()


@router.get("/knowledge/refresh/status")
async def knowledge_refresh_status() -> dict[str, object]:
    settings = get_settings()
    return read_refresh_status(settings.knowledge_refresh_status_path)


@router.get("/advisory/quality")
async def advisory_quality() -> dict[str, object]:
    return advisory_quality_metrics.snapshot()


@router.get("/orchestration/health")
async def orchestration_health() -> dict[str, object]:
    snapshot = advisory_quality_metrics.snapshot()
    return {
        "mode": snapshot.get("last_orchestration_mode"),
        "active_agents": snapshot.get("last_active_agents", []),
        "last_routing_decision": snapshot.get("last_routing_decision"),
        "last_aggregation_decision": snapshot.get("last_aggregation_decision"),
        "last_agent_count": snapshot.get("last_agent_count", 0),
        "critic_warning_count": snapshot.get("critic_warning_count", 0),
        "orchestration_failure_count": snapshot.get("orchestration_failure_count", 0),
        "request_count": snapshot.get("request_count", 0),
    }


@router.get("/operations/profile")
async def operations_profile() -> dict[str, object]:
    settings = get_settings()
    return OperationalDiagnostics(settings).deployment_profile()


@router.get("/operations/health")
async def operations_health() -> dict[str, object]:
    settings = get_settings()
    diagnostics = OperationalDiagnostics(settings)
    retriever = build_retriever(settings)
    return diagnostics.runtime_status(
        retrieval=retriever.diagnostics(),
        refresh_status=read_refresh_status(settings.knowledge_refresh_status_path),
    )


@router.get("/operations/analytics")
async def operations_analytics() -> dict[str, object]:
    settings = get_settings()
    diagnostics = OperationalDiagnostics(settings)
    return {
        "deployment": diagnostics.deployment_profile(),
        "observability": diagnostics.observability_status(),
        "advisory_quality": advisory_quality_metrics.snapshot(),
    }
