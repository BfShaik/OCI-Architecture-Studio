variable "tenancy_ocid" {
  description = "OCI tenancy OCID."
  type        = string
}

variable "parent_compartment_ocid" {
  description = "Parent compartment where the project compartment will be created."
  type        = string
}

variable "region" {
  description = "OCI region, for example us-ashburn-1."
  type        = string
}

variable "ssh_public_key" {
  description = "SSH public key for the backend Compute instance."
  type        = string
}

variable "availability_domain" {
  description = "Optional availability domain name. If empty, the first AD is used."
  type        = string
  default     = ""
}

variable "backend_image_ocid" {
  description = "Compute image OCID for the backend host. Use an Oracle Linux image OCID for the selected region."
  type        = string
}

variable "backend_shape" {
  description = "Compute shape for the backend host."
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

variable "frontend_bucket_access_type" {
  description = "Frontend bucket access type."
  type        = string
  default     = "ObjectReadWithoutList"
}

variable "alarm_email" {
  description = "Optional email endpoint for monitoring notifications."
  type        = string
  default     = ""
}

variable "enable_knowledge_refresh_scheduler" {
  description = "Enable OCI Resource Scheduler schedules for knowledge refresh."
  type        = bool
  default     = false
}

variable "knowledge_refresh_function_image" {
  description = "Container image for the knowledge refresh OCI Function. Required when scheduler is enabled."
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

variable "enable_api_gateway" {
  description = "Enable optional OCI API Gateway in front of the backend VM."
  type        = bool
  default     = false
}

variable "api_gateway_path_prefix" {
  description = "Path prefix for optional OCI API Gateway deployment."
  type        = string
  default     = "/"
}

variable "oci_devops_project_ocid" {
  description = "Optional OCI DevOps project OCID for deployment readiness metadata."
  type        = string
  default     = ""
}

variable "oci_devops_deploy_pipeline_ocid" {
  description = "Optional OCI DevOps deploy pipeline OCID for deployment readiness metadata."
  type        = string
  default     = ""
}

variable "enable_autonomous_vector_database" {
  description = "Enable optional Oracle Autonomous AI Database for Oracle AI Vector Search shadow mode."
  type        = bool
  default     = false
}

variable "autonomous_vector_db_name" {
  description = "Oracle Autonomous Database DB name for vector-search shadow mode."
  type        = string
  default     = "OCIARCHVEC"
}

variable "autonomous_vector_db_admin_password" {
  description = "Optional admin password override for the Autonomous AI Database. When empty, Terraform generates one and stores a copy in OCI Vault."
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
