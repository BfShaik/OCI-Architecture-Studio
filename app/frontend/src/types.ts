export type RetrievedSource = {
  title: string;
  source_type: string;
  url?: string | null;
  summary: string;
};

export type ArchitectureReviewRequest = {
  question: string;
  workload_context?: string;
};

export type ArchitectureReviewResponse = {
  answer: string;
  recommendations: string[];
  assumptions: string[];
  risks: string[];
  citations: RetrievedSource[];
  next_steps: string[];
};
