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
    retrieval_debug: bool = Field(
        default=False,
        description="Include backend retrieval trace details for diagnostics.",
    )


class RetrievedSource(BaseModel):
    chunk_id: str | None = None
    title: str
    source_type: str
    url: str | None = None
    source_url: str | None = None
    service: str | None = None
    service_domain: str | None = None
    service_category: str | None = None
    category: str | None = None
    pattern: str | None = None
    workload: str | None = None
    workload_types: list[str] = Field(default_factory=list)
    domain: str | None = None
    domain_tags: list[str] = Field(default_factory=list)
    topic: str | None = None
    migration_mappings: dict[str, str] = Field(default_factory=dict)
    ha_dr_tags: list[str] = Field(default_factory=list)
    cost_optimization_tags: list[str] = Field(default_factory=list)
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


class SectionCitationSource(BaseModel):
    chunk_id: str | None = None
    source_document: str
    oci_service_category: str | None = None
    service: str | None = None


class SectionCitation(BaseModel):
    section: str
    sources: list[SectionCitationSource] = Field(default_factory=list)


class RetrievalScoreTrace(BaseModel):
    chunk_id: str
    title: str
    base_score: float
    final_score: float
    adjustments: dict[str, float] = Field(default_factory=dict)


class RetrievalDebugTrace(BaseModel):
    detected_intent: str | None = None
    mapped_oci_services: list[str] = Field(default_factory=list)
    mapped_service_summary: str | None = None
    domain_heuristics: list[str] = Field(default_factory=list)
    retrieved_chunk_ids: list[str] = Field(default_factory=list)
    retrieval_scores: list[RetrievalScoreTrace] = Field(default_factory=list)
    selected_final_chunks: list[str] = Field(default_factory=list)


class SynthesisQualityScore(BaseModel):
    grounding_quality: float
    oci_specificity: float
    workload_alignment: float
    migration_accuracy: float
    recommendation_diversity: float
    citation_coverage: float
    overall: float
    notes: list[str] = Field(default_factory=list)


class ConfidenceScore(BaseModel):
    retrieval: float
    evidence: float
    freshness: float
    release_awareness: float
    recommendation: float
    overall: float
    level: str
    notes: list[str] = Field(default_factory=list)


class AgentTrace(BaseModel):
    agent: str
    role: str
    status: str
    latency_ms: float
    evidence_count: int = 0
    notes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class AgentContribution(BaseModel):
    agent: str
    focus: str
    evidence_count: int
    summary: str
    recommendations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ArchitectureReviewResponse(BaseModel):
    intent: str
    prompt_template: str
    orchestration_mode: str = "single_pass"
    active_agents: list[str] = Field(default_factory=list)
    routing_decision: str | None = None
    agent_trace: list[AgentTrace] = Field(default_factory=list)
    agent_contributions: list[AgentContribution] = Field(default_factory=list)
    aggregation_decision: str | None = None
    critic_findings: list[str] = Field(default_factory=list)
    orchestration_warnings: list[str] = Field(default_factory=list)
    synthesis_provider: str = "deterministic"
    synthesis_model: str | None = None
    synthesis_warnings: list[str] = Field(default_factory=list)
    synthesis_fallback_used: bool = False
    synthesis_quality: SynthesisQualityScore | None = None
    answer: str
    recommendations: list[str]
    assumptions: list[str]
    risks: list[str]
    citations: list[RetrievedSource]
    section_citations: list[SectionCitation] = Field(default_factory=list)
    retrieval_debug: RetrievalDebugTrace | None = None
    evidence_links: list[EvidenceLink] = Field(default_factory=list)
    confidence: ConfidenceScore | None = None
    quality_warnings: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    not_enough_evidence: bool = False
    low_confidence: bool = False
    next_steps: list[str]
