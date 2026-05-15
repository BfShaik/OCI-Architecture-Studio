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

output "api_gateway_ocid" {
  value = var.enable_api_gateway ? oci_apigateway_gateway.api[0].id : null
}

output "api_gateway_endpoint" {
  value = var.enable_api_gateway ? "https://${oci_apigateway_gateway.api[0].hostname}${var.api_gateway_path_prefix}" : null
}

output "api_gateway_deployment_ocid" {
  value = var.enable_api_gateway ? oci_apigateway_deployment.backend[0].id : null
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

output "knowledge_refresh_function_ocid" {
  value = var.enable_knowledge_refresh_scheduler ? oci_functions_function.knowledge_refresh[0].id : null
}

output "knowledge_refresh_release_schedule_ocid" {
  value = var.enable_knowledge_refresh_scheduler ? oci_resource_scheduler_schedule.knowledge_refresh_release_watch[0].id : null
}

output "knowledge_refresh_stable_docs_schedule_ocid" {
  value = var.enable_knowledge_refresh_scheduler ? oci_resource_scheduler_schedule.knowledge_refresh_stable_docs[0].id : null
}

output "autonomous_vector_database_ocid" {
  value = var.enable_autonomous_vector_database ? oci_database_autonomous_database.vector_search[0].id : null
}

output "autonomous_vector_database_private_endpoint" {
  value = var.enable_autonomous_vector_database ? oci_database_autonomous_database.vector_search[0].private_endpoint : null
}

output "autonomous_vector_database_connection_strings" {
  value     = var.enable_autonomous_vector_database ? oci_database_autonomous_database.vector_search[0].connection_strings : null
  sensitive = true
}

output "governance_resource_summary" {
  description = "OCI-native governance and operations resources managed by Terraform for rebuild/audit review."
  value = {
    compartment_ocid              = oci_identity_compartment.project.id
    backend_dynamic_group_name    = oci_identity_dynamic_group.backend_instances.name
    backend_policy_ocid           = oci_identity_policy.backend_access.id
    vault_ocid                    = oci_kms_vault.main.id
    key_ocid                      = oci_kms_key.main.id
    app_config_secret_ocid        = oci_vault_secret.app_config_placeholder.id
    log_group_ocid                = oci_logging_log_group.app.id
    notification_topic_ocid       = oci_ons_notification_topic.alerts.id
    resource_lifecycle_rule_ocid  = oci_events_rule.resource_lifecycle.id
    backend_cpu_alarm_ocid        = oci_monitoring_alarm.backend_cpu.id
    api_gateway_ocid              = var.enable_api_gateway ? oci_apigateway_gateway.api[0].id : null
    api_gateway_endpoint          = var.enable_api_gateway ? "https://${oci_apigateway_gateway.api[0].hostname}${var.api_gateway_path_prefix}" : null
    api_gateway_deployment_ocid   = var.enable_api_gateway ? oci_apigateway_deployment.backend[0].id : null
    oci_devops_project_ocid       = var.oci_devops_project_ocid != "" ? var.oci_devops_project_ocid : null
    oci_devops_deploy_pipeline    = var.oci_devops_deploy_pipeline_ocid != "" ? var.oci_devops_deploy_pipeline_ocid : null
    knowledge_refresh_function    = var.enable_knowledge_refresh_scheduler ? oci_functions_function.knowledge_refresh[0].id : null
    release_refresh_schedule_ocid = var.enable_knowledge_refresh_scheduler ? oci_resource_scheduler_schedule.knowledge_refresh_release_watch[0].id : null
    stable_docs_schedule_ocid     = var.enable_knowledge_refresh_scheduler ? oci_resource_scheduler_schedule.knowledge_refresh_stable_docs[0].id : null
    autonomous_vector_database    = var.enable_autonomous_vector_database ? oci_database_autonomous_database.vector_search[0].id : null
  }
}

output "runtime_infrastructure_summary" {
  description = "Operator-readable OCI runtime topology and IaC rebuildability summary."
  value = {
    environment        = var.environment
    region             = var.region
    deployment_profile = var.deployment_profile
    network = {
      compartment_ocid    = oci_identity_compartment.project.id
      vcn_ocid            = oci_core_vcn.main.id
      public_subnet_ocid  = oci_core_subnet.public.id
      internet_gateway    = oci_core_internet_gateway.main.id
      public_route_table  = oci_core_route_table.public.id
      public_securitylist = oci_core_security_list.public.id
    }
    api_exposure = {
      mode                 = var.enable_api_gateway ? "oci_api_gateway" : "direct_backend_vm"
      api_gateway_ocid     = var.enable_api_gateway ? oci_apigateway_gateway.api[0].id : null
      api_gateway_endpoint = var.enable_api_gateway ? "https://${oci_apigateway_gateway.api[0].hostname}${var.api_gateway_path_prefix}" : null
      backend_public_ip    = oci_core_instance.backend.public_ip
      backend_direct_port  = 8000
    }
    runtime = {
      backend_instance_ocid           = oci_core_instance.backend.id
      backend_shape                   = var.backend_shape
      backend_ocpus                   = var.backend_ocpus
      backend_memory_gbs              = var.backend_memory_gbs
      functions_scheduler             = var.enable_knowledge_refresh_scheduler ? "enabled" : "disabled"
      knowledge_refresh_function_ocid = var.enable_knowledge_refresh_scheduler ? oci_functions_function.knowledge_refresh[0].id : null
      release_refresh_schedule_ocid   = var.enable_knowledge_refresh_scheduler ? oci_resource_scheduler_schedule.knowledge_refresh_release_watch[0].id : null
      stable_docs_schedule_ocid       = var.enable_knowledge_refresh_scheduler ? oci_resource_scheduler_schedule.knowledge_refresh_stable_docs[0].id : null
    }
    storage = {
      frontend_bucket  = oci_objectstorage_bucket.frontend.name
      snapshots_bucket = oci_objectstorage_bucket.snapshots.name
      namespace        = data.oci_objectstorage_namespace.namespace.namespace
    }
    security = {
      vault_ocid                 = oci_kms_vault.main.id
      key_ocid                   = oci_kms_key.main.id
      app_config_secret_ocid     = oci_vault_secret.app_config_placeholder.id
      backend_dynamic_group_name = oci_identity_dynamic_group.backend_instances.name
      backend_policy_ocid        = oci_identity_policy.backend_access.id
    }
    observability = {
      log_group_ocid               = oci_logging_log_group.app.id
      notification_topic_ocid      = oci_ons_notification_topic.alerts.id
      backend_cpu_alarm_ocid       = oci_monitoring_alarm.backend_cpu.id
      resource_lifecycle_rule_ocid = oci_events_rule.resource_lifecycle.id
    }
    delivery = {
      oci_devops_project_ocid         = var.oci_devops_project_ocid != "" ? var.oci_devops_project_ocid : null
      oci_devops_deploy_pipeline_ocid = var.oci_devops_deploy_pipeline_ocid != "" ? var.oci_devops_deploy_pipeline_ocid : null
    }
    vector_search = {
      provider_ready                     = var.enable_autonomous_vector_database
      autonomous_database_ocid           = var.enable_autonomous_vector_database ? oci_database_autonomous_database.vector_search[0].id : null
      autonomous_database_private_ep     = var.enable_autonomous_vector_database ? oci_database_autonomous_database.vector_search[0].private_endpoint : null
      autonomous_database_version        = var.enable_autonomous_vector_database ? oci_database_autonomous_database.vector_search[0].db_version : null
      autonomous_database_private_access = var.enable_autonomous_vector_database
    }
  }
}
