# 02 - EKS RDS Migration

## Prompt

Create a migration advisory for moving an AWS workload from EKS, RDS, S3, CloudFront, Route53, and Fargate to OCI while minimizing downtime and preserving rollback options.

## Expected Intent

- migration
- modernization

## Expected OCI Services

- EKS -> OKE
- RDS -> OCI Base Database or Autonomous Database
- S3 -> Object Storage
- CloudFront -> OCI CDN
- Route53 -> OCI DNS
- Fargate -> OKE Virtual Nodes
- Virtual Cloud Network
- Database Migration
- Logging
- Monitoring

## Expected Architectural Traits

- Explicit AWS-to-OCI service mapping before design recommendations
- Migration waves for platform, data, networking, DNS, and cutover
- Parallel validation and rollback planning
- Kubernetes ingress, secrets, storage classes, and IAM differences called out
- Database engine/version discovery before final target selection

## Required Risk Considerations

- RDS engine compatibility and extension gaps
- Stateful Kubernetes workloads and persistent volume migration
- DNS cutover timing and rollback
- IAM policy remapping and secret rotation
- Network connectivity and latency during migration

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

- Fails to map EKS to OKE or RDS to OCI database services
- Treats migration as a single big-bang cutover without rollback
- Ignores data replication or database compatibility
- Provides OCI recommendations unrelated to the AWS source services
- Claims zero downtime without stating assumptions and validation steps
