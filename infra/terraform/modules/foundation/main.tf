locals {
  name_prefix = "${var.project_name}-${var.environment}"
  common_tags = {
    project     = var.project_name
    environment = var.environment
    managed_by  = "terraform"
  }
}

data "oci_identity_availability_domains" "ads" {
  compartment_id = var.tenancy_ocid
}

data "oci_objectstorage_namespace" "namespace" {
  compartment_id = var.tenancy_ocid
}

resource "oci_identity_compartment" "project" {
  compartment_id = var.parent_compartment_ocid
  name           = local.name_prefix
  description    = "OCI Architecture Studio ${var.environment} environment"
  enable_delete  = true
  freeform_tags  = local.common_tags
}

resource "oci_core_vcn" "main" {
  compartment_id = oci_identity_compartment.project.id
  cidr_block     = var.vcn_cidr
  display_name   = "${local.name_prefix}-vcn"
  dns_label      = "ocias${var.environment}"
  freeform_tags  = local.common_tags
}

resource "oci_core_internet_gateway" "main" {
  compartment_id = oci_identity_compartment.project.id
  vcn_id         = oci_core_vcn.main.id
  display_name   = "${local.name_prefix}-igw"
  enabled        = true
  freeform_tags  = local.common_tags
}

resource "oci_core_route_table" "public" {
  compartment_id = oci_identity_compartment.project.id
  vcn_id         = oci_core_vcn.main.id
  display_name   = "${local.name_prefix}-public-rt"
  freeform_tags  = local.common_tags

  route_rules {
    network_entity_id = oci_core_internet_gateway.main.id
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
  }
}

resource "oci_core_security_list" "public" {
  compartment_id = oci_identity_compartment.project.id
  vcn_id         = oci_core_vcn.main.id
  display_name   = "${local.name_prefix}-public-sl"
  freeform_tags  = local.common_tags

  ingress_security_rules {
    protocol = "6"
    source   = "0.0.0.0/0"

    tcp_options {
      min = 22
      max = 22
    }
  }

  ingress_security_rules {
    protocol = "6"
    source   = "0.0.0.0/0"

    tcp_options {
      min = 8000
      max = 8000
    }
  }

  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
  }
}

resource "oci_core_subnet" "public" {
  compartment_id             = oci_identity_compartment.project.id
  vcn_id                     = oci_core_vcn.main.id
  cidr_block                 = var.public_subnet_cidr
  display_name               = "${local.name_prefix}-public-subnet"
  dns_label                  = "public"
  route_table_id             = oci_core_route_table.public.id
  security_list_ids          = [oci_core_security_list.public.id]
  prohibit_public_ip_on_vnic = false
  freeform_tags              = local.common_tags
}

resource "oci_objectstorage_bucket" "frontend" {
  compartment_id = oci_identity_compartment.project.id
  namespace      = data.oci_objectstorage_namespace.namespace.namespace
  name           = "${local.name_prefix}-frontend-assets"
  access_type    = var.frontend_bucket_access_type
  storage_tier   = "Standard"
  freeform_tags  = local.common_tags
}

resource "oci_objectstorage_bucket" "snapshots" {
  compartment_id = oci_identity_compartment.project.id
  namespace      = data.oci_objectstorage_namespace.namespace.namespace
  name           = "${local.name_prefix}-knowledge-snapshots"
  access_type    = "NoPublicAccess"
  storage_tier   = "Standard"
  freeform_tags  = local.common_tags
}

resource "oci_kms_vault" "main" {
  compartment_id = oci_identity_compartment.project.id
  display_name   = "${local.name_prefix}-vault"
  vault_type     = "DEFAULT"
  freeform_tags  = local.common_tags
}

resource "oci_kms_key" "main" {
  compartment_id      = oci_identity_compartment.project.id
  display_name        = "${local.name_prefix}-key"
  management_endpoint = oci_kms_vault.main.management_endpoint
  freeform_tags       = local.common_tags

  key_shape {
    algorithm = "AES"
    length    = 32
  }
}

resource "oci_vault_secret" "app_config_placeholder" {
  compartment_id = oci_identity_compartment.project.id
  vault_id       = oci_kms_vault.main.id
  key_id         = oci_kms_key.main.id
  secret_name    = "${local.name_prefix}-app-config-placeholder"
  description    = "Placeholder secret for OCI Architecture Studio app configuration."
  freeform_tags  = local.common_tags

  secret_content {
    content_type = "BASE64"
    content      = base64encode("replace-through-oci-console-or-ci")
  }
}

resource "oci_logging_log_group" "app" {
  compartment_id = oci_identity_compartment.project.id
  display_name   = "${local.name_prefix}-logs"
  description    = "OCI Architecture Studio application and ingestion logs"
  freeform_tags  = local.common_tags
}

