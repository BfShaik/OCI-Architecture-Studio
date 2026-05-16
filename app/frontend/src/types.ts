export type RetrievedSource = {
  chunk_id?: string | null;
  title: string;
  source_type: string;
  url?: string | null;
  source_url?: string | null;
  service?: string | null;
  service_domain?: string | null;
  service_category?: string | null;
  category?: string | null;
  pattern?: string | null;
  workload?: string | null;
  workload_types: string[];
  domain?: string | null;
  domain_tags: string[];
  topic?: string | null;
  migration_mappings: Record<string, string>;
  ha_dr_tags: string[];
  cost_optimization_tags: string[];
  intent_tags: string[];
  fetched_timestamp?: string | null;
  freshness_score?: number | null;
  trust_level?: string | null;
  architecture_patterns: string[];
  is_stale: boolean;
  summary: string;
  relevance_score?: number | null;
};

export type EvidenceLink = {
  recommendation_index: number;
  support_level: string;
  source_chunk_ids: string[];
  source_titles: string[];
  rationale: string;
};

export type SectionCitationSource = {
  chunk_id?: string | null;
  source_document: string;
  oci_service_category?: string | null;
  service?: string | null;
  source_url?: string | null;
  relevance_score?: number | null;
  trust_level?: string | null;
};

export type SectionCitation = {
  section: string;
  sources: SectionCitationSource[];
  source_count?: number;
  traceability_note?: string | null;
};

export type RetrievalScoreTrace = {
  chunk_id: string;
  title: string;
  base_score: number;
  final_score: number;
  adjustments: Record<string, number>;
};

export type RetrievalDebugTrace = {
  detected_intent?: string | null;
  mapped_oci_services: string[];
  mapped_service_summary?: string | null;
  domain_heuristics: string[];
  retrieved_chunk_ids: string[];
  retrieval_scores: RetrievalScoreTrace[];
  selected_final_chunks: string[];
};

export type ConfidenceScore = {
  retrieval: number;
  evidence: number;
  freshness: number;
  release_awareness: number;
  recommendation: number;
  service_relevance?: number;
  workload_alignment?: number;
  migration_mapping?: number;
  citation_coverage?: number;
  overall: number;
  level: string;
  notes: string[];
};

export type SynthesisQualityScore = {
  grounding_quality: number;
  oci_specificity: number;
  workload_alignment: number;
  migration_accuracy: number;
  recommendation_diversity: number;
  citation_coverage: number;
  overall: number;
  notes: string[];
};

export type AgentTrace = {
  agent: string;
  role: string;
  status: string;
  latency_ms: number;
  evidence_count: number;
  notes: string[];
  warnings: string[];
};

export type AgentContribution = {
  agent: string;
  focus: string;
  evidence_count: number;
  summary: string;
  recommendations: string[];
  warnings: string[];
};

export type ArchitectureDecisionReason = {
  recommendation: string;
  service?: string | null;
  why_chosen: string;
  workload_signal?: string | null;
  tradeoffs: string[];
  alternatives_rejected: string[];
  source_chunk_ids: string[];
  confidence: number;
};

export type ArchitectureTradeoffAnalysis = {
  dimension: string;
  decision: string;
  benefit: string;
  cost_or_risk: string;
  guidance: string;
  source_chunk_ids: string[];
};

export type RecommendationConfidenceIndicator = {
  recommendation: string;
  score: number;
  level: string;
  reasoning_basis: string;
  source_chunk_ids: string[];
  known_limitations: string[];
  assumptions: string[];
};

export type ArchitectureComparison = {
  decision: string;
  preferred_option: string;
  alternatives: string[];
  pros: string[];
  cons: string[];
  governance_implications: string[];
  cost_implications: string;
  operational_complexity: string;
  source_chunk_ids: string[];
};

export type RecommendationPriority = {
  recommendation_index: number;
  priority: string;
  implementation_phase: string;
  rationale: string;
};

export type ExecutiveAdvisorySummary = {
  business_impact: string;
  governance_posture: string;
  risk_summary: string;
  implementation_guidance: string;
};

export type EnterpriseGovernanceAssessment = {
  maturity_level: string;
  executive_summary: ExecutiveAdvisorySummary;
  recommendation_priorities: RecommendationPriority[];
  architecture_comparisons: ArchitectureComparison[];
  notes: string[];
};

export type ArchitectureTopologyNode = {
  node_id: string;
  label: string;
  service?: string | null;
  category?: string | null;
  role: string;
  source_chunk_ids: string[];
};

