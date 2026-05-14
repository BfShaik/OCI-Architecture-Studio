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
