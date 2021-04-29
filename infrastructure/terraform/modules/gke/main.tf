locals {
  name_prefix = "${var.general["name"]}-${var.general["env"]}"
}

# Provides access to available Google Container Engine versions in a zone for a given project.
# https://www.terraform.io/docs/providers/google/d/google_container_engine_versions.html
data "google_container_engine_versions" "region" {
  project  = var.general["project"] != "" ? var.general["project"] : var.project
  location = var.general["zone"]
}

resource "google_container_cluster" "new_container_cluster" {
  provider = google-beta

  name = lookup(
    var.general,
    "name",
    "${local.name_prefix}-${var.general["zone"]}-master",
  )

  location = var.general["zone"]
  project  = var.general["project"] != "" ? var.general["project"] : var.project

  network    = lookup(var.cluster, "network", "default")
  subnetwork = lookup(var.cluster, "subnetwork", "default")

  logging_service    = lookup(var.cluster, "logging_service", "logging.googleapis.com")
  monitoring_service = lookup(var.cluster, "monitoring_service", "none")

  enable_kubernetes_alpha = lookup(var.cluster, "enable_kubernetes_alpha", false)
  enable_legacy_abac      = lookup(var.cluster, "enable_legacy_abac", false)

  ip_allocation_policy {
    cluster_secondary_range_name  = lookup(var.cluster, "cluster_secondary_range_name", "pod-net")
    services_secondary_range_name = lookup(var.cluster, "services_secondary_range_name", "svc-net")
  }

  cluster_autoscaling {
    enabled             = true
    autoscaling_profile = lookup(var.cluster, "autoscaling_profile", "BALANCED")
    resource_limits {
      resource_type = "memory"
      minimum       = 1
      maximum       = 300
    }
    resource_limits {
      resource_type = "cpu"
      minimum       = 1
      maximum       = 150
    }

    auto_provisioning_defaults {
      oauth_scopes = split(",", var.cluster["oauth_scopes"])
    }
  }

  remove_default_node_pool = lookup(var.cluster, "default_node_pool", true)

  min_master_version = lookup(
    var.cluster,
    "version",
    data.google_container_engine_versions.region.latest_master_version,
  )
  node_version = lookup(
    var.cluster,
    "version",
    data.google_container_engine_versions.region.latest_node_version,
  )

  node_pool {
    name = "default-pool"
  }

  maintenance_policy {
    recurring_window {
      start_time = "2020-03-17T00:00:00Z"
      end_time   = "2020-03-18T00:00:00Z"
      recurrence = "FREQ=WEEKLY;BYDAY=SA"
    }
  }

  addons_config {
    http_load_balancing {
      disabled = lookup(var.cluster, "disable_http_load_balancing", true)
    }

    horizontal_pod_autoscaling {
      disabled = lookup(var.cluster, "disable_horizontal_pod_autoscaling", true)
    }
  }

  lifecycle {
    ignore_changes = [
      node_pool,
      ip_allocation_policy,
    ]
  }
}

resource "google_container_node_pool" "new_container_cluster_node_pool" {
  provider = google-beta
  count    = length(var.node_pool)

  name = lookup(
    var.node_pool[count.index],
    "name",
    "${local.name_prefix}-${var.general["zone"]}-pool-${count.index}",
  )
  location   = var.general["zone"]
  project    = var.general["project"] != "" ? var.general["project"] : var.project
  node_count = lookup(var.node_pool[count.index], "node_count", 1)
  cluster    = google_container_cluster.new_container_cluster.name

  node_config {
    disk_size_gb    = lookup(var.node_pool[count.index], "disk_size_gb", 10)
    disk_type       = lookup(var.node_pool[count.index], "disk_type", "pd-standard")
    image_type      = lookup(var.node_pool[count.index], "image", "COS")
    local_ssd_count = lookup(var.node_pool[count.index], "local_ssd_count", 0)
    machine_type    = lookup(var.node_pool[count.index], "machine_type", "n1-standard-2")

    oauth_scopes = split(",", var.node_pool[count.index]["oauth_scopes"])
    preemptible  = lookup(var.node_pool[count.index], "preemptible", false)
    tags         = split(",", var.node_pool[count.index]["tags"])

    metadata = {
      disable-legacy-endpoints         = "true"
      google-compute-enable-virtio-rng = "true"
      disable-legacy-endpoints         = "true"
    }

    workload_metadata_config {
      node_metadata = "SECURE"
    }

    dynamic "taint" {
      for_each = lookup(var.node_pool[count.index], "taint", false) ? [lookup(var.node_pool[count.index], "taint")] : []
      content {
        effect = lookup(var.node_pool[count.index], "taint_effect", "")
        key    = lookup(var.node_pool[count.index], "taint_key", "")
        value  = lookup(var.node_pool[count.index], "taint_value", "")
      }
    }
  }

  autoscaling {
    min_node_count = lookup(var.node_pool[count.index], "min_node_count", 1)
    max_node_count = lookup(var.node_pool[count.index], "max_node_count", 3)
  }

  management {
    auto_repair  = lookup(var.node_pool[count.index], "auto_repair", true)
    auto_upgrade = lookup(var.node_pool[count.index], "auto_upgrade", false)
  }

  upgrade_settings {
    max_surge       = 1
    max_unavailable = 0
  }

  lifecycle {
    ignore_changes = [node_count]
  }
}
