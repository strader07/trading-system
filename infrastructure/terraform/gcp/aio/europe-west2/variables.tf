locals {
  gke_nodes_oauth_scopes = "${join(",", list(
    "https://www.googleapis.com/auth/cloud.useraccounts.readonly",
    "https://www.googleapis.com/auth/compute",
    "https://www.googleapis.com/auth/devstorage.read_write",
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/cloudkms",
    "https://www.googleapis.com/auth/logging.write",
    "https://www.googleapis.com/auth/monitoring.write",
    "https://www.googleapis.com/auth/pubsub",
    "https://www.googleapis.com/auth/service.management.readonly",
    "https://www.googleapis.com/auth/servicecontrol",
    "https://www.googleapis.com/auth/source.read_only",
    "https://www.googleapis.com/auth/trace.append",
  ))}"
}

variable "storage_bucket_roles" {
  type = list(string)
  default = [
    "roles/storage.legacyBucketReader",
    "roles/storage.objectAdmin",
  ]
  description = "List of storage bucket roles."
}

variable "project_id" {
  default = "strange-metrics-258802"
}

variable "billing_account" {
  default = "01C124-40DF57-B5F3D2"
}

variable "project_number" {
  default = "265906417975"
}

variable "region" {
  default = "europe-west2"
}

variable "zone" {
  default = "europe-west2-c"
}

variable "k8s_version" {
  description = "Kubernetes Version"
  default     = "1.14.10-gke.42"
}
