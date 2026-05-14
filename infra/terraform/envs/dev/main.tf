module "foundation" {
  source = "../../modules/foundation"

  tenancy_ocid                = var.tenancy_ocid
  parent_compartment_ocid     = var.parent_compartment_ocid
  region                      = var.region
  ssh_public_key              = var.ssh_public_key
  availability_domain         = var.availability_domain
  backend_image_ocid          = var.backend_image_ocid
  backend_shape               = var.backend_shape
  backend_ocpus               = var.backend_ocpus
  backend_memory_gbs          = var.backend_memory_gbs
  frontend_bucket_access_type = var.frontend_bucket_access_type
  alarm_email                 = var.alarm_email
}
