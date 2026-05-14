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
