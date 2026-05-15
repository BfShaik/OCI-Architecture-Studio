# 01 - HA Ecommerce

## Prompt

Design a highly available OCI architecture for an ecommerce platform with public web traffic, checkout flows, product media, a relational database, and seasonal traffic spikes.

## Expected Intent

- HA/DR
- ecommerce workload architecture

## Expected OCI Services

- OCI Load Balancer
- Virtual Cloud Network
- OCI Kubernetes Engine or Compute
- OCI Database Services or Autonomous Database
- Object Storage
- OCI CDN
- Web Application Firewall
- Logging
- Monitoring

## Expected Architectural Traits

- Public ingress separated from private application and data tiers
- Multi-AD or fault-domain placement where region topology allows
- Health checks, autoscaling, and rolling deployment support
- Durable object storage for product media and static assets
- Database backup and recovery posture
- Clear distinction between stateless app tiers and stateful data tiers

## Required Risk Considerations

- Checkout consistency and payment isolation
- Peak-sale capacity and autoscaling limits
- Database HA, backup, and recovery objectives
- WAF, TLS, and least-privilege access
- Observability for latency, error rate, and order-flow health

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

- Omits HA/DR tradeoffs or recovery objectives
- Recommends unsupported or uncited OCI services
- Places the database in a public subnet without risk discussion
- Ignores product media/static asset handling
- Produces generic cloud guidance without ecommerce-specific risks
