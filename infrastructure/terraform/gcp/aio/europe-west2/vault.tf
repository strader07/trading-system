resource "google_storage_bucket" "vault" {
  name          = "${data.google_project.gcp_project.project_id}-vault-storage"
  project       = data.google_project.gcp_project.project_id
  force_destroy = true
  storage_class = "MULTI_REGIONAL"

  bucket_policy_only = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }

    condition {
      num_newer_versions = 1
    }
  }
}

resource "google_storage_bucket_iam_member" "vault-server" {
  count  = length(var.storage_bucket_roles)
  bucket = google_storage_bucket.vault.name
  role   = element(var.storage_bucket_roles, count.index)
  member = "serviceAccount:service-${var.project_number}@container-engine-robot.iam.gserviceaccount.com"
}

resource "google_kms_key_ring" "vault" {
  name     = "vault"
  location = var.region
  project  = data.google_project.gcp_project.project_id
}

# Create the crypto key for encrypting init keys
resource "google_kms_crypto_key" "vault-init" {
  name            = "vault"
  key_ring        = google_kms_key_ring.vault.id
  rotation_period = "604800s"
}