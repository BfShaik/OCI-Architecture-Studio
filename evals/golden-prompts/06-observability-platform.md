# 06 - Observability Platform

## Prompt

Design OCI observability guidance for an enterprise platform that needs centralized logs, metrics, alarms, security audit trails, and operational dashboards across application and database tiers.

## Expected Intent

- observability
- security
- operations

## Expected OCI Services

- Logging
- Monitoring
- Notifications or alarms where available in evidence
- Identity and Access Management
- Cloud Guard
- Vault where secrets and keys affect audit scope
- Database Services
- Compute or OKE where workload telemetry is discussed

## Expected Architectural Traits

- Centralized log and metric collection
- Alarm strategy tied to SLOs and operational runbooks
- Auditability for identity, network, and data-tier access
- Separation of application health, infrastructure health, and security findings
- Retention and access-control assumptions stated

## Required Risk Considerations

- Missing logs can block incident response and compliance evidence
- Excessive log retention can increase cost
- Dashboards without alarms do not provide operational readiness
- Broad log access can expose sensitive data

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

- Treats observability as only dashboards
- Omits audit logging or access control
- Does not include alarms or operational response
- Ignores cost and retention tradeoffs
- Invents observability services not grounded in evidence
