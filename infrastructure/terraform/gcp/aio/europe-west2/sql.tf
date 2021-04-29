# resource "random_string" "db_positions_01" {
#   length  = 16
#   special = true
# }

# resource "google_sql_database_instance" "db_inst_01" {
#   name             = "db-inst-01"
#   region           = var.region
#   database_version = "POSTGRES_11"

#   settings {
#     tier            = "db-custom-2-7680" #https://cloud.google.com/sql/docs/postgres/create-instance#machine-types
#     disk_autoresize = "true"
#     disk_type       = "PD_SSD"

#     backup_configuration {
#       enabled    = true
#       start_time = "00:00"
#     }

#     maintenance_window {
#       day  = "3"
#       hour = "10"
#     }
#   }
# }

# resource "google_sql_database" "db_positions_01" {
#   name      = "positions"
#   instance  = google_sql_database_instance.db_inst_01.name
#   charset   = "UTF8"
#   collation = "en_US.UTF8"
# }

# resource "google_sql_user" "db_positions_01" {
#   name     = "positions"
#   instance = google_sql_database_instance.db_inst_01.name
#   password = random_string.db_positions_01.result

#   # Ignored for postgres
#   host = ""
# }
