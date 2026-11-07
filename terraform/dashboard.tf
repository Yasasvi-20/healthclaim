# ============================================================
# Milestone 6 - Cloud Monitoring Dashboard
# ============================================================

resource "google_monitoring_dashboard" "mediclaim" {
  project = "mediclaim-509016"

  dashboard_json = file("${path.module}/mediclaim-dashboard.json")

  lifecycle {
    prevent_destroy = true
  }
}
