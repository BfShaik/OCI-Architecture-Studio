export type RetrievedSource = {
  chunk_id?: string | null;
  title: string;
  source_type: string;
  url?: string | null;
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
