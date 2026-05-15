# 08 - Multi Region SaaS

## Prompt

Design a multi-region OCI SaaS platform architecture with tenant isolation, public ingress, shared services, database resilience, observability, cost controls, and migration-aware expansion from AWS.

## Expected Intent

- SaaS-platform
- HA/DR
- migration
- cost-optimization

## Expected OCI Services

- OCI Load Balancer
- Virtual Cloud Network
- OCI DNS
- OCI CDN
- OKE or Compute
- OCI Database Services or Autonomous Database
- Object Storage
- Identity and Access Management
- Vault
- Logging
- Monitoring
- Cost Management

## Expected Architectural Traits

- Tenant isolation model explicitly stated as an assumption or design choice
- Multi-region traffic, failover, and data placement considerations
- Shared platform services separated from tenant workloads where applicable
- Migration mappings for AWS-origin services when source context is present
- Cost allocation through tagging, budgets, and environment controls

## Required Risk Considerations

- Data residency and tenant isolation failures
- Cross-region database consistency and recovery objectives
- Noisy-neighbor and scaling risks
- DNS/failover and operational readiness
- Cost allocation and shared-service chargeback gaps

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

- Omits tenant isolation or data residency
- Treats multi-region as automatically active-active without tradeoffs
- Ignores migration-aware AWS-to-OCI mapping when AWS is mentioned
- Does not cover observability and cost allocation
- Produces a single-region generic web app design
