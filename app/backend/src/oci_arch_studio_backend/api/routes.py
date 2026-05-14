from fastapi import APIRouter

from oci_arch_studio_backend.models.architecture import (
    ArchitectureReviewRequest,
    ArchitectureReviewResponse,
    HealthResponse,
)
from oci_arch_studio_backend.services.orchestrator import ArchitectureReviewOrchestrator
from oci_arch_studio_backend.services.retrieval import PlaceholderRetriever

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service="oci-architecture-studio-api")


@router.post("/architecture-review", response_model=ArchitectureReviewResponse)
async def architecture_review(
    request: ArchitectureReviewRequest,
) -> ArchitectureReviewResponse:
    retriever = PlaceholderRetriever()
    orchestrator = ArchitectureReviewOrchestrator(retriever=retriever)
    return await orchestrator.review(request)
