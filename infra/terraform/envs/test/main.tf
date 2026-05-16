module "foundation" {
  source = "../../modules/foundation"

  tenancy_ocid                        = var.tenancy_ocid
  parent_compartment_ocid             = var.parent_compartment_ocid
  region                              = var.region
  environment                         = "test"
  ssh_public_key                      = var.ssh_public_key
  availability_domain                 = var.availability_domain
  backend_image_ocid                  = var.backend_image_ocid
  backend_shape                       = var.backend_shape
  backend_ocpus                       = var.backend_ocpus
  backend_memory_gbs                  = var.backend_memory_gbs
  frontend_bucket_access_type         = var.frontend_bucket_access_type
  alarm_email                         = var.alarm_email
  enable_api_gateway                  = var.enable_api_gateway
  api_gateway_path_prefix             = var.api_gateway_path_prefix
  oci_devops_project_ocid             = var.oci_devops_project_ocid
  oci_devops_deploy_pipeline_ocid     = var.oci_devops_deploy_pipeline_ocid
  enable_autonomous_vector_database   = var.enable_autonomous_vector_database
  autonomous_vector_db_name           = var.autonomous_vector_db_name
  autonomous_vector_db_admin_password = var.autonomous_vector_db_admin_password
  autonomous_vector_db_compute_count  = var.autonomous_vector_db_compute_count
  autonomous_vector_db_storage_tbs    = var.autonomous_vector_db_storage_tbs
  autonomous_vector_db_version        = var.autonomous_vector_db_version
  autonomous_vector_db_license_model  = var.autonomous_vector_db_license_model
}
