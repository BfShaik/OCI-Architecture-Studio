import { FormEvent, useState } from "react";
import { Send } from "lucide-react";
import { ReviewResult } from "./components/ReviewResult";
import { requestArchitectureReview } from "./lib/api";
import type { ArchitectureReviewResponse } from "./types";

const starterQuestion =
  "How should I design a highly available customer portal on OCI?";

const demoPrompts = [
  "Design a highly available ecommerce platform on OCI.",
  "Migrate EKS + RDS to OCI.",
  "Recommend OCI services for fintech DR.",
  "Build a cost-optimized web app on OCI.",
  "A new OCI Object Storage release was announced. Does it change my architecture?",
];

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
            response with grounded evidence and confidence signals.
          </p>
          <div className="demo-prompts" aria-label="Demo prompts">
            {demoPrompts.map((prompt) => (
              <button
                key={prompt}
                type="button"
                className="prompt-chip"
                onClick={() => {
                  setQuestion(prompt);
                  setWorkloadContext("");
                  setError(null);
                }}
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
      </aside>

      <section className="workspace">
        <div className="conversation">
          <div className="message message-system">
            <span>System</span>
            <p>
              Retrieval uses the configured OCI knowledge provider with citation
              metadata, evidence links, confidence scoring, and release freshness
              signals.
            </p>
          </div>

          {result ? (
            <ReviewResult result={result} />
          ) : isLoading ? (
            <div className="loading-state" role="status">
              <span>Retrieving OCI context</span>
              <p>Classifying intent, ranking sources, and preparing citations.</p>
            </div>
          ) : (
            <div className="empty-state">
              <h2>Ready for the first OCI architecture question.</h2>
              <p>
                The response will include recommendations, assumptions, risks,
                citation metadata, freshness signals, and next steps.
              </p>
            </div>
          )}

          {error ? (
            <div className="error-state" role="alert">
              <strong>Review failed</strong>
              <p>{error}</p>
            </div>
          ) : null}
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
