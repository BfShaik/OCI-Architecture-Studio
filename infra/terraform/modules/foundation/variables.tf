variable "tenancy_ocid" {
  description = "OCI tenancy OCID."
  type        = string
}

variable "parent_compartment_ocid" {
  description = "Parent compartment where the project compartment will be created."
  type        = string
}

variable "region" {
  description = "OCI region."
  type        = string
}

variable "project_name" {
  description = "Project name prefix."
  type        = string
  default     = "oci-architecture-studio"
}

variable "environment" {
  description = "Environment name."
  type        = string
  default     = "dev"
}

variable "vcn_cidr" {
  description = "VCN CIDR block."
  type        = string
  default     = "10.20.0.0/16"
}

variable "public_subnet_cidr" {
  description = "Public subnet CIDR block."
  type        = string
  default     = "10.20.10.0/24"
}

variable "frontend_bucket_access_type" {
  description = "Frontend bucket access type. Use ObjectReadWithoutList for simple static hosting, NoPublicAccess for private/CDN-only hosting."
  type        = string
  default     = "ObjectReadWithoutList"
}

variable "ssh_public_key" {
  description = "SSH public key for backend instance."
  type        = string
}

variable "availability_domain" {
  description = "Optional availability domain name. If empty, the first AD is used."
  type        = string
  default     = ""
}

variable "backend_image_ocid" {
  description = "Compute image OCID for backend host."
  type        = string
}

variable "backend_shape" {
  description = "Compute shape for backend host."
  type        = string
  default     = "VM.Standard.E5.Flex"
}

variable "backend_ocpus" {
  description = "OCPUs for flexible backend shape."
  type        = number
  default     = 8
}

variable "backend_memory_gbs" {
  description = "Memory in GB for flexible backend shape."
  type        = number
  default     = 128
}

variable "alarm_email" {
  description = "Optional email endpoint for monitoring notifications."
  type        = string
  default     = ""
}

variable "enable_knowledge_refresh_scheduler" {
  description = "Enable OCI Resource Scheduler schedules for the knowledge refresh function."
  type        = bool
  default     = false
}

variable "knowledge_refresh_function_image" {
  description = "Container image for the OCI Function that runs knowledge refresh. Required when scheduler is enabled."
  type        = string
  default     = ""
}

variable "knowledge_refresh_release_cron" {
  description = "Cron expression for release-note refresh."
  type        = string
  default     = "17 */6 * * *"
}

variable "knowledge_refresh_stable_docs_cron" {
  description = "Cron expression for stable OCI documentation refresh."
  type        = string
  default     = "23 2 * * 0"
}

variable "knowledge_refresh_function_memory_mbs" {
  description = "Memory in MB for the knowledge refresh OCI Function."
  type        = number
  default     = 1024
}

variable "knowledge_refresh_function_timeout_seconds" {
  description = "Timeout in seconds for the knowledge refresh OCI Function."
  type        = number
  default     = 900
}

variable "deployment_profile" {
  description = "Runtime deployment profile exposed to the backend diagnostics layer."
  type        = string
  default     = "oci_vm"

  validation {
    condition     = contains(["local_dev", "oci_vm", "oke", "oci_functions"], var.deployment_profile)
    error_message = "deployment_profile must be one of local_dev, oci_vm, oke, or oci_functions."
  }
}

variable "operational_diagnostics_enabled" {
  description = "Enable additive operational diagnostics endpoints and runtime health summaries."
  type        = bool
  default     = true
}

variable "oci_connectivity_check_enabled" {
  description = "Enable live OCI SDK connectivity checks from operational diagnostics. Keep false unless runtime IAM is ready."
  type        = bool
  default     = false
}

variable "enable_api_gateway" {
  description = "Enable optional OCI API Gateway in front of the backend VM. Default false to avoid changing staging exposure until explicitly promoted."
  type        = bool
  default     = false
}

variable "api_gateway_path_prefix" {
  description = "Path prefix for the optional OCI API Gateway deployment."
  type        = string
  default     = "/"
}

variable "oci_devops_project_ocid" {
  description = "Optional OCI DevOps project OCID for deployment-readiness diagnostics and IaC rebuild metadata."
  type        = string
  default     = ""
}

variable "oci_devops_deploy_pipeline_ocid" {
  description = "Optional OCI DevOps deploy pipeline OCID for deployment-readiness diagnostics and IaC rebuild metadata."
  type        = string
  default     = ""
}

variable "enable_autonomous_vector_database" {
  description = "Enable optional Oracle Autonomous AI Database for Oracle AI Vector Search shadow mode. Default false to avoid provisioning database cost until explicitly approved."
  type        = bool
  default     = false
}

variable "autonomous_vector_db_name" {
  description = "Oracle Autonomous Database DB name for vector-search shadow mode. Use letters and numbers only."
  type        = string
  default     = "OCIARCHVEC"

  validation {
    condition     = can(regex("^[A-Za-z][A-Za-z0-9]{1,13}$", var.autonomous_vector_db_name))
    error_message = "autonomous_vector_db_name must start with a letter and contain 2-14 letters or numbers."
  }
}

variable "autonomous_vector_db_admin_password" {
  description = "Admin password for the optional Autonomous AI Database. Required only when enable_autonomous_vector_database is true. This value is sensitive and will still be present in Terraform state."
  type        = string
  default     = ""
  sensitive   = true
}

variable "autonomous_vector_db_compute_count" {
  description = "ECPU compute count for the optional Autonomous AI Database."
  type        = number
  default     = 2
}

variable "autonomous_vector_db_storage_tbs" {
  description = "Storage size in TB for the optional Autonomous AI Database."
  type        = number
  default     = 1
}

variable "autonomous_vector_db_version" {
  description = "Autonomous Database version for vector-search shadow mode."
  type        = string
  default     = "26ai"
}

variable "autonomous_vector_db_license_model" {
  description = "License model for the optional Autonomous AI Database."
  type        = string
  default     = "LICENSE_INCLUDED"
}
