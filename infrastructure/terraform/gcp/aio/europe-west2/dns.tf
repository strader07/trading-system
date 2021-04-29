
resource "google_dns_managed_zone" "dns_zone" {
  name        = "muwazana-com"
  dns_name    = "muwazana.com."
  description = "Cloud DNS Zone for muwazana.com"

  visibility = "public"

  # We explicitly prevent destruction using terraform. Remove this only if you really know what you're doing.
  lifecycle {
    prevent_destroy = true
  }
}

resource "google_dns_record_set" "dev_redis_exposed" {
  name = "redis-exposed.ftx.dev.${google_dns_managed_zone.dns_zone.dns_name}"
  type = "A"
  ttl  = 300

  managed_zone = google_dns_managed_zone.dns_zone.name

  rrdatas = [google_compute_address.redis_exposed_ip_addr.address]
}
