from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class ArchitectureReviewRequest(BaseModel):
    question: str = Field(
        min_length=3,
        description="User's OCI architecture question or scenario.",
    )
    workload_context: str | None = Field(
        default=None,
        description="Optional workload, constraints, or business context.",
    )


class RetrievedSource(BaseModel):
    chunk_id: str | None = None
    title: str
    source_type: str
    url: str | None = None
    summary: str
    relevance_score: float | None = None


class ArchitectureReviewResponse(BaseModel):
    intent: str
    prompt_template: str
    answer: str
    recommendations: list[str]
    assumptions: list[str]
    risks: list[str]
    citations: list[RetrievedSource]
    next_steps: list[str]
