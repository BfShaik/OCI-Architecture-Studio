locals {
  name_prefix = "${var.project_name}-${var.environment}"
  common_tags = {
    project     = var.project_name
    environment = var.environment
    managed_by  = "terraform"
  }
  autonomous_vector_db_admin_password = (
    var.autonomous_vector_db_admin_password != ""
    ? var.autonomous_vector_db_admin_password
    : try(random_password.autonomous_vector_db_admin[0].result, "")
  )
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
      min = 443
      max = 443
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

  ingress_security_rules {
    protocol = "6"
    source   = var.public_subnet_cidr

    tcp_options {
      min = 1522
      max = 1522
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

resource "random_password" "autonomous_vector_db_admin" {
  count            = var.enable_autonomous_vector_database && var.autonomous_vector_db_admin_password == "" ? 1 : 0
  length           = 24
  min_lower        = 1
  min_numeric      = 1
  min_special      = 1
  min_upper        = 1
  override_special = "#_-"
  special          = true
}

resource "oci_vault_secret" "autonomous_vector_db_admin_password" {
  count          = var.enable_autonomous_vector_database ? 1 : 0
  compartment_id = oci_identity_compartment.project.id
  vault_id       = oci_kms_vault.main.id
  key_id         = oci_kms_key.main.id
  secret_name    = "${local.name_prefix}-vector-db-admin-password"
  description    = "Admin password for the Autonomous Database used by Oracle AI Vector Search shadow mode."
  freeform_tags  = merge(local.common_tags, { purpose = "oracle-ai-vector-search" })

  secret_content {
    content_type = "BASE64"
    content      = base64encode(local.autonomous_vector_db_admin_password)
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
        oci_api_gateway_ocid            = var.enable_api_gateway ? oci_apigateway_gateway.api[0].id : ""
        oci_api_gateway_endpoint        = var.enable_api_gateway ? "https://${oci_apigateway_gateway.api[0].hostname}${var.api_gateway_path_prefix}" : ""
        oci_devops_project_ocid         = var.oci_devops_project_ocid
        oci_devops_deploy_pipeline_ocid = var.oci_devops_deploy_pipeline_ocid
        oci_monitoring_namespace        = "oci_architecture_studio"
        operational_diagnostics_enabled = var.operational_diagnostics_enabled
        oci_connectivity_check_enabled  = var.oci_connectivity_check_enabled
        snapshots_bucket_name           = oci_objectstorage_bucket.snapshots.name
        object_storage_namespace        = data.oci_objectstorage_namespace.namespace.namespace
      }
    ))
  }

  lifecycle {
    ignore_changes = [
      metadata["user_data"],
    ]
  }
}

resource "oci_apigateway_gateway" "api" {
  count          = var.enable_api_gateway ? 1 : 0
  compartment_id = oci_identity_compartment.project.id
  display_name   = "${local.name_prefix}-api-gateway"
  endpoint_type  = "PUBLIC"
  subnet_id      = oci_core_subnet.public.id
  freeform_tags  = local.common_tags
}

resource "oci_apigateway_deployment" "backend" {
  count          = var.enable_api_gateway ? 1 : 0
  compartment_id = oci_identity_compartment.project.id
  display_name   = "${local.name_prefix}-backend-api"
  gateway_id     = oci_apigateway_gateway.api[0].id
  path_prefix    = var.api_gateway_path_prefix
  freeform_tags  = local.common_tags

  specification {
    routes {
      path    = "/{path*}"
      methods = ["GET", "POST", "OPTIONS"]

      backend {
        type = "HTTP_BACKEND"
        url  = "http://${oci_core_instance.backend.public_ip}:8000/$${request.path[path]}"
      }
    }
  }
}

resource "oci_core_network_security_group" "autonomous_vector_db" {
  count          = var.enable_autonomous_vector_database ? 1 : 0
  compartment_id = oci_identity_compartment.project.id
  vcn_id         = oci_core_vcn.main.id
  display_name   = "${local.name_prefix}-vector-db-nsg"
  freeform_tags  = local.common_tags
}

resource "oci_core_network_security_group_security_rule" "backend_to_autonomous_vector_db" {
  count                     = var.enable_autonomous_vector_database ? 1 : 0
  network_security_group_id = oci_core_network_security_group.autonomous_vector_db[0].id
  direction                 = "INGRESS"
  protocol                  = "6"
  source                    = var.public_subnet_cidr
  source_type               = "CIDR_BLOCK"
  description               = "Allow backend subnet access to Autonomous Database private endpoint over TCPS."

  tcp_options {
    destination_port_range {
      min = 1522
      max = 1522
    }
  }
}

resource "oci_database_autonomous_database" "vector_search" {
  count                       = var.enable_autonomous_vector_database ? 1 : 0
  compartment_id              = oci_identity_compartment.project.id
  db_name                     = var.autonomous_vector_db_name
  display_name                = "${local.name_prefix}-vector-db"
  admin_password              = local.autonomous_vector_db_admin_password
  compute_model               = "ECPU"
  compute_count               = var.autonomous_vector_db_compute_count
  data_storage_size_in_tbs    = var.autonomous_vector_db_storage_tbs
  db_version                  = var.autonomous_vector_db_version
  db_workload                 = "OLTP"
  is_auto_scaling_enabled     = true
  is_mtls_connection_required = true
  license_model               = var.autonomous_vector_db_license_model
  subnet_id                   = oci_core_subnet.public.id
  nsg_ids                     = [oci_core_network_security_group.autonomous_vector_db[0].id]
  private_endpoint_label      = "${var.environment}vectordb"
  whitelisted_ips             = []
  freeform_tags               = merge(local.common_tags, { purpose = "oracle-ai-vector-search" })

  lifecycle {
    precondition {
      condition     = !var.enable_autonomous_vector_database || local.autonomous_vector_db_admin_password != ""
      error_message = "autonomous_vector_db_admin_password or generated password is required when enable_autonomous_vector_database is true."
    }
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
    "Allow dynamic-group ${oci_identity_dynamic_group.backend_instances.name} to use generative-ai-family in compartment ${oci_identity_compartment.project.name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.backend_instances.name} to use instance-agent-command-family in compartment ${oci_identity_compartment.project.name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.backend_instances.name} to use instance-agent-command-execution-family in compartment ${oci_identity_compartment.project.name} where request.instance.id = target.instance.id",
  ]
}

resource "oci_identity_policy" "backend_genai_tenancy_access" {
  compartment_id = var.tenancy_ocid
  name           = "${local.name_prefix}-backend-genai-tenancy-access"
  description    = "Tenancy-level OCI Generative AI access for pretrained model catalog and inference visibility."
  freeform_tags  = local.common_tags

  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.backend_instances.name} to use generative-ai-family in tenancy",
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
