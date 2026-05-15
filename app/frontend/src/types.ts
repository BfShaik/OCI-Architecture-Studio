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
};

export type SectionCitation = {
  section: string;
  sources: SectionCitationSource[];
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

export type ArchitectureReviewRequest = {
  question: string;
  workload_context?: string;
  retrieval_debug?: boolean;
};

export type ArchitectureReviewResponse = {
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
