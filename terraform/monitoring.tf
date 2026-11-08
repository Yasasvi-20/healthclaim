# ============================================================
# Milestone 6 - Observability
# ============================================================

resource "google_logging_metric" "mediclaim_http_5xx" {
  project = "mediclaim-509016"

  name = "mediclaim_http_5xx_count"

  description = "Counts HTTP 5xx responses from the MediClaim backend"

  filter = <<-EOT

    resource.type="k8s_container"
    resource.labels.namespace_name="mediclaim"
    resource.labels.container_name="backend"
    jsonPayload.message="HTTP request completed"
    jsonPayload.status_code>=500
    jsonPayload.status_code<600
  EOT

  lifecycle {
    prevent_destroy = true
  }
}

# ============================================================
# Milestone 6 - HTTP 5xx Alert Policy
# ============================================================

resource "google_monitoring_alert_policy" "mediclaim_5xx_alert" {
  project      = "mediclaim-509016"
  display_name = "MediClaim - Backend HTTP 5xx Alert"
  combiner     = "OR"
  enabled      = true

  conditions {
    display_name = "Kubernetes Container - logging/user/mediclaim_http_5xx_count"

    condition_threshold {
      filter = "resource.type = \"k8s_container\" AND metric.type = \"logging.googleapis.com/user/mediclaim_http_5xx_count\""

      comparison      = "COMPARISON_GT"
      threshold_value = 0
      duration        = "0s"

      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_SUM"
        cross_series_reducer = "REDUCE_SUM"
      }

      trigger {
        count = 1
      }
    }
  }

  notification_channels = [
    "projects/mediclaim-509016/notificationChannels/12066239525332148428"
  ]

  alert_strategy {
    notification_prompts = ["OPENED"]
  }

  lifecycle {
    prevent_destroy = true
  }
}
