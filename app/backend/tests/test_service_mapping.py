from oci_arch_studio_backend.services.service_mapping import OciServiceMapper


def test_aws_to_oci_service_mapping_detects_initial_mappings() -> None:
    mapping = OciServiceMapper().map_text(
        "Migrate EKS, RDS, S3, CloudFront, Route53, and Fargate to OCI."
    )

    assert mapping.summary() == (
        "EKS -> OCI Kubernetes Engine; "
        "RDS -> Database Services, Autonomous Database; "
        "S3 -> Object Storage; "
        "CloudFront -> CDN; "
        "Route53 -> OCI DNS; "
        "Fargate -> OKE Virtual Nodes, OCI Kubernetes Engine"
    )
    assert "OCI Kubernetes Engine" in mapping.mapped_services
    assert "Object Storage" in mapping.mapped_services
    assert "OCI DNS" in mapping.mapped_services


def test_aws_to_oci_service_mapping_detects_expanded_domains() -> None:
    mapping = OciServiceMapper().map_text(
        "Move CloudWatch, AWS IAM, KMS, ALB, ECR, Lambda, Glue, SageMaker, and VPC patterns to OCI."
    )

    assert "Logging" in mapping.mapped_services
    assert "Monitoring" in mapping.mapped_services
    assert "Identity and Access Management" in mapping.mapped_services
    assert "Vault" in mapping.mapped_services
    assert "Load Balancer" in mapping.mapped_services
    assert "OCI Registry" in mapping.mapped_services
    assert "OCI Functions" in mapping.mapped_services
    assert "OCI Data Integration" in mapping.mapped_services
    assert "OCI Data Science" in mapping.mapped_services
    assert "Virtual Cloud Network" in mapping.mapped_services
