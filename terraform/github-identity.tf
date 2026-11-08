# GitHub Actions Workload Identity Pool
resource "google_iam_workload_identity_pool" "github" {
  project                   = "936957989967"
  workload_identity_pool_id = "mediclaim-github"
  display_name              = "MediClaim GitHub Actions"

  lifecycle {
    prevent_destroy = true
  }
}

resource "google_iam_workload_identity_pool_provider" "github" {
  project                            = "936957989967"
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"

  display_name = "MediClaim GitHub Provider"

  attribute_mapping = {
    "google.subject"             = "assertion.sub"
    "attribute.repository"       = "assertion.repository"
    "attribute.repository_owner" = "assertion.repository_owner"
    "attribute.ref"              = "assertion.ref"
  }

  attribute_condition = "assertion.repository=='Yasasvi-20/healthclaim' && assertion.ref=='refs/heads/main'"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "google_service_account" "github_deployer" {
  project      = "mediclaim-509016"
  account_id   = "mediclaim-github-deployer"
  display_name = "MediClaim GitHub Actions Deployer"

  lifecycle {
    prevent_destroy = true
  }
}

resource "google_service_account_iam_member" "github_workload_identity" {
  service_account_id = google_service_account.github_deployer.name
  role               = "roles/iam.workloadIdentityUser"

  member = "principalSet://iam.googleapis.com/projects/936957989967/locations/global/workloadIdentityPools/mediclaim-github/attribute.repository/Yasasvi-20/healthclaim"
}


resource "google_artifact_registry_repository_iam_member" "github_artifact_writer" {
  project    = "mediclaim-509016"
  location   = "us-central1"
  repository = "healthcare-claims"
  role       = "roles/artifactregistry.writer"

  member = "serviceAccount:${google_service_account.github_deployer.email}"
}

resource "google_project_iam_member" "github_cluster_viewer" {
  project = "mediclaim-509016"
  role    = "roles/container.clusterViewer"

  member = "serviceAccount:${google_service_account.github_deployer.email}"
}
