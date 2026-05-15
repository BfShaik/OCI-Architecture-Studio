from oci_arch_studio_backend.models.architecture import RetrievedSource
from oci_arch_studio_backend.services.architecture_consistency import ArchitectureConsistencyValidator
from oci_arch_studio_backend.services.intents import Intent, get_intent_profile


def test_consistency_validator_flags_conflicting_dr_requirements() -> None:
    findings = ArchitectureConsistencyValidator().validate(
        question="Design a fintech DR platform with zero downtime, no backups, and no monitoring.",
        workload_context=None,
        profile=get_intent_profile(Intent.DR),
        answer="Use Vault for keys and document RTO/RPO.",
        recommendations=["Use Vault and define recovery tiers."],
        sources=[
            RetrievedSource(
                chunk_id="vault::1",
                title="Vault",
                source_type="oci_doc",
                service="Vault",
                service_domain="security",
                summary="Vault protects secrets.",
            )
        ],
    )

    checks = {finding.check for finding in findings}
    assert "conflicting_availability_claim" in checks
    assert "missing_backup_conflict" in checks
    assert "missing_monitoring_conflict" in checks


def test_consistency_validator_flags_missing_migration_target_evidence() -> None:
    findings = ArchitectureConsistencyValidator().validate(
        question="Migrate EKS and CloudWatch to OCI.",
        workload_context=None,
        profile=get_intent_profile(Intent.MIGRATION),
        answer="Migrate Kubernetes in waves.",
        recommendations=["Plan migration waves and rollback."],
        sources=[
            RetrievedSource(
                chunk_id="oke::1",
                title="OKE",
                source_type="oci_doc",
                service="OCI Kubernetes Engine",
                service_domain="containers",
                summary="OKE supports Kubernetes.",
            )
        ],
    )

    assert any(finding.check == "migration_mapping_coverage" for finding in findings)
