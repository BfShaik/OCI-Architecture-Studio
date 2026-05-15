# 05 - Release Awareness

## Prompt

A new OCI Object Storage release was announced. Explain how to evaluate whether it changes an existing architecture recommendation for static assets, backups, and S3-compatible migration paths.

## Expected Intent

- release-awareness
- migration
- architecture impact analysis

## Expected OCI Services

- Object Storage
- OCI CDN
- Database Services where backups are discussed
- Cost Management where lifecycle or storage tiers are discussed
- Logging or Monitoring where operational impact is discussed

## Expected Architectural Traits

- Separates known local evidence from current release truth
- Requires service name, release date, release note URL, or approved release snapshot
- Evaluates impact against compatibility, limits, security, cost, operations, and migration assumptions
- Recommends refreshing knowledge and rerunning affected evals before changing guidance

## Required Risk Considerations

- Stale local corpus can produce outdated claims
- Release scope may be regional, feature-specific, or migration-specific
- S3-compatible behavior can affect migration and client configuration
- Architecture changes should not be made without verified release evidence

## Expected Output Sections

1. Executive Summary
2. Recommended OCI Services
3. Reference Architecture
4. HA/DR Design
5. Security Considerations
6. Cost Optimization
7. Risks & Assumptions
8. Migration Strategy
9. Observability
10. Recommended Next Steps

## Failure Conditions

- Claims current release impact without release evidence
- Treats all Object Storage releases as architecture-changing
- Omits freshness boundaries or knowledge refresh steps
- Ignores S3-compatible migration considerations
- Gives uncited or overconfident current-state claims
