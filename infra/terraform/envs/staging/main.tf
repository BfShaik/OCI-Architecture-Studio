module "foundation" {
  source = "../../modules/foundation"

  tenancy_ocid                               = var.tenancy_ocid
  parent_compartment_ocid                    = var.parent_compartment_ocid
  region                                     = var.region
  environment                                = "staging"
  ssh_public_key                             = var.ssh_public_key
  availability_domain                        = var.availability_domain
  backend_image_ocid                         = var.backend_image_ocid
  backend_shape                              = var.backend_shape
  backend_ocpus                              = var.backend_ocpus
  backend_memory_gbs                         = var.backend_memory_gbs
  frontend_bucket_access_type                = var.frontend_bucket_access_type
  alarm_email                                = var.alarm_email
  enable_knowledge_refresh_scheduler         = var.enable_knowledge_refresh_scheduler
  knowledge_refresh_function_image           = var.knowledge_refresh_function_image
  knowledge_refresh_release_cron             = var.knowledge_refresh_release_cron
  knowledge_refresh_stable_docs_cron         = var.knowledge_refresh_stable_docs_cron
  knowledge_refresh_function_memory_mbs      = var.knowledge_refresh_function_memory_mbs
  knowledge_refresh_function_timeout_seconds = var.knowledge_refresh_function_timeout_seconds
}
