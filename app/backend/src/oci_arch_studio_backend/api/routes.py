from fastapi import APIRouter, HTTPException, Response

from oci_arch_studio_backend.models.architecture import (
    ArchitectureReviewRequest,
    ArchitectureReviewResponse,
    HealthResponse,
    ReviewHistoryDetail,
    ReviewHistoryExportResponse,
    ReviewHistoryListResponse,
    ReviewHistoryPolicy,
)
from oci_arch_studio_backend.core.config import get_settings
from oci_arch_studio_backend.services.advisory_metrics import advisory_quality_metrics
from oci_arch_studio_backend.services.orchestrator import ArchitectureReviewOrchestrator
from oci_arch_studio_backend.services.operational import OperationalDiagnostics, read_refresh_status
from oci_arch_studio_backend.services.releases import ReleaseSnapshotStore
from oci_arch_studio_backend.services.retrieval import build_retriever
from oci_arch_studio_backend.services.review_history import ReviewHistoryStore
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
    response = await orchestrator.review(request)
    if request.save_to_history:
        saved = ReviewHistoryStore(settings.review_history_path).save(request, response)
        response.review_id = saved.review_id
    return response


@router.get("/review-history", response_model=ReviewHistoryListResponse)
async def review_history() -> ReviewHistoryListResponse:
    settings = get_settings()
    return ReviewHistoryStore(settings.review_history_path).list()


@router.get("/review-history/policy", response_model=ReviewHistoryPolicy)
async def review_history_policy() -> ReviewHistoryPolicy:
    settings = get_settings()
    return ReviewHistoryStore(settings.review_history_path).policy()


@router.get("/review-history/export", response_model=ReviewHistoryExportResponse)
async def export_review_history() -> ReviewHistoryExportResponse:
    settings = get_settings()
    return ReviewHistoryStore(settings.review_history_path).export()


@router.delete("/review-history", status_code=204)
async def delete_review_history() -> Response:
    return _delete_review_history()


@router.post("/review-history/delete-all", status_code=204)
async def post_delete_review_history() -> Response:
    return _delete_review_history()


@router.get("/review-history/{review_id}", response_model=ReviewHistoryDetail)
async def review_history_detail(review_id: str) -> ReviewHistoryDetail:
    settings = get_settings()
    detail = ReviewHistoryStore(settings.review_history_path).get(review_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Review history item not found.")
    return detail


@router.delete("/review-history/{review_id}", status_code=204)
async def delete_review_history_item(review_id: str) -> Response:
    return _delete_review_history_item(review_id)


@router.post("/review-history/{review_id}/delete", status_code=204)
async def post_delete_review_history_item(review_id: str) -> Response:
    return _delete_review_history_item(review_id)


def _delete_review_history_item(review_id: str) -> Response:
    settings = get_settings()
    deleted = ReviewHistoryStore(settings.review_history_path).delete(review_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Review history item not found.")
    return Response(status_code=204)


def _delete_review_history() -> Response:
    settings = get_settings()
    ReviewHistoryStore(settings.review_history_path).delete_all()
    return Response(status_code=204)


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


@router.get("/operations/readiness")
async def operations_readiness() -> dict[str, object]:
    settings = get_settings()
    diagnostics = OperationalDiagnostics(settings)
    retriever = build_retriever(settings)
    return diagnostics.runtime_readiness(
        retrieval=retriever.diagnostics(),
        refresh_status=read_refresh_status(settings.knowledge_refresh_status_path),
    )


@router.get("/operations/infrastructure")
async def operations_infrastructure() -> dict[str, object]:
    settings = get_settings()
    diagnostics = OperationalDiagnostics(settings)
    retriever = build_retriever(settings)
    return diagnostics.infrastructure_visibility(
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