export type ArchitectureTopologyRelationship = {
  from_node: string;
  to_node: string;
  relationship: string;
  rationale: string;
  source_chunk_ids: string[];
};

export type ArchitectureTopologySummary = {
  topology_summary: string;
  deployment_topology: string;
  ha_dr_topology: string;
  service_dependencies: ArchitectureTopologyRelationship[];
  nodes: ArchitectureTopologyNode[];
  mermaid_flow?: string | null;
  operational_notes: string[];
  source_chunk_ids: string[];
};

export type ExecutiveDecisionBrief = {
  title: string;
  summary: string;
  business_impact: string;
  risk_visibility: string;
  implementation_priority: string;
};

export type ImplementationSequenceItem = {
  phase: string;
  objective: string;
  actions: string[];
  exit_criteria: string[];
};

export type ArchitectureVisualizationSummary = {
  topology_summary: string;
  dependency_summary: string[];
  deployment_view: string;
  ha_dr_view: string;
  migration_flow: string[];
  mermaid_flow?: string | null;
};

export type ArchitectureReviewArtifact = {
  title: string;
  markdown_summary: string;
  json_summary: Record<string, unknown>;
  review_checkpoints: string[];
};

export type ExecutiveExperienceSummary = {
  executive_summary: string;
  decision_brief: ExecutiveDecisionBrief[];
  implementation_sequence: ImplementationSequenceItem[];
  architecture_visualization?: ArchitectureVisualizationSummary | null;
  comparison_summary: ArchitectureComparison[];
  explainability_highlights: string[];
  review_artifacts: ArchitectureReviewArtifact[];
};

export type MigrationPhasePlan = {
  phase: string;
  objective: string;
  actions: string[];
  dependencies: string[];
  rollback_considerations: string[];
  readiness_checks: string[];
};

export type ModernizationOption = {
  approach: string;
  fit: string;
  tradeoffs: string[];
  operational_implications: string[];
  readiness_requirements: string[];
};

export type FinOpsRecommendation = {
  lever: string;
  recommendation: string;
  expected_cost_implication: string;
  performance_tradeoff: string;
  operational_savings: string;
  source_chunk_ids: string[];
};

export type WorkloadOptimizationSignal = {
  workload: string;
  service_priorities: string[];
  scaling_guidance: string;
  governance_weighting: string;
  cost_performance_tradeoff: string;
};

export type OptimizationPlanSummary = {
  maturity_level: string;
  migration_phases: MigrationPhasePlan[];
  modernization_options: ModernizationOption[];
  finops_recommendations: FinOpsRecommendation[];
  workload_optimization_signals: WorkloadOptimizationSignal[];
  optimization_comparisons: ArchitectureComparison[];
  implementation_readiness: string[];
  recommendation_additions: string[];
};

export type ReleaseImpactSummary = {
  snapshot_path?: string | null;
  snapshot_generated_at?: string | null;
  matched_release_count: number;
  architecture_affecting_services: string[];
  impact_categories: string[];
  change_categories: string[];
  recommendation_affecting_services: string[];
  maturity_notes: string[];
};

export type KnowledgeTemporalContext = {
  knowledge_mode: string;
  current_knowledge_snapshot?: string | null;
  current_release_snapshot?: string | null;
  current_knowledge_as_of?: string | null;
  requested_time_context?: string | null;
  historical_snapshots: string[];
  historical_context_available: boolean;
  notes: string[];
};

export type ArchitectureReviewRequest = {
  question: string;
  workload_context?: string;
  retrieval_debug?: boolean;
  save_to_history?: boolean;
};

export type KnowledgeRefreshLifecycle = {
  candidate_created?: boolean;
  candidate_changed?: boolean;
  gates_run?: boolean;
  gates_passed?: boolean;
  promoted?: boolean;
  promotion_status?: string;
  authoritative_snapshots_updated?: boolean;
  oci_upload_requested?: boolean;
  oci_upload_performed?: boolean;
  oci_upload_status?: string;
  rollback_available?: boolean;
  rollback_performed?: boolean;
  query_time_refresh?: boolean;
  selective_reindex?: boolean;
  full_reindex?: boolean;
};

export type KnowledgeRefreshRun = {
  run_id?: string;
  status?: string;
  passed?: boolean;
  started_at?: string;
  generated_at?: string;
  changed_release_count?: number;
  affected_source_ids?: string[];
  gates_passed?: boolean;
  rollback_performed?: boolean;
  lifecycle?: KnowledgeRefreshLifecycle;
};

