output "compartment_ocid" {
  value = oci_identity_compartment.project.id
}

output "vcn_ocid" {
  value = oci_core_vcn.main.id
}

output "public_subnet_ocid" {
  value = oci_core_subnet.public.id
}

output "backend_instance_ocid" {
  value = oci_core_instance.backend.id
}

output "backend_public_ip" {
  value = oci_core_instance.backend.public_ip
}

output "frontend_bucket_name" {
  value = oci_objectstorage_bucket.frontend.name
}

output "snapshots_bucket_name" {
  value = oci_objectstorage_bucket.snapshots.name
}

output "vault_ocid" {
  value = oci_kms_vault.main.id
}

output "key_ocid" {
  value = oci_kms_key.main.id
}

output "log_group_ocid" {
  value = oci_logging_log_group.app.id
}

output "notification_topic_ocid" {
  value = oci_ons_notification_topic.alerts.id
}

output "backend_cpu_alarm_ocid" {
  value = oci_monitoring_alarm.backend_cpu.id
}

output "resource_lifecycle_event_rule_ocid" {
  value = oci_events_rule.resource_lifecycle.id
}

output "app_config_secret_ocid" {
  value = oci_vault_secret.app_config_placeholder.id
}

output "backend_dynamic_group_name" {
  value = oci_identity_dynamic_group.backend_instances.name
}

output "backend_policy_ocid" {
  value = oci_identity_policy.backend_access.id
}
