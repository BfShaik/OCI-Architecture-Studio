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

function percent(value: number) {
  return `${Math.round(value * 100)}%`;
}

export function ReviewResult({ result }: ReviewResultProps) {
  const citationCount = result.citations.length;
  const confidence = result.confidence;

  return (
    <div className="review-result">
      <section className="answer-block">
        <h2>Architecture Review</h2>
        <div className="intent-row">
          <span className="intent-badge">{labelForIntent(result.intent)}</span>
          <span>{citationCount} sources</span>
          <span>
            synthesis {result.synthesis_provider}
            {result.synthesis_fallback_used ? " fallback" : ""}
          </span>
          <span>orchestration {result.orchestration_mode}</span>
          {confidence ? (
            <span className={`confidence-badge confidence-${confidence.level}`}>
              confidence {confidence.level} · {percent(confidence.overall)}
            </span>
          ) : null}
          {result.not_enough_evidence ? <span className="warning-pill">needs evidence</span> : null}
          <span>{result.prompt_template}</span>
        </div>
        <p>{result.answer}</p>
        {result.quality_warnings.length ||
        result.synthesis_warnings.length ||
        result.orchestration_warnings.length ? (
          <div className="quality-warnings" aria-label="Quality warnings">
            {[...result.quality_warnings, ...result.synthesis_warnings, ...result.orchestration_warnings].map((warning) => (
              <span key={warning}>{warning}</span>
            ))}
          </div>
        ) : null}
      </section>

      {result.active_agents.length || result.critic_findings.length ? (
        <section className="result-section orchestration-panel">
          <h3>Controlled Orchestration</h3>
          {result.routing_decision ? <p>{result.routing_decision}</p> : null}
          {result.aggregation_decision ? <p>{result.aggregation_decision}</p> : null}
          {result.active_agents.length ? (
            <div className="agent-row">
              {result.active_agents.map((agent) => (
                <span key={agent}>{agent.replace(/_/g, " ")}</span>
              ))}
            </div>
          ) : null}
          {result.agent_contributions.length ? (
            <div className="agent-contributions">
              {result.agent_contributions.map((contribution) => (
                <article key={contribution.agent}>
                  <strong>{contribution.agent.replace(/_/g, " ")}</strong>
                  <span>{contribution.evidence_count} evidence chunks</span>
                  <p>{contribution.summary}</p>
                </article>
              ))}
            </div>
          ) : null}
          {result.critic_findings.length ? (
            <ul>
              {result.critic_findings.map((finding) => (
                <li key={finding}>{finding}</li>
              ))}
            </ul>
          ) : null}
        </section>
      ) : null}

      {confidence ? (
        <section className="result-section confidence-panel">
          <h3>Confidence</h3>
          <div className="confidence-grid">
            <span>Retrieval {percent(confidence.retrieval)}</span>
            <span>Evidence {percent(confidence.evidence)}</span>
            <span>Freshness {percent(confidence.freshness)}</span>
            <span>Release {percent(confidence.release_awareness)}</span>
            <span>Recommendation {percent(confidence.recommendation)}</span>
          </div>
          {confidence.notes.length ? (
            <ul>
              {confidence.notes.map((note) => (
                <li key={note}>{note}</li>
              ))}
            </ul>
          ) : null}
        </section>
      ) : null}

      <div className="result-grid">
        <Section title="Recommendations" items={result.recommendations} />
        <Section title="Assumptions" items={result.assumptions} />
        <Section title="Risks" items={result.risks} />
        <Section title="Next Steps" items={result.next_steps} />
      </div>

      {result.evidence_links.length ? (
        <section className="result-section evidence-links">
          <h3>Evidence Links</h3>
          {result.evidence_links.map((link) => (
            <article key={`${link.recommendation_index}-${link.support_level}`}>
              <strong>
                Recommendation {link.recommendation_index + 1}: {link.support_level}
              </strong>
              <p>{link.rationale}</p>
            </article>
          ))}
        </section>
      ) : null}

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
