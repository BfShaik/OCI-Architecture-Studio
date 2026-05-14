import { FormEvent, useState } from "react";
import { Send } from "lucide-react";
import { ReviewResult } from "./components/ReviewResult";
import { requestArchitectureReview } from "./lib/api";
import type { ArchitectureReviewResponse } from "./types";

const starterQuestion =
  "How should I design a highly available customer portal on OCI?";

export function App() {
  const [question, setQuestion] = useState(starterQuestion);
  const [workloadContext, setWorkloadContext] = useState("");
  const [result, setResult] = useState<ArchitectureReviewResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const response = await requestArchitectureReview({
        question,
        workload_context: workloadContext || undefined,
      });
      setResult(response);
    } catch (caught) {
      const message =
        caught instanceof Error ? caught.message : "Unable to request review.";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">OCI Architecture Studio</p>
          <h1>Architecture Advisor</h1>
          <p className="lede">
            Ask an OCI design question and receive a structured, review-ready
            response from the first vertical slice.
          </p>
        </div>
      </aside>

      <section className="workspace">
        <div className="conversation">
          <div className="message message-system">
            <span>System</span>
            <p>
              Retrieval and prompt orchestration are scaffolded placeholders.
              Production grounding will be added behind these service boundaries.
            </p>
          </div>

          {result ? (
            <ReviewResult result={result} />
          ) : (
            <div className="empty-state">
              <h2>Ready for the first OCI architecture question.</h2>
              <p>
                The response will include recommendations, assumptions, risks,
                placeholder citations, and next steps.
              </p>
            </div>
          )}

          {error ? <div className="error-state">{error}</div> : null}
        </div>

        <form className="composer" onSubmit={handleSubmit}>
          <label htmlFor="question">Architecture question</label>
          <textarea
            id="question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            rows={3}
            minLength={3}
            required
          />

          <label htmlFor="context">Workload context</label>
          <textarea
            id="context"
            value={workloadContext}
            onChange={(event) => setWorkloadContext(event.target.value)}
            rows={2}
            placeholder="Optional: compliance, traffic, availability, budget, migration constraints"
          />

          <button type="submit" disabled={isLoading}>
            <Send size={18} aria-hidden="true" />
            {isLoading ? "Reviewing" : "Request Review"}
          </button>
        </form>
      </section>
    </main>
  );
}
