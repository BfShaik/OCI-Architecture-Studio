output "compartment_ocid" {
  value = module.foundation.compartment_ocid
}

output "backend_public_ip" {
  value = module.foundation.backend_public_ip
}

output "frontend_bucket_name" {
  value = module.foundation.frontend_bucket_name
}

output "snapshots_bucket_name" {
  value = module.foundation.snapshots_bucket_name
}

output "vault_ocid" {
  value = module.foundation.vault_ocid
}

output "log_group_ocid" {
  value = module.foundation.log_group_ocid
}

output "notification_topic_ocid" {
  value = module.foundation.notification_topic_ocid
}

output "backend_cpu_alarm_ocid" {
  value = module.foundation.backend_cpu_alarm_ocid
}

output "resource_lifecycle_event_rule_ocid" {
  value = module.foundation.resource_lifecycle_event_rule_ocid
}

output "app_config_secret_ocid" {
  value = module.foundation.app_config_secret_ocid
}

output "knowledge_refresh_function_ocid" {
  value = module.foundation.knowledge_refresh_function_ocid
}

output "knowledge_refresh_release_schedule_ocid" {
  value = module.foundation.knowledge_refresh_release_schedule_ocid
}

output "knowledge_refresh_stable_docs_schedule_ocid" {
  value = module.foundation.knowledge_refresh_stable_docs_schedule_ocid
}
