resource "google_service_account" "clouddns_operator" {
  account_id   = "clouddns-operator"
  display_name = "CloudDNS Operator"
}

resource "google_service_account" "cloudstorage_operator" {
  account_id   = "cloudstorage-operator"
  display_name = "CloudStorage Operator"
}

resource "google_service_account" "mktdata_archiver_operator" {
  account_id   = "mktdata-archiver-operator"
  display_name = "Mktdata Archiver Operator"
  project      = "strange-metrics-258802"
}

resource "google_service_account" "research_operator" {
  account_id   = "research-operator"
  display_name = "Research Operator"
}

resource "google_service_account" "cpp_trader_operator" {
  account_id   = "cpp-trader"
  display_name = "CPP Trader"
  project      = "strange-metrics-258802"
}

resource "google_project_iam_policy" "iam_policy" {
  project     = var.project_id
  policy_data = data.google_iam_policy.iam_data.policy_data
}

data "google_iam_policy" "iam_data" {
  binding {
    role = "roles/dns.admin"

    members = [
      "serviceAccount:${google_service_account.clouddns_operator.email}",
    ]
  }

  binding {
    members = [
      "user:nrcopty@gmail.com",
      "user:nayef.copty@muwazana.com",
      "user:mustafa@muwazana.com",
      "user:josh@dvir.us",
      "user:josh@swiftlane.com",
    ]

    role = "roles/owner"
  }

  binding {
    members = [
      "serviceAccount:service-${var.project_number}@container-engine-robot.iam.gserviceaccount.com",
    ]

    role = "roles/container.serviceAgent"
  }

  binding {
    members = [
      "serviceAccount:service-${var.project_number}@compute-system.iam.gserviceaccount.com",
    ]

    role = "roles/compute.serviceAgent"
  }

  binding {
    members = [
      "serviceAccount:${var.project_number}-compute@developer.gserviceaccount.com",
      "serviceAccount:${var.project_number}@cloudservices.gserviceaccount.com",
      "serviceAccount:service-${var.project_number}@compute-system.iam.gserviceaccount.com",
      "serviceAccount:service-${var.project_number}@container-engine-robot.iam.gserviceaccount.com",
      "serviceAccount:service-${var.project_number}@containerregistry.iam.gserviceaccount.com",
      "serviceAccount:${var.project_id}@appspot.gserviceaccount.com",
    ]

    role = "roles/editor"
  }

  binding {
    members = [
      "user:nrcopty@gmail.com",
      "user:nayef.copty@muwazana.com",
      "user:mustafa@muwazana.com",
      "user:eslamsamir232@gmail.com",
      "user:butera.paul@gmail.com",
    ]
    role = "roles/iap.httpsResourceAccessor"
  }

  # Port forwarding only
  binding {
    members = [
      "user:eslamsamir232@gmail.com",
      "user:butera.paul@gmail.com",
    ]
    role = "roles/container.viewer"
  }

  binding {
    members = [
      "serviceAccount:service-${var.project_number}@gcf-admin-robot.iam.gserviceaccount.com",
      "serviceAccount:${google_service_account.cpp_trader_operator.email}",
    ]

    role = "roles/cloudfunctions.serviceAgent"
  }

  binding {
    members = [
      "serviceAccount:${google_service_account.cloudstorage_operator.email}",
      "serviceAccount:${google_service_account.research_operator.email}",
      "serviceAccount:${google_service_account.cpp_trader_operator.email}",
      "serviceAccount:${google_service_account.mktdata_archiver_operator.email}",
      "serviceAccount:service-${var.project_number}@containerregistry.iam.gserviceaccount.com",
      "user:butera.paul@gmail.com"
    ]

    role = "roles/storage.admin"
  }

  binding {
    members = [
      "serviceAccount:${google_service_account.cloudstorage_operator.email}",
      "serviceAccount:${google_service_account.research_operator.email}",
      "serviceAccount:${var.project_number}-compute@developer.gserviceaccount.com",
      "serviceAccount:${var.project_number}@cloudservices.gserviceaccount.com",
      "serviceAccount:service-${var.project_number}@compute-system.iam.gserviceaccount.com",
      "serviceAccount:service-${var.project_number}@container-engine-robot.iam.gserviceaccount.com",
      "user:butera.paul@gmail.com",
    ]

    role = "roles/storage.objectAdmin"
  }

  binding {
    members = [
      "serviceAccount:${google_service_account.cloudstorage_operator.email}",
      "serviceAccount:${google_service_account.research_operator.email}",
      "user:eslamsamir232@gmail.com",
      "user:butera.paul@gmail.com",
    ]

    role = "roles/bigquery.jobUser"
  }

  binding {
    members = [
      "serviceAccount:${google_service_account.cloudstorage_operator.email}",
      "serviceAccount:${google_service_account.research_operator.email}",
      "user:eslamsamir232@gmail.com",
      "user:butera.paul@gmail.com",
    ]

    role = "roles/bigquery.dataEditor"
  }

  binding {
    members = [
      "user:butera.paul@gmail.com",
    ]

    role = "roles/monitoring.admin"
  }

  binding {
    members = [
      "serviceAccount:265906417975@cloudbuild.gserviceaccount.com",
    ]

    role = "roles/cloudbuild.builds.builder"
  }

  binding {
    members = [
      "serviceAccount:service-265906417975@gcp-sa-cloudbuild.iam.gserviceaccount.com",
    ]

    role = "roles/cloudbuild.serviceAgent"
  }

  binding {
    members = [
      "serviceAccount:${var.project_number}-compute@developer.gserviceaccount.com",
      "serviceAccount:${var.project_number}@cloudservices.gserviceaccount.com",
      "serviceAccount:service-${var.project_number}@compute-system.iam.gserviceaccount.com",
      "serviceAccount:service-${var.project_number}@container-engine-robot.iam.gserviceaccount.com",
    ]

    role = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  }
}
