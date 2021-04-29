resource "google_bigquery_dataset" "bq_order_analytics" {
  dataset_id = "order_analytics"
  location   = "EU"
}
