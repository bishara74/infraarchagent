# Random passwords for DB and Grafana
resource "random_password" "grafana_admin" {
  length  = 12
  special = false
}
