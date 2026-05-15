import type { ArchitectureReviewResponse } from "../types";

type ReviewResultProps = {
  result: ArchitectureReviewResponse;
};

function Section({ title, items }: { title: string; items: string[] }) {
  return (
    <section className="result-section">
      <h3>{title}</h3>
      <ul>
        {items.map((item, index) => (
          <li key={`${title}-${index}-${item}`}>{item}</li>
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

function readable(value: string) {
  return value.replace(/_/g, " ");
}

function answerSections(answer: string) {
  const sections = answer
    .split(/\n(?=\d+\.\s)/g)
    .map((section) => section.trim())
    .filter(Boolean);
  return sections.length > 1 ? sections : [answer];
}

function downloadMarkdown(title: string, markdown: string) {
  const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${title.toLowerCase().replace(/[^a-z0-9]+/g, "-")}.md`;
  link.click();
  URL.revokeObjectURL(url);
}

export function ReviewResult({ result }: ReviewResultProps) {
  const citationCount = result.citations.length;
  const confidence = result.confidence;
  const experience = result.executive_experience;
  const visualization = experience?.architecture_visualization;
  const reviewArtifact = experience?.review_artifacts[0];
  const optimization = result.optimization_plan;

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
        {experience ? <p className="executive-summary">{experience.executive_summary}</p> : null}
        <div className="answer-sections">
          {answerSections(result.answer).slice(0, 4).map((section, index) => (
            <p key={`answer-${index}`}>{section}</p>
          ))}
        </div>
        {result.quality_warnings.length ||
        result.synthesis_warnings.length ||
        result.orchestration_warnings.length ? (
          <div className="quality-warnings" aria-label="Quality warnings">
            {[...result.quality_warnings, ...result.synthesis_warnings, ...result.orchestration_warnings].map((warning, index) => (
              <span key={`warning-${index}-${warning}`}>{warning}</span>
            ))}
          </div>
        ) : null}
      </section>

      {experience ? (
        <section className="result-section executive-brief">
          <div className="section-heading-row">
            <div>
              <h3>Executive Brief</h3>
              <p>Review-ready decisions, implementation order, and governance context.</p>
            </div>
            {reviewArtifact ? (
              <button
                type="button"
                className="secondary-action"
                onClick={() => downloadMarkdown(reviewArtifact.title, reviewArtifact.markdown_summary)}
              >
                Export Markdown
              </button>
            ) : null}
          </div>
          <div className="decision-grid">
            {experience.decision_brief.map((decision, index) => (
              <article key={`decision-${index}`}>
                <span>{readable(decision.implementation_priority)}</span>
                <h4>{decision.summary}</h4>
                <p>{decision.business_impact}</p>
                <small>{decision.risk_visibility}</small>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {experience?.implementation_sequence.length ? (
        <section className="result-section sequence-panel">
          <h3>Implementation Sequence</h3>
          <div className="sequence-list">
            {experience.implementation_sequence.map((phase) => (
              <article key={phase.phase}>
                <strong>{phase.phase}</strong>
                <p>{phase.objective}</p>
                <ul>
                  {phase.actions.slice(0, 3).map((action, index) => (
                    <li key={`${phase.phase}-action-${index}`}>{action}</li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {visualization ? (
        <section className="result-section topology-panel">
          <h3>Architecture View</h3>
          <div className="topology-grid">
            <div>
              <h4>Topology</h4>
              <p>{visualization.topology_summary}</p>
            </div>
            <div>
              <h4>Deployment</h4>
              <p>{visualization.deployment_view}</p>
            </div>
            <div>
              <h4>HA/DR</h4>
              <p>{visualization.ha_dr_view}</p>
            </div>
          </div>
          {visualization.dependency_summary.length ? (
            <div className="dependency-flow">
              {visualization.dependency_summary.slice(0, 6).map((dependency, index) => (
                <span key={`dependency-${index}`}>{dependency}</span>
              ))}
            </div>
          ) : null}
          {visualization.migration_flow.length ? (
            <ol className="migration-flow">
              {visualization.migration_flow.map((step, index) => (
                <li key={`flow-${index}-${step}`}>{step}</li>
              ))}
            </ol>
          ) : null}
        </section>
      ) : null}

      {experience?.comparison_summary.length ? (
        <section className="result-section comparison-panel">
          <h3>Decision Comparisons</h3>
          <div className="comparison-list">
            {experience.comparison_summary.map((comparison, index) => (
              <article key={`comparison-${index}-${comparison.decision}`}>
                <div>
                  <strong>{comparison.decision}</strong>
                  <span>Prefer {comparison.preferred_option}</span>
                </div>
                <p>{comparison.operational_complexity}</p>
                <p>{comparison.cost_implications}</p>
                {comparison.governance_implications.length ? (
                  <small>{comparison.governance_implications.slice(0, 2).join(" ")}</small>
                ) : null}
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {optimization ? (
        <section className="result-section optimization-panel">
          <div className="section-heading-row">
            <div>
              <h3>Migration & FinOps Optimization</h3>
              <p>{readable(optimization.maturity_level)}</p>
            </div>
          </div>
          {optimization.migration_phases.length ? (
            <div className="optimization-subsection">
              <h4>Migration Phases</h4>
              <div className="sequence-list">
                {optimization.migration_phases.map((phase) => (
                  <article key={phase.phase}>
                    <strong>{phase.phase}</strong>
                    <p>{phase.objective}</p>
                    <ul>
                      {phase.readiness_checks.slice(0, 2).map((check, index) => (
                        <li key={`${phase.phase}-check-${index}`}>{check}</li>
                      ))}
                    </ul>
                  </article>
                ))}
              </div>
            </div>
          ) : null}
          {optimization.finops_recommendations.length ? (
            <div className="optimization-subsection">
              <h4>FinOps Levers</h4>
              <div className="comparison-list">
                {optimization.finops_recommendations.slice(0, 4).map((item) => (
                  <article key={item.lever}>
                    <div>
                      <strong>{item.lever}</strong>
                      <span>Cost control</span>
                    </div>
                    <p>{item.recommendation}</p>
                    <small>{item.expected_cost_implication}</small>
                  </article>
                ))}
              </div>
            </div>
          ) : null}
          {optimization.workload_optimization_signals.length ? (
            <div className="optimization-subsection">
              <h4>Workload Optimization</h4>
              <div className="topology-grid">
                {optimization.workload_optimization_signals.map((signal) => (
                  <div key={signal.workload}>
                    <h4>{signal.workload}</h4>
                    <p>{signal.scaling_guidance}</p>
                    <small>{signal.cost_performance_tradeoff}</small>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
          {optimization.implementation_readiness.length ? (
            <ul>
              {optimization.implementation_readiness.map((item, index) => (
                <li key={`readiness-${index}`}>{item}</li>
              ))}
            </ul>
          ) : null}
        </section>
      ) : null}

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
              {result.critic_findings.map((finding, index) => (
                <li key={`critic-${index}-${finding}`}>{finding}</li>
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
            {typeof confidence.citation_coverage === "number" ? (
              <span>Citations {percent(confidence.citation_coverage)}</span>
            ) : null}
          </div>
          {confidence.notes.length ? (
            <ul>
              {confidence.notes.map((note, index) => (
                <li key={`confidence-note-${index}-${note}`}>{note}</li>
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

      {experience?.explainability_highlights.length || result.decision_reasoning.length ? (
        <section className="result-section explainability-panel">
          <h3>Why This Recommendation</h3>
          {experience?.explainability_highlights.length ? (
            <ul>
              {experience.explainability_highlights.map((highlight, index) => (
                <li key={`highlight-${index}`}>{highlight}</li>
              ))}
            </ul>
          ) : null}
          {result.decision_reasoning.length ? (
            <div className="reasoning-list">
              {result.decision_reasoning.slice(0, 4).map((reason) => (
                <article key={`${reason.recommendation}-${reason.why_chosen}`}>
                  <strong>{reason.service ?? "Architecture decision"}</strong>
                  <p>{reason.why_chosen}</p>
                  {reason.alternatives_rejected.length ? (
                    <small>Alternatives: {reason.alternatives_rejected.slice(0, 2).join("; ")}</small>
                  ) : null}
                </article>
              ))}
            </div>
          ) : null}
        </section>
      ) : null}

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
        {result.citations.map((source, index) => (
          <article key={`${source.chunk_id ?? source.title}-${index}`} className="source-item">
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
