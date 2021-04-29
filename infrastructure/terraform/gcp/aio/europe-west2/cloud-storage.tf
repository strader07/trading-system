resource "google_storage_bucket" "argo" {
  name     = "muzna-argo"
  location = "EUROPE-WEST2"
  project  = var.project_id
}

resource "google_storage_bucket" "mlflow" {
  name     = "muzna-mlflow"
  location = "EUROPE-WEST2"
  project  = var.project_id
}
