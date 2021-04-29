provider "google-beta" {
  region  = var.region
  project = var.project
  version = "> 2.5.0"
}
