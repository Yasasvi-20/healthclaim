terraform {
  backend "gcs" {
    bucket = "mediclaim-terraform-state-509016"
    prefix = "milestone6/gke"
  }
}
