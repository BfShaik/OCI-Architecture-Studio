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
