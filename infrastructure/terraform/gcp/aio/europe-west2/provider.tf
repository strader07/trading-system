provider "google-beta" {
  region  = var.region
  project = var.project_id
  version = "= 3.35.0"
}
