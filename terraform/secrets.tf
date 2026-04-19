resource "google_secret_manager_secret" "openrouter_api_key" {
  secret_id = "${var.service_name}-openrouter-api-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "openrouter_api_key" {
  secret      = google_secret_manager_secret.openrouter_api_key.id
  secret_data = var.openrouter_api_key
}

resource "google_secret_manager_secret_iam_member" "cloud_run_access" {
  secret_id = google_secret_manager_secret.openrouter_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run.email}"
}