resource "oci_ons_notification_topic" "alerts" {
  compartment_id = oci_identity_compartment.project.id
  name           = "${local.name_prefix}-alerts"
  description    = "OCI Architecture Studio operational alerts"
  freeform_tags  = local.common_tags
}

resource "oci_ons_subscription" "email" {
  count          = var.alarm_email == "" ? 0 : 1
  compartment_id = oci_identity_compartment.project.id
  topic_id       = oci_ons_notification_topic.alerts.id
  protocol       = "EMAIL"
  endpoint       = var.alarm_email
}

resource "oci_events_rule" "resource_lifecycle" {
  compartment_id = oci_identity_compartment.project.id
  display_name   = "${local.name_prefix}-resource-lifecycle-alerts"
  description    = "Send OCI Architecture Studio environment lifecycle events to the alerts topic."
  is_enabled     = true
  freeform_tags  = local.common_tags

  condition = jsonencode({
    data = {
      compartmentId = [oci_identity_compartment.project.id]
    }
  })

  actions {
    actions {
      action_type = "ONS"
      is_enabled  = true
      description = "Notify operators about resource lifecycle events in this environment."
      topic_id    = oci_ons_notification_topic.alerts.id
    }
  }
}

resource "oci_functions_application" "knowledge_refresh" {
  count          = var.enable_knowledge_refresh_scheduler ? 1 : 0
  compartment_id = oci_identity_compartment.project.id
  display_name   = "${local.name_prefix}-knowledge-refresh"
  subnet_ids     = [oci_core_subnet.public.id]
  shape          = "GENERIC_X86"
  freeform_tags  = local.common_tags

  config = {
    APP_ENV                      = var.environment
    REFRESH_POLICY_PATH          = "/function/knowledge/refresh_policy.json"
    KNOWLEDGE_INDEX_PATH         = "/function/knowledge/snapshots/oci-rag-index.json"
    RELEASE_SNAPSHOT_PATH        = "/function/knowledge/snapshots/oci-release-snapshot.json"
    RETRIEVAL_PROVIDER           = "local_json"
    EMBEDDING_PROVIDER           = "local"
    OCI_OBJECT_STORAGE_NAMESPACE = data.oci_objectstorage_namespace.namespace.namespace
    OCI_VECTOR_BUCKET            = oci_objectstorage_bucket.snapshots.name
    OCI_VECTOR_OBJECT_NAME       = "oci-rag-index.json"
    OCI_AUTH_MODE                = "resource_principal"
  }
}

resource "oci_functions_function" "knowledge_refresh" {
  count              = var.enable_knowledge_refresh_scheduler ? 1 : 0
  application_id     = oci_functions_application.knowledge_refresh[0].id
  display_name       = "${local.name_prefix}-knowledge-refresh"
  image              = var.knowledge_refresh_function_image
  memory_in_mbs      = var.knowledge_refresh_function_memory_mbs
  timeout_in_seconds = var.knowledge_refresh_function_timeout_seconds
  freeform_tags      = local.common_tags

  config = {
    SNAPSHOTS_BUCKET = oci_objectstorage_bucket.snapshots.name
  }

  lifecycle {
    precondition {
      condition     = !var.enable_knowledge_refresh_scheduler || var.knowledge_refresh_function_image != ""
      error_message = "knowledge_refresh_function_image is required when enable_knowledge_refresh_scheduler is true."
    }
  }
}

resource "oci_resource_scheduler_schedule" "knowledge_refresh_release_watch" {
  count              = var.enable_knowledge_refresh_scheduler ? 1 : 0
  compartment_id     = oci_identity_compartment.project.id
  display_name       = "${local.name_prefix}-knowledge-refresh-release-watch"
  description        = "Scheduled release-note refresh for OCI Architecture Studio."
  action             = "START_RESOURCE"
  recurrence_type    = "CRON"
  recurrence_details = var.knowledge_refresh_release_cron
  freeform_tags      = local.common_tags

  resources {
    id = oci_functions_function.knowledge_refresh[0].id

    parameters {
      parameter_type = "BODY"
      value = [
        jsonencode({
          mode        = "release-watch"
          upload      = true
          quick_gates = false
        })
      ]
    }
  }
}

resource "oci_resource_scheduler_schedule" "knowledge_refresh_stable_docs" {
  count              = var.enable_knowledge_refresh_scheduler ? 1 : 0
  compartment_id     = oci_identity_compartment.project.id
  display_name       = "${local.name_prefix}-knowledge-refresh-stable-docs"
  description        = "Scheduled stable OCI documentation refresh for OCI Architecture Studio."
  action             = "START_RESOURCE"
  recurrence_type    = "CRON"
  recurrence_details = var.knowledge_refresh_stable_docs_cron
  freeform_tags      = local.common_tags

  resources {
    id = oci_functions_function.knowledge_refresh[0].id

    parameters {
      parameter_type = "BODY"
      value = [
        jsonencode({
          mode        = "stable-docs"
          upload      = true
          quick_gates = false
        })
      ]
    }
  }
}

