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

export type ArchitectureReviewRequest = {
  question: string;
  workload_context?: string;
};

export type ArchitectureReviewResponse = {
  intent: string;
  prompt_template: string;
  answer: string;
  recommendations: string[];
  assumptions: string[];
  risks: string[];
  citations: RetrievedSource[];
  next_steps: string[];
};
