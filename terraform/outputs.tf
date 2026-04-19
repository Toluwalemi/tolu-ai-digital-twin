output "service_url" {
  description = "URL of the deployed Cloud Run service"
  value       = google_cloud_run_v2_service.app.uri
}

output "artifact_registry" {
  description = "Docker image registry path"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker.repository_id}"
}

output "memory_bucket" {
  description = "GCS bucket for conversation memory"
  value       = google_storage_bucket.memory.name
}

output "openrouter_secret_name" {
  description = "Secret Manager resource holding the OpenRouter API key"
  value       = google_secret_manager_secret.openrouter_api_key.name
}

output "wif_provider" {
  description = "Workload Identity Federation provider (used as GCP_WIF_PROVIDER secret)"
  value       = google_iam_workload_identity_pool_provider.github.name
}

output "app_deployer_service_account" {
  description = "App deployer SA email (used as GCP_APP_DEPLOYER_SA secret)"
  value       = google_service_account.app_deployer.email
}

output "infra_deployer_service_account" {
  description = "Infra deployer SA email (use as GCP_INFRA_DEPLOYER_SA secret)"
  value       = google_service_account.infra_deployer.email
}
