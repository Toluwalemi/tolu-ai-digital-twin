resource "google_service_account" "cloud_run" {
  account_id   = "${var.service_name}-sa"
  display_name = "Digital Twin Cloud Run Service Account"

  depends_on = [google_project_service.apis]
}

resource "google_storage_bucket_iam_member" "memory_access" {
  bucket = google_storage_bucket.memory.name
  role   = "roles/storage.objectUser"
  member = "serviceAccount:${google_service_account.cloud_run.email}"
}


# Identity for GitHub Actions
resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "github-actions-pool"
  display_name              = "GitHub Actions Pool"
  description               = "WIF pool for GitHub Actions CI/CD"

  depends_on = [google_project_service.apis]
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub Provider"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }

  attribute_condition = "assertion.repository == '${var.github_repo}'"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}


# App deployer SA (only builds image and update Cloud Run)
resource "google_service_account" "app_deployer" {
  account_id   = "gh-app-deployer"
  display_name = "GitHub Actions App Deployer"

  depends_on = [google_project_service.apis]
}

resource "google_service_account_iam_member" "app_deployer_wif" {
  service_account_id = google_service_account.app_deployer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repo}"
}

resource "google_project_iam_member" "app_deployer_run" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.app_deployer.email}"
}

resource "google_project_iam_member" "app_deployer_ar_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.app_deployer.email}"
}

resource "google_service_account_iam_member" "app_deployer_act_as_runtime_sa" {
  service_account_id = google_service_account.cloud_run.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.app_deployer.email}"
}


# Infra deployer SA (broader perms for terraform apply)
resource "google_service_account" "infra_deployer" {
  account_id   = "gh-infra-deployer"
  display_name = "GitHub Actions Infra Deployer"

  depends_on = [google_project_service.apis]
}

resource "google_service_account_iam_member" "infra_deployer_wif" {
  service_account_id = google_service_account.infra_deployer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repo}"
}

resource "google_project_iam_member" "infra_deployer_roles" {
  for_each = toset([
    "roles/run.admin",
    "roles/artifactregistry.admin",
    "roles/storage.admin",
    "roles/iam.serviceAccountAdmin",
    "roles/iam.workloadIdentityPoolAdmin",
    "roles/resourcemanager.projectIamAdmin",
    "roles/secretmanager.admin",
    "roles/serviceusage.serviceUsageAdmin",
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.infra_deployer.email}"
}

resource "google_service_account_iam_member" "infra_deployer_act_as_runtime_sa" {
  service_account_id = google_service_account.cloud_run.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.infra_deployer.email}"
}