resource "oci_core_instance" "backend" {
  availability_domain = var.availability_domain != "" ? var.availability_domain : data.oci_identity_availability_domains.ads.availability_domains[0].name
  compartment_id      = oci_identity_compartment.project.id
  display_name        = "${local.name_prefix}-backend"
  shape               = var.backend_shape
  freeform_tags       = local.common_tags

  shape_config {
    ocpus         = var.backend_ocpus
    memory_in_gbs = var.backend_memory_gbs
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.public.id
    assign_public_ip = true
    display_name     = "${local.name_prefix}-backend-vnic"
  }

  source_details {
    source_type = "image"
    source_id   = var.backend_image_ocid
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
    user_data = base64encode(templatefile(
      "${path.root}/cloud-init.yaml.tftpl",
      {
        app_env                         = var.environment
        deployment_profile              = var.deployment_profile
        oci_region                      = var.region
        oci_compartment_id              = oci_identity_compartment.project.id
        oci_vault_config_secret_ocid    = oci_vault_secret.app_config_placeholder.id
        oci_logging_log_group_ocid      = oci_logging_log_group.app.id
        oci_notifications_topic_ocid    = oci_ons_notification_topic.alerts.id
        oci_events_rule_ocid            = oci_events_rule.resource_lifecycle.id
        oci_monitoring_namespace        = "oci_architecture_studio"
        operational_diagnostics_enabled = var.operational_diagnostics_enabled
        oci_connectivity_check_enabled  = var.oci_connectivity_check_enabled
        snapshots_bucket_name           = oci_objectstorage_bucket.snapshots.name
        object_storage_namespace        = data.oci_objectstorage_namespace.namespace.namespace
      }
    ))
  }
}

resource "oci_identity_dynamic_group" "backend_instances" {
  compartment_id = var.tenancy_ocid
  name           = "${local.name_prefix}-backend-instances"
  description    = "Backend Compute instances for OCI Architecture Studio ${var.environment}"
  matching_rule  = "ALL {instance.compartment.id = '${oci_identity_compartment.project.id}'}"
  freeform_tags  = local.common_tags
}

resource "oci_identity_policy" "backend_access" {
  compartment_id = var.parent_compartment_ocid
  name           = "${local.name_prefix}-backend-access"
  description    = "Least-privilege starter policy for OCI Architecture Studio backend access."
  freeform_tags  = local.common_tags

  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.backend_instances.name} to manage objects in compartment ${oci_identity_compartment.project.name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.backend_instances.name} to read secret-bundles in compartment ${oci_identity_compartment.project.name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.backend_instances.name} to use keys in compartment ${oci_identity_compartment.project.name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.backend_instances.name} to use metrics in compartment ${oci_identity_compartment.project.name}",
  ]
}

resource "oci_identity_dynamic_group" "knowledge_refresh_schedules" {
  count          = var.enable_knowledge_refresh_scheduler ? 1 : 0
  compartment_id = var.tenancy_ocid
  name           = "${local.name_prefix}-knowledge-refresh-schedules"
  description    = "Resource Scheduler schedules that invoke OCI Architecture Studio knowledge refresh."
  matching_rule  = "ANY {resource.id = '${oci_resource_scheduler_schedule.knowledge_refresh_release_watch[0].id}', resource.id = '${oci_resource_scheduler_schedule.knowledge_refresh_stable_docs[0].id}'}"
  freeform_tags  = local.common_tags
}

resource "oci_identity_policy" "knowledge_refresh_schedule_access" {
  count          = var.enable_knowledge_refresh_scheduler ? 1 : 0
  compartment_id = var.parent_compartment_ocid
  name           = "${local.name_prefix}-knowledge-refresh-schedule-access"
  description    = "Allow OCI Resource Scheduler to invoke the knowledge refresh function."
  freeform_tags  = local.common_tags

  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.knowledge_refresh_schedules[0].name} to use functions-family in compartment ${oci_identity_compartment.project.name}",
  ]
}

resource "oci_monitoring_alarm" "backend_cpu" {
  compartment_id        = oci_identity_compartment.project.id
  display_name          = "${local.name_prefix}-backend-cpu-high"
  metric_compartment_id = oci_identity_compartment.project.id
  namespace             = "oci_computeagent"
  query                 = "CpuUtilization[1m].mean() > 80"
  severity              = "WARNING"
  is_enabled            = true
  destinations          = [oci_ons_notification_topic.alerts.id]
  body                  = "Backend instance CPU utilization is above 80%."
  freeform_tags         = local.common_tags
}
