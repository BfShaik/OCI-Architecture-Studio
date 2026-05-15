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


class EvidenceLink(BaseModel):
    recommendation_index: int
    support_level: str
    source_chunk_ids: list[str] = Field(default_factory=list)
    source_titles: list[str] = Field(default_factory=list)
    rationale: str


class ConfidenceScore(BaseModel):
    retrieval: float
    evidence: float
    freshness: float
    release_awareness: float
    recommendation: float
    overall: float
    level: str
    notes: list[str] = Field(default_factory=list)


class ArchitectureReviewResponse(BaseModel):
    intent: str
    prompt_template: str
    synthesis_provider: str = "deterministic"
    synthesis_model: str | None = None
    synthesis_warnings: list[str] = Field(default_factory=list)
    synthesis_fallback_used: bool = False
    answer: str
    recommendations: list[str]
    assumptions: list[str]
    risks: list[str]
    citations: list[RetrievedSource]
    evidence_links: list[EvidenceLink] = Field(default_factory=list)
    confidence: ConfidenceScore | None = None
    quality_warnings: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    not_enough_evidence: bool = False
    low_confidence: bool = False
    next_steps: list[str]
