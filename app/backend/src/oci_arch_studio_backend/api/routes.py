from fastapi import APIRouter

from oci_arch_studio_backend.models.architecture import (
    ArchitectureReviewRequest,
    ArchitectureReviewResponse,
    HealthResponse,
)
from oci_arch_studio_backend.core.config import get_settings
from oci_arch_studio_backend.services.advisory_metrics import advisory_quality_metrics
from oci_arch_studio_backend.services.orchestrator import ArchitectureReviewOrchestrator
from oci_arch_studio_backend.services.releases import ReleaseSnapshotStore
from oci_arch_studio_backend.services.retrieval import build_retriever

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
    release_store = ReleaseSnapshotStore(snapshot_path=settings.release_snapshot_path)
    orchestrator = ArchitectureReviewOrchestrator(retriever=retriever, release_store=release_store)
    return await orchestrator.review(request)


@router.get("/retrieval/health")
async def retrieval_health() -> dict[str, object]:
    settings = get_settings()
    retriever = build_retriever(settings)
    return retriever.diagnostics()


@router.get("/advisory/quality")
async def advisory_quality() -> dict[str, object]:
    return advisory_quality_metrics.snapshot()
