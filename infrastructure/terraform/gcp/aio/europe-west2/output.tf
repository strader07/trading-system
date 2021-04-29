output "redis_exposed_ip_addr" {
  value = google_compute_address.redis_exposed_ip_addr.address
}
