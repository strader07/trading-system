module "gke-bo-aio-01" {
  source = "../../../modules/gke"

  general = {
    name    = "muzna-bo-aio-01"
    env     = "aio"
    zone    = var.zone
    project = data.google_project.gcp_project.project_id
  }

  cluster = {
    version                            = var.k8s_version
    network                            = google_compute_network.vpc.self_link
    subnetwork                         = google_compute_subnetwork.subnet.self_link
    cluster_secondary_range_name       = "aio-pod-net"
    services_secondary_range_name      = "aio-svc-net"
    logging_service                    = "logging.googleapis.com"
    monitoring_service                 = "none"
    disable_http_load_balancing        = true
    disable_horizontal_pod_autoscaling = false
    autoscaling_profile                = "OPTIMIZE_UTILIZATION"
    oauth_scopes                       = local.gke_nodes_oauth_scopes
  }

  node_pool = [
    # {
    #   name           = "node-pool"
    #   machine_type   = "custom-8-18432"
    #   disk_size_gb   = 80
    #   node_count     = 1
    #   min_node_count = 1
    #   max_node_count = 5
    #   oauth_scopes   = local.gke_nodes_oauth_scopes
    #   tags           = "aio,${var.zone}"
    #   auto_repair    = true
    #   auto_upgrade   = true
    # },
    {
      name           = "preemptible-pool"
      machine_type   = "n1-standard-8"
      disk_size_gb   = 80
      node_count     = 0
      min_node_count = 0
      max_node_count = 20
      oauth_scopes   = local.gke_nodes_oauth_scopes
      tags           = "aio,preemptible,${var.zone}"
      taint          = true
      taint_key      = "preemptible"
      taint_value    = true
      taint_effect   = "NO_SCHEDULE"
      auto_repair    = true
      auto_upgrade   = true
      preemptible    = true
    },
    {
      name           = "argo-pool-v1"
      machine_type   = "n1-highmem-16"
      disk_size_gb   = 80
      node_count     = 0
      min_node_count = 0
      max_node_count = 20
      taint          = true
      taint_key      = "argo"
      taint_value    = true
      taint_effect   = "NO_SCHEDULE"
      oauth_scopes   = local.gke_nodes_oauth_scopes
      tags           = "aio,preemptible,${var.zone}"
      auto_repair    = true
      auto_upgrade   = true
      preemptible    = true
    },
    {
      name           = "node-pool-v1"
      machine_type   = "n1-standard-2"
      disk_size_gb   = 80
      node_count     = 1
      min_node_count = 1
      max_node_count = 5
      oauth_scopes   = local.gke_nodes_oauth_scopes
      tags           = "aio,${var.zone}"
      auto_repair    = true
      auto_upgrade   = true
    }
  ]
}
