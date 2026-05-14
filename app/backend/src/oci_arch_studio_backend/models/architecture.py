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
    source_url: str | None = None
    service: str | None = None
    service_domain: str | None = None
    intent_tags: list[str] = Field(default_factory=list)
    fetched_timestamp: str | None = None
    freshness_score: float | None = None
    trust_level: str | None = None
    architecture_patterns: list[str] = Field(default_factory=list)
    is_stale: bool = False
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
