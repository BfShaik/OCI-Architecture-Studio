# Optional remote state backend template.
#
# Copy this file into an environment directory as backend.tf after creating
# the state bucket and updating the values. Do not commit real bucket or
# namespace values if they are sensitive for your environment.

terraform {
  backend "oci" {
    bucket    = "oci-architecture-studio-tfstate"
    namespace = "replace_with_object_storage_namespace"
    key       = "oci-architecture-studio/dev/terraform.tfstate"
    region    = "us-ashburn-1"
  }
}
