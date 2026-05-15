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
  overall: number;
  level: string;
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