export type KnowledgeRefreshSnapshot = {
  run_id?: string;
  started_at?: string;
  generated_at?: string;
  policy_version?: string;
  mode?: string;
  refresh_reason?: string;
  status?: string;
  lineage?: {
    knowledge_snapshot_version?: string;
    release_snapshot_version?: string;
    embedding_version?: string;
    embedding_provider?: string;
    metadata_schema_version?: string;
    affected_source_ids?: string[];
    changed_release_ids?: string[];
    impacted_eval_cases?: string[];
  };
};

export type KnowledgeRefreshStatus = {
  status?: string;
  status_path?: string;
  generated_at?: string;
  last_run?: KnowledgeRefreshRun | null;
  current_promoted_snapshot?: KnowledgeRefreshSnapshot | null;
};

export type RetrievalStoreHealth = {
  provider?: string;
  exists?: boolean;
  chunk_count?: number;
  service_count?: number;
  service_domain_count?: number;
  index_path?: string;
  namespace?: string;
  bucket?: string;
  object_name?: string;
  fallback_enabled?: boolean;
  fallback_active?: boolean;
  fallback_reason?: string | null;
  primary?: RetrievalStoreHealth;
  fallback?: RetrievalStoreHealth;
  read_enabled?: boolean;
  table_name?: string;
  index_name?: string;
  expected_dimensions?: number;
  missing_config?: string[];
  schema?: {
    configured?: boolean;
    valid?: boolean;
  };
  last_error?: string | null;
};

export type RetrievalHealth = {
  provider?: string;
  embedding_model?: string;
  embedding_provider?: string;
  store?: RetrievalStoreHealth;
  metrics?: {
    request_count?: number;
    missing_index_count?: number;
    no_result_count?: number;
    average_latency_ms?: number;
    average_embedding_latency_ms?: number;
    last_latency_ms?: number | null;
    last_embedding_latency_ms?: number | null;
    last_result_count?: number;
    last_provider?: string;
    last_embedding_model?: string;
    last_intent?: string | null;
    warnings?: string[];
  };
};

export type ArchitectureReviewResponse = {
  review_id?: string | null;
  intent: string;
  prompt_template: string;
  orchestration_mode: string;
  active_agents: string[];
  routing_decision?: string | null;
  agent_trace: AgentTrace[];
  agent_contributions: AgentContribution[];
  aggregation_decision?: string | null;
  critic_findings: string[];
  orchestration_warnings: string[];
  synthesis_provider: string;
  synthesis_model?: string | null;
  synthesis_warnings: string[];
  synthesis_fallback_used: boolean;
  synthesis_quality?: SynthesisQualityScore | null;
  decision_reasoning: ArchitectureDecisionReason[];
  architecture_tradeoffs: ArchitectureTradeoffAnalysis[];
  recommendation_confidence: RecommendationConfidenceIndicator[];
  enterprise_governance?: EnterpriseGovernanceAssessment | null;
  architecture_topology?: ArchitectureTopologySummary | null;
  executive_experience?: ExecutiveExperienceSummary | null;
  optimization_plan?: OptimizationPlanSummary | null;
  release_context?: ReleaseImpactSummary | null;
  knowledge_temporal_context?: KnowledgeTemporalContext | null;
  answer: string;
  recommendations: string[];
  assumptions: string[];
  risks: string[];
  citations: RetrievedSource[];
  section_citations: SectionCitation[];
  retrieval_debug?: RetrievalDebugTrace | null;
  evidence_links: EvidenceLink[];
  confidence?: ConfidenceScore | null;
  quality_warnings: string[];
  unsupported_claims: string[];
  not_enough_evidence: boolean;
  low_confidence: boolean;
  next_steps: string[];
};

export type ReviewHistorySummary = {
  review_id: string;
  created_at: string;
  updated_at: string;
  question_preview: string;
  workload_context_preview?: string | null;
  intent: string;
  confidence_level?: string | null;
  confidence_overall?: number | null;
  citation_count: number;
  recommendation_count: number;
};

export type ReviewHistoryDetail = ReviewHistorySummary & {
  question: string;
  workload_context?: string | null;
  response: ArchitectureReviewResponse;
};

export type ReviewHistoryListResponse = {
  items: ReviewHistorySummary[];
  retention_limit: number;
};
