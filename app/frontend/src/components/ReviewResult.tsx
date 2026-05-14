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

function labelForIntent(intent: string) {
  return intent.replace(/_/g, " ");
}

export function ReviewResult({ result }: ReviewResultProps) {
  const citationCount = result.citations.length;

  return (
    <div className="review-result">
      <section className="answer-block">
        <h2>Architecture Review</h2>
        <div className="intent-row">
          <span className="intent-badge">{labelForIntent(result.intent)}</span>
          <span>{citationCount} sources</span>
          <span>{result.prompt_template}</span>
        </div>
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
          <article key={source.chunk_id ?? source.title} className="source-item">
            <div>
              <strong>{source.title}</strong>
              {source.service ? <span>{source.service}</span> : null}
              {source.service_domain ? <span>{source.service_domain}</span> : null}
              <span>
                {source.source_type}
                {typeof source.relevance_score === "number"
                  ? ` · ${source.relevance_score.toFixed(2)}`
                  : ""}
              </span>
              {typeof source.freshness_score === "number" ? (
                <span>freshness {source.freshness_score.toFixed(2)}</span>
              ) : null}
              {source.trust_level ? <span>{source.trust_level}</span> : null}
              {source.is_stale ? <span className="warning-pill">stale</span> : null}
            </div>
            {source.intent_tags.length || source.architecture_patterns.length ? (
              <div className="source-tags">
                {source.intent_tags.slice(0, 4).map((tag) => (
                  <span key={`${source.chunk_id}-intent-${tag}`}>{tag}</span>
                ))}
                {source.architecture_patterns.slice(0, 3).map((pattern) => (
                  <span key={`${source.chunk_id}-pattern-${pattern}`}>{pattern}</span>
                ))}
              </div>
            ) : null}
            <p>{source.summary}</p>
            {source.source_url ? (
              <a href={source.source_url} target="_blank" rel="noreferrer">
                Open source
              </a>
            ) : null}
          </article>
        ))}
      </section>
    </div>
  );
}
