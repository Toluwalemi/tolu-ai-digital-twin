resource "google_artifact_registry_repository" "docker" {
  location      = var.region
  repository_id = "${var.service_name}-repo"
  format        = "DOCKER"
  description   = "Docker images for the Digital Twin app"

  depends_on = [google_project_service.apis]
}
