import type { ArchitectureReviewResponse } from "../types";

type ReviewResultProps = {
  result: ArchitectureReviewResponse;
};

function Section({ title, items }: { title: string; items: string[] }) {
  return (
    <section className="result-section">
      <h3>{title}</h3>
      <ul>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

export function ReviewResult({ result }: ReviewResultProps) {
  return (
    <div className="review-result">
      <section className="answer-block">
        <h2>Architecture Review</h2>
        <p>{result.answer}</p>
      </section>

      <div className="result-grid">
        <Section title="Recommendations" items={result.recommendations} />
        <Section title="Assumptions" items={result.assumptions} />
        <Section title="Risks" items={result.risks} />
        <Section title="Next Steps" items={result.next_steps} />
      </div>

      <section className="result-section citations">
        <h3>Sources</h3>
        {result.citations.map((source) => (
          <article key={source.title} className="source-item">
            <div>
              <strong>{source.title}</strong>
              <span>{source.source_type}</span>
            </div>
            <p>{source.summary}</p>
          </article>
        ))}
      </section>
    </div>
  );
}
