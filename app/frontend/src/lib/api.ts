import type {
  ArchitectureReviewRequest,
  ArchitectureReviewResponse,
  KnowledgeRefreshStatus,
  ReviewHistoryDetail,
  ReviewHistoryListResponse,
  RetrievalHealth,
} from "../types";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  (window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1"
    ? "http://localhost:8000"
    : window.location.origin);

export async function requestArchitectureReview(
  payload: ArchitectureReviewRequest,
): Promise<ArchitectureReviewResponse> {
  const response = await fetch(`${API_BASE_URL}/architecture-review`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Architecture review failed: ${response.status}`);
  }

  return response.json();
}

export async function requestKnowledgeRefreshStatus(): Promise<KnowledgeRefreshStatus> {
  const response = await fetch(`${API_BASE_URL}/knowledge/refresh/status`);

  if (!response.ok) {
    throw new Error(`Knowledge refresh status failed: ${response.status}`);
  }

  return response.json();
}

export async function requestRetrievalHealth(): Promise<RetrievalHealth> {
  const response = await fetch(`${API_BASE_URL}/retrieval/health`);

  if (!response.ok) {
    throw new Error(`Retrieval health failed: ${response.status}`);
  }

  return response.json();
}

export async function requestReviewHistory(): Promise<ReviewHistoryListResponse> {
  const response = await fetch(`${API_BASE_URL}/review-history`);

  if (!response.ok) {
    throw new Error(`Review history failed: ${response.status}`);
  }

  return response.json();
}

export async function requestReviewHistoryDetail(
  reviewId: string,
): Promise<ReviewHistoryDetail> {
  const response = await fetch(`${API_BASE_URL}/review-history/${reviewId}`);

  if (!response.ok) {
    throw new Error(`Review history item failed: ${response.status}`);
  }

  return response.json();
}

export async function deleteReviewHistoryItem(reviewId: string): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/review-history/${reviewId}/delete`,
    {
      method: "POST",
    },
  );

  if (!response.ok) {
    throw new Error(`Delete history item failed: ${response.status}`);
  }
}
