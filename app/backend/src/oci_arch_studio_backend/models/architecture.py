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
    synthesis_debug: bool = Field(
        default=False,
        description="Include backend synthesis grounding diagnostics for provider validation.",
    )
    save_to_history: bool = Field(
        default=True,
        description="Persist a redacted review record for session history.",
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
    source_url: str | None = None
    relevance_score: float | None = None
    trust_level: str | None = None


class SectionCitation(BaseModel):
    section: str
    sources: list[SectionCitationSource] = Field(default_factory=list)
    source_count: int = 0
    traceability_note: str | None = None


class RetrievalScoreTrace(BaseModel):
    chunk_id: str
    title: str
    base_score: float
    final_score: float
    adjustments: dict[str, float] = Field(default_factory=dict)


class RetrievalDebugTrace(BaseModel):
    provider: str | None = None
    detected_intent: str | None = None
    mapped_oci_services: list[str] = Field(default_factory=list)
    mapped_service_summary: str | None = None
    domain_heuristics: list[str] = Field(default_factory=list)
    metadata_filters: dict[str, list[str] | str | bool | None] = Field(default_factory=dict)
    retrieved_chunk_ids: list[str] = Field(default_factory=list)
    retrieved_chunk_diversity: dict[str, int] = Field(default_factory=dict)
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


class SynthesisDebugTrace(BaseModel):
    selected_provider: str
    selected_model: str | None = None
    retrieved_chunk_ids: list[str] = Field(default_factory=list)
    grounding_prompt_sections: list[str] = Field(default_factory=list)
    prompt_char_count: int = 0
    estimated_input_tokens: int = 0
    output_char_count: int = 0
    fallback_used: bool = False
    fallback_reason: str | None = None
    token_usage: dict[str, int] = Field(default_factory=dict)


class ConfidenceScore(BaseModel):
    retrieval: float
    evidence: float
    freshness: float
    release_awareness: float
    recommendation: float
    service_relevance: float = 0.0
    workload_alignment: float = 0.0
    migration_mapping: float = 1.0
    citation_coverage: float = 0.0
    overall: float
    level: str
    notes: list[str] = Field(default_factory=list)


class ArchitectureDecisionReason(BaseModel):
    recommendation: str
    service: str | None = None
    why_chosen: str
    workload_signal: str | None = None
    tradeoffs: list[str] = Field(default_factory=list)
    alternatives_rejected: list[str] = Field(default_factory=list)
    source_chunk_ids: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class ArchitectureTradeoffAnalysis(BaseModel):
    dimension: str
    decision: str
    benefit: str
    cost_or_risk: str
    guidance: str
    source_chunk_ids: list[str] = Field(default_factory=list)


class RecommendationConfidenceIndicator(BaseModel):
    recommendation: str
    score: float
    level: str
    reasoning_basis: str
    source_chunk_ids: list[str] = Field(default_factory=list)
    known_limitations: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class ArchitectureReasoningTrace(BaseModel):
    profile: str
    heuristics_triggered: list[str] = Field(default_factory=list)
    pattern_hints: list[str] = Field(default_factory=list)
    retrieval_terms: list[str] = Field(default_factory=list)
    service_priorities: list[str] = Field(default_factory=list)
    risk_emphasis: list[str] = Field(default_factory=list)
    synthesis_provider: str | None = None


class ArchitectureConsistencyFinding(BaseModel):
    check: str
    severity: str
    message: str
    recommendation: str
    source_chunk_ids: list[str] = Field(default_factory=list)


class GovernanceAnnotation(BaseModel):
    recommendation_index: int | None = None
    control_area: str
    policy_signal: str
    guidance: str
    confidence: float = 0.0
    source_chunk_ids: list[str] = Field(default_factory=list)


class ArchitectureRiskClassification(BaseModel):
    risk_id: str
    level: str
    category: str
    summary: str
    impacted_areas: list[str] = Field(default_factory=list)
    operational_implication: str
    mitigation: str
    source_chunk_ids: list[str] = Field(default_factory=list)


class RecommendationPriority(BaseModel):
    recommendation_index: int
    priority: str
    implementation_phase: str
    rationale: str


class ArchitectureComparison(BaseModel):
    decision: str
    preferred_option: str
    alternatives: list[str] = Field(default_factory=list)
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    governance_implications: list[str] = Field(default_factory=list)
    cost_implications: str
    operational_complexity: str
    source_chunk_ids: list[str] = Field(default_factory=list)


class EnterpriseReviewFinding(BaseModel):
    check: str
    severity: str
    finding: str
    impacted_area: str
    mitigation: str
    source_chunk_ids: list[str] = Field(default_factory=list)


class AuditabilityTrace(BaseModel):
    retrieval_source_chunk_ids: list[str] = Field(default_factory=list)
    reasoning_profile: str | None = None
    heuristics_applied: list[str] = Field(default_factory=list)
    release_influence: list[str] = Field(default_factory=list)
    synthesis_provider: str
    fallback_events: list[str] = Field(default_factory=list)
    confidence_level: str | None = None
    evaluation_signals: dict[str, object] = Field(default_factory=dict)


class ExecutiveAdvisorySummary(BaseModel):
    business_impact: str
    governance_posture: str
    risk_summary: str
    implementation_guidance: str


class EnterpriseGovernanceAssessment(BaseModel):
    maturity_level: str
    executive_summary: ExecutiveAdvisorySummary
    governance_annotations: list[GovernanceAnnotation] = Field(default_factory=list)
    security_posture_checks: list[GovernanceAnnotation] = Field(default_factory=list)
    risk_classifications: list[ArchitectureRiskClassification] = Field(default_factory=list)
    recommendation_priorities: list[RecommendationPriority] = Field(default_factory=list)
    architecture_comparisons: list[ArchitectureComparison] = Field(default_factory=list)
    enterprise_review_findings: list[EnterpriseReviewFinding] = Field(default_factory=list)
    auditability_trace: AuditabilityTrace
    notes: list[str] = Field(default_factory=list)


class ArchitectureTopologyNode(BaseModel):
    node_id: str
    label: str
    service: str | None = None
    category: str | None = None
    role: str
    source_chunk_ids: list[str] = Field(default_factory=list)


class ArchitectureTopologyRelationship(BaseModel):
    from_node: str
    to_node: str
    relationship: str
    rationale: str
    source_chunk_ids: list[str] = Field(default_factory=list)


class ArchitectureTopologySummary(BaseModel):
    topology_summary: str
    deployment_topology: str
    ha_dr_topology: str
    service_dependencies: list[ArchitectureTopologyRelationship] = Field(default_factory=list)
    nodes: list[ArchitectureTopologyNode] = Field(default_factory=list)
    mermaid_flow: str | None = None
    operational_notes: list[str] = Field(default_factory=list)
    source_chunk_ids: list[str] = Field(default_factory=list)


class ExecutiveDecisionBrief(BaseModel):
    title: str
    summary: str
    business_impact: str
    risk_visibility: str
    implementation_priority: str


class ImplementationSequenceItem(BaseModel):
    phase: str
    objective: str
    actions: list[str] = Field(default_factory=list)
    exit_criteria: list[str] = Field(default_factory=list)


class ArchitectureVisualizationSummary(BaseModel):
    topology_summary: str
    dependency_summary: list[str] = Field(default_factory=list)
    deployment_view: str
    ha_dr_view: str
    migration_flow: list[str] = Field(default_factory=list)
    mermaid_flow: str | None = None


class ArchitectureReviewArtifact(BaseModel):
    title: str
    markdown_summary: str
    json_summary: dict[str, object] = Field(default_factory=dict)
    review_checkpoints: list[str] = Field(default_factory=list)


class ExecutiveExperienceSummary(BaseModel):
    executive_summary: str
    decision_brief: list[ExecutiveDecisionBrief] = Field(default_factory=list)
    implementation_sequence: list[ImplementationSequenceItem] = Field(default_factory=list)
    architecture_visualization: ArchitectureVisualizationSummary | None = None
    comparison_summary: list[ArchitectureComparison] = Field(default_factory=list)
    explainability_highlights: list[str] = Field(default_factory=list)
    review_artifacts: list[ArchitectureReviewArtifact] = Field(default_factory=list)


class MigrationPhasePlan(BaseModel):
    phase: str
    objective: str
    actions: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    rollback_considerations: list[str] = Field(default_factory=list)
    readiness_checks: list[str] = Field(default_factory=list)


class ModernizationOption(BaseModel):
    approach: str
    fit: str
    tradeoffs: list[str] = Field(default_factory=list)
    operational_implications: list[str] = Field(default_factory=list)
    readiness_requirements: list[str] = Field(default_factory=list)


class FinOpsRecommendation(BaseModel):
    lever: str
    recommendation: str
    expected_cost_implication: str
    performance_tradeoff: str
    operational_savings: str
    source_chunk_ids: list[str] = Field(default_factory=list)


class WorkloadOptimizationSignal(BaseModel):
    workload: str
    service_priorities: list[str] = Field(default_factory=list)
    scaling_guidance: str
    governance_weighting: str
    cost_performance_tradeoff: str


class OptimizationPlanSummary(BaseModel):
    maturity_level: str
    migration_phases: list[MigrationPhasePlan] = Field(default_factory=list)
    modernization_options: list[ModernizationOption] = Field(default_factory=list)
    finops_recommendations: list[FinOpsRecommendation] = Field(default_factory=list)
    workload_optimization_signals: list[WorkloadOptimizationSignal] = Field(default_factory=list)
    optimization_comparisons: list[ArchitectureComparison] = Field(default_factory=list)
    implementation_readiness: list[str] = Field(default_factory=list)
    recommendation_additions: list[str] = Field(default_factory=list)


class ReleaseImpactSummary(BaseModel):
    snapshot_path: str | None = None
    snapshot_generated_at: str | None = None
    matched_release_count: int = 0
    architecture_affecting_services: list[str] = Field(default_factory=list)
    impact_categories: list[str] = Field(default_factory=list)
    change_categories: list[str] = Field(default_factory=list)
    recommendation_affecting_services: list[str] = Field(default_factory=list)
    maturity_notes: list[str] = Field(default_factory=list)


class KnowledgeTemporalContext(BaseModel):
    knowledge_mode: str = "current_snapshot"
    current_knowledge_snapshot: str | None = None
    current_release_snapshot: str | None = None
    current_knowledge_as_of: str | None = None
    requested_time_context: str | None = None
    historical_snapshots: list[str] = Field(default_factory=list)
    historical_context_available: bool = False
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
    review_id: str | None = None
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
    synthesis_debug: SynthesisDebugTrace | None = None
    decision_reasoning: list[ArchitectureDecisionReason] = Field(default_factory=list)
    reasoning_trace: ArchitectureReasoningTrace | None = None
    architecture_tradeoffs: list[ArchitectureTradeoffAnalysis] = Field(default_factory=list)
    recommendation_confidence: list[RecommendationConfidenceIndicator] = Field(default_factory=list)
    consistency_findings: list[ArchitectureConsistencyFinding] = Field(default_factory=list)
    enterprise_governance: EnterpriseGovernanceAssessment | None = None
    architecture_topology: ArchitectureTopologySummary | None = None
    executive_experience: ExecutiveExperienceSummary | None = None
    optimization_plan: OptimizationPlanSummary | None = None
    release_context: ReleaseImpactSummary | None = None
    knowledge_temporal_context: KnowledgeTemporalContext | None = None
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


class ReviewHistorySummary(BaseModel):
    review_id: str
    created_at: str
    updated_at: str
    question_preview: str
    workload_context_preview: str | None = None
    intent: str
    confidence_level: str | None = None
    confidence_overall: float | None = None
    citation_count: int = 0
    recommendation_count: int = 0


class ReviewHistoryDetail(ReviewHistorySummary):
    question: str
    workload_context: str | None = None
    response: ArchitectureReviewResponse


class ReviewHistoryPolicy(BaseModel):
    retention_limit: int
    storage_scope: str = "backend_file"
    file_mode: str = "0600"
    redaction_enabled: bool = True
    stores_debug_traces: bool = False
    export_scope: str = "redacted_saved_reviews"
    delete_scope: str = "saved_review_history"


class ReviewHistoryListResponse(BaseModel):
    items: list[ReviewHistorySummary] = Field(default_factory=list)
    retention_limit: int
    policy: ReviewHistoryPolicy


class ReviewHistoryExportResponse(BaseModel):
    policy: ReviewHistoryPolicy
    items: list[ReviewHistoryDetail] = Field(default_factory=list)
