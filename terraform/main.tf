terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.0"
    }
  }
}

provider "google" {
  project = "mediclaim-509016"
  region  = "us-central1"
}

data "google_compute_network" "default" {
  name = "default"
}

data "google_compute_subnetwork" "default" {
  name   = "default"
  region = "us-central1"
}

resource "google_service_account" "gke_nodes" {
  account_id   = "mediclaim-gke-nodes"
  display_name = "MediClaim GKE Node Service Account"
}

resource "google_project_iam_member" "node_role" {
  project = "mediclaim-509016"
  role    = "roles/container.defaultNodeServiceAccount"
  member  = "serviceAccount:${google_service_account.gke_nodes.email}"
}

resource "google_project_iam_member" "artifact_reader" {
  project = "mediclaim-509016"
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.gke_nodes.email}"
}

resource "google_container_cluster" "mediclaim" {
  name     = "mediclaim-gke"
  location = "us-central1-b"

  network    = data.google_compute_network.default.id
  subnetwork = data.google_compute_subnetwork.default.id

  remove_default_node_pool = true
  initial_node_count       = 1

  deletion_protection = true

  networking_mode = "VPC_NATIVE"

  ip_allocation_policy {
    cluster_ipv4_cidr_block  = "/16"
    services_ipv4_cidr_block = "/20"
  }

  workload_identity_config {
    workload_pool = "mediclaim-509016.svc.id.goog"
  }

  logging_service    = "logging.googleapis.com/kubernetes"
  monitoring_service = "monitoring.googleapis.com/kubernetes"
}

resource "google_container_node_pool" "primary" {
  name     = "mediclaim-pool"
  location = google_container_cluster.mediclaim.location
  cluster  = google_container_cluster.mediclaim.name

  node_count = 2

  node_config {
    machine_type = "e2-standard-2"
    disk_size_gb = 30
    disk_type    = "pd-balanced"

    service_account = google_service_account.gke_nodes.email

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    workload_metadata_config {
      mode = "GKE_METADATA"
    }
  }

  depends_on = [
    google_project_iam_member.node_role,
    google_project_iam_member.artifact_reader
  ]
}
