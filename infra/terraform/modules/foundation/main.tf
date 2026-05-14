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
      {}
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
