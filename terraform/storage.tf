# GCS bucket for conversation memory.
resource "google_storage_bucket" "memory" {
  name          = "${var.project_id}-memory"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  # Auto-delete conversation files after 7 days.
  lifecycle_rule {
    condition {
      age = 7
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.apis]
}
