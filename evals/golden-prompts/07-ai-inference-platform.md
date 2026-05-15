# 07 - AI Inference Platform

## Prompt

Recommend an OCI architecture for an AI inference platform serving internal applications, with model artifacts, private API access, logging, monitoring, security controls, and cost-aware scaling.

## Expected Intent

- AI/ML
- security
- cost-optimization

## Expected OCI Services

- Compute or OKE for serving workloads when grounded
- Object Storage for model artifacts
- Virtual Cloud Network
- Load Balancer where API ingress is needed
- Identity and Access Management
- Vault
- Logging
- Monitoring
- Cost Management

## Expected Architectural Traits

- Private network placement for internal inference APIs
- Model artifacts stored durably with access controls
- Scaling strategy tied to throughput and latency assumptions
- Observability for latency, error rate, saturation, and model-serving health
- Security controls for secrets, identity, and data access

## Required Risk Considerations

- Model serving capacity and cost can vary with traffic shape
- Sensitive prompts, inputs, or outputs may require retention and access controls
- Model artifact integrity and rollout strategy must be governed
- GPU or specialized serving recommendations require evidence and sizing data

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

- Invents AI services or accelerator details without evidence
- Ignores private access and model artifact security
- Omits monitoring of inference health
- Provides generic AI advice without OCI service grounding
- Recommends expensive always-on capacity without cost tradeoffs
