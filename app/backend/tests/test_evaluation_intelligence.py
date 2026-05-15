from oci_arch_studio_backend.services.evaluation_intelligence import (
    ArchitectureQualityScorer,
    HallucinationDetector,
    QualityGateEvaluator,
    QualityGateThresholds,
    ResponseQualityAnalytics,
)


def _response() -> dict:
    return {
        "intent": "dr",
        "answer": (
            "1. Executive Summary\nDesign fintech DR with RTO/RPO tiers.\n"
            "2. Recommended OCI Services\nUse Vault, Database Services, Logging, Monitoring, Object Storage.\n"
            "3. Reference Architecture\nPrivate network tiers with validated failover.\n"
            "4. HA/DR Design\nBackups, replication, failover runbooks, and return-to-primary testing.\n"
            "5. Security Considerations\nIAM, Vault, encryption, audit, and least privilege.\n"
            "6. Cost Optimization\nUse tiered resilience and lifecycle controls.\n"
            "7. Risks & Assumptions\nReplication lag and key access need validation.\n"
            "8. Migration Strategy\nUse migration waves, validation, cutover, and rollback.\n"
            "9. Observability\nLogging, Monitoring, metrics, alarms, and dashboards.\n"
            "10. Recommended Next Steps\nRun DR tests and confirm ownership."
        ),
        "recommendations": [
            "Use Vault, Database Services, Logging, and Monitoring for regulated DR. Evidence: OCI Vault.",
            "Use migration waves with validation, cutover, and rollback. Evidence: OCI Database Migration.",
        ],
        "citations": [
            {
                "chunk_id": "vault::1",
                "title": "OCI Vault",
                "url": "https://example.com/vault",
                "summary": "Vault supports key management.",
                "service": "Vault",
                "service_domain": "security",
            },
            {
                "chunk_id": "monitoring::1",
                "title": "OCI Monitoring",
                "url": "https://example.com/monitoring",
                "summary": "Monitoring supports metrics and alarms.",
                "service": "Monitoring",
                "service_domain": "observability",
            },
        ],
        "evidence_links": [
            {"support_level": "strong", "source_chunk_ids": ["vault::1"], "source_titles": ["OCI Vault"]},
            {"support_level": "partial", "source_chunk_ids": ["monitoring::1"], "source_titles": ["OCI Monitoring"]},
        ],
        "confidence": {"evidence": 0.8, "citation_coverage": 1.0, "migration_mapping": 0.85},
        "decision_reasoning": [
            {
                "recommendation": "Use Vault.",
                "why_chosen": "Matches fintech security.",
                "tradeoffs": ["Improves security with operational ownership."],
            }
        ],
        "reasoning_trace": {
            "profile": "fintech_workload",
            "pattern_hints": ["active-passive-dr"],
            "service_priorities": ["Vault", "Database Services"],
        },
        "architecture_tradeoffs": [
            {
                "dimension": "cost_vs_resilience",
                "decision": "Tier resilience.",
                "benefit": "Improves recovery.",
                "cost_or_risk": "Adds cost.",
                "guidance": "Use tiered resilience.",
            }
        ],
        "consistency_findings": [],
    }


def test_architecture_quality_scoring_is_multidimensional() -> None:
    quality = ArchitectureQualityScorer().score(
        _response(),
        {
            "prompt": "Design regulated fintech DR.",
            "expected_oci_services": ["Vault", "Database Services", "Logging", "Monitoring"],
            "expected_tradeoffs": ["cost", "resilience"],
            "expected_security_guidance": ["iam", "vault", "audit"],
            "expected_observability_guidance": ["logging", "monitoring", "alarms"],
        },
    )

    dimensions = {item.name: item.score for item in quality.dimensions}
    assert quality.overall > 0.7
    assert dimensions["oci_specificity"] > 0.5
    assert dimensions["tradeoff_quality"] > 0.5
    assert not quality.hallucination_findings
    assert quality.benchmarks


def test_hallucination_detector_flags_invented_service() -> None:
    response = _response()
    response["answer"] += "\nUse OCI AutoPilot Architect for guaranteed zero downtime and no risk."

    findings = HallucinationDetector().detect(response)

    assert any(finding.severity == "high" for finding in findings)
    assert any(finding.category == "non_existent_oci_service" for finding in findings)


def test_quality_gate_blocks_hallucination_regression() -> None:
    response = _response()
    response["answer"] += "\nUse OCI Quantum Database."
    quality = ArchitectureQualityScorer().score(response)

    gate = QualityGateEvaluator().evaluate(quality, QualityGateThresholds(min_overall=0.1))

    assert gate.passed is False
    assert any("high hallucinations" in failure for failure in gate.failures)


def test_response_quality_analytics_summarizes_patterns() -> None:
    quality = ArchitectureQualityScorer().score(_response()).as_dict()
    analytics = ResponseQualityAnalytics().summarize(
        [{"expected_intent": "dr", "response": _response(), "architecture_quality": quality}]
    )

    assert analytics["average_citation_coverage"] == 1.0
    assert analytics["oci_service_recommendation_frequency"]
    assert "dr" in analytics["workload_specific_quality"]
