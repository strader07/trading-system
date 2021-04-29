resource "google_compute_network" "vpc" {
  name                    = "muzna-bo-aio-01"
  auto_create_subnetworks = "false"
}

resource "google_compute_subnetwork" "subnet" {
  name          = "aio-subnet"
  region        = var.region
  ip_cidr_range = "10.191.0.0/22"
  network       = google_compute_network.vpc.self_link

  secondary_ip_range {
    range_name    = "aio-pod-net"
    ip_cidr_range = "10.48.0.0/14"
  }
  secondary_ip_range {
    range_name    = "aio-svc-net"
    ip_cidr_range = "10.2.0.0/20"
  }
}
