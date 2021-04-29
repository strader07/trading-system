output "endpoint" {
  value       = google_container_cluster.new_container_cluster.endpoint
  description = "The IP address of this cluster's Kubernetes master"
}

output "client_key" {
  value       = google_container_cluster.new_container_cluster.master_auth[0].client_key
  description = "Base64 encoded private key used by clients to authenticate to the cluster endpoint"
}

output "client_certificate" {
  value       = google_container_cluster.new_container_cluster.master_auth[0].client_certificate
  description = "Base64 encoded public certificate used by clients to authenticate to the cluster endpoint"
}

output "cluster_ca_certificate" {
  value       = google_container_cluster.new_container_cluster.master_auth[0].cluster_ca_certificate
  description = "Base64 encoded public certificate that is the root of trust for the cluster"
}

output "name" {
  value       = google_container_cluster.new_container_cluster.name
  description = "Kubernetes cluster name"
}

