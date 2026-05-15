# 03 - Fintech DR

## Prompt

Design an OCI disaster recovery approach for a regulated fintech payment platform that needs strict RTO/RPO tiers, auditability, encrypted secrets, and tested failover runbooks.

## Expected Intent

- HA/DR
- security
- fintech

## Expected OCI Services

- Full Stack Disaster Recovery
- OCI Database Services or Autonomous Database
- Virtual Cloud Network
- OCI DNS
- Vault
- Identity and Access Management
- Logging
- Monitoring
- Object Storage

## Expected Architectural Traits

- RTO/RPO tiers by workload criticality
- Cross-region or cross-fault-domain DR posture based on stated assumptions
- Database backup, replication, and recovery guidance
- Runbook-driven failover and return-to-primary testing
- Audit logging, key management, and least privilege included from the start

## Required Risk Considerations

- Data residency and regulatory evidence
- Key and secret availability during failover
- Split-brain or inconsistent payment state
- Untested runbooks and manual approval gates
- Cost and complexity tradeoffs for active-active versus active-passive

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

- Gives DR guidance without RTO/RPO tiers
- Omits auditability, encryption, or secrets handling
- Recommends active-active as mandatory without tradeoff analysis
- Does not include failover testing and runbook validation
- Uses unsupported services or makes uncited compliance claims
