import type {
  ArchitectureReviewRequest,
  ArchitectureReviewResponse,
} from "../types";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

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
