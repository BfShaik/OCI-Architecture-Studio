export type RetrievedSource = {
  chunk_id?: string | null;
  title: string;
  source_type: string;
  url?: string | null;
  source_url?: string | null;
  service?: string | null;
  service_domain?: string | null;
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

export type ArchitectureReviewRequest = {
  question: string;
  workload_context?: string;
};

export type ArchitectureReviewResponse = {
  intent: string;
  prompt_template: string;
  synthesis_provider: string;
  synthesis_model?: string | null;
  synthesis_warnings: string[];
  synthesis_fallback_used: boolean;
  answer: string;
  recommendations: string[];
  assumptions: string[];
  risks: string[];
  citations: RetrievedSource[];
  evidence_links: EvidenceLink[];
  confidence?: ConfidenceScore | null;
  quality_warnings: string[];
  unsupported_claims: string[];
  not_enough_evidence: boolean;
  low_confidence: boolean;
  next_steps: string[];
};
