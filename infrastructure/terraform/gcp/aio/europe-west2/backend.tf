terraform {
  backend "gcs" {
    bucket = "muzna_tfstate_shared"
    prefix = "prod-europe-west2"
  }
}
