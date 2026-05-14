from oci_arch_studio_backend.models.architecture import (
    ArchitectureReviewRequest,
    ArchitectureReviewResponse,
)
from oci_arch_studio_backend.services.retrieval import PlaceholderRetriever


class ArchitectureReviewOrchestrator:
    """Coordinates retrieval and response shaping for the first vertical slice."""

    def __init__(self, retriever: PlaceholderRetriever) -> None:
        self.retriever = retriever

    async def review(
        self,
        request: ArchitectureReviewRequest,
    ) -> ArchitectureReviewResponse:
        sources = await self.retriever.retrieve(request.question)

        return ArchitectureReviewResponse(
            answer=(
                "This is an initial architecture review scaffold. Based on the "
                "placeholder OCI guidance, start by clarifying workload goals, "
                "availability requirements, security boundaries, data flows, "
                "and cost constraints before selecting services."
            ),
            recommendations=[
                "Define target regions, availability domains, and fault domains early.",
                "Separate public entry points, application tiers, and data services with explicit network boundaries.",
                "Capture non-functional requirements before choosing compute, database, and integration services.",
                "Require citations for production recommendations once retrieval is enabled.",
            ],
            assumptions=[
                "The question is exploratory and not yet tied to a finalized workload design.",
                "The current response uses placeholder retrieval instead of a production OCI knowledge index.",
            ],
            risks=[
                "Recommendations are not yet validated against current OCI release changes.",
                "Cost guidance is directional until workload sizing and pricing inputs are added.",
            ],
            citations=sources,
            next_steps=[
                "Add a curated OCI seed corpus for the first retrieval-backed response.",
                "Create eval cases for unsupported claims and missing assumptions.",
                "Introduce a prompt template that requires cited, structured output.",
            ],
        )
