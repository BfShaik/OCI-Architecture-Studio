# 04 - Cost Optimized Web App

## Prompt

Recommend a cost-optimized OCI architecture for a small but growing public web application with static assets, a database, dev/test environments, and uncertain traffic growth.

## Expected Intent

- cost-optimization
- web architecture

## Expected OCI Services

- OCI Load Balancer
- Compute or OKE where justified
- Object Storage
- OCI CDN
- OCI Database Services or Autonomous Database
- Cost Management
- Budgets
- Logging
- Monitoring

## Expected Architectural Traits

- Start lean and scale based on measured demand
- Use Object Storage and CDN for static assets where appropriate
- Separate production and dev/test lifecycle controls
- Rightsizing and autoscaling recommendations
- Budget, tagging, and cost visibility guidance

## Required Risk Considerations

- Cost savings must not remove required backups, security, or observability
- Database service and shape selection depends on workload profile
- Always-on capacity can become wasteful during uncertain growth
- CDN and storage lifecycle choices have performance and retrieval tradeoffs

## Expected Output Sections

1. Executive Summary
2. Recommended OCI Services
3. Reference Architecture
4. HA/DR Design
5. Security Considerations
6. Cost Optimization
7. Risks & Assumptions
8. Observability
9. Recommended Next Steps

## Failure Conditions

- Provides generic cost advice without concrete OCI cost levers
- Recommends cheapest possible design while omitting resilience risks
- Ignores dev/test lifecycle or budget controls
- Does not distinguish static assets from application compute
- Invents pricing or SKU details not present in evidence
