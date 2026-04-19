variable "project_id" {
  description = "GCP project ID"
  type        = string
  default     = "andela-digital-twin"
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "europe-west1"
}

variable "service_name" {
  description = "Cloud Run service name"
  type        = string
  default     = "digital-twin"
}

variable "docker_image_tag" {
  description = "Docker image tag to deploy. CI overrides this per commit; Terraform ignores subsequent image drift."
  type        = string
  default     = "bootstrap"
}

variable "openrouter_api_key" {
  description = "OpenRouter API key"
  type        = string
  sensitive   = true
}

variable "chat_model" {
  description = "OpenRouter model identifier"
  type        = string
  default     = "google/gemini-2.5-flash-lite"
}

variable "github_repo" {
  description = "GitHub repository owner allowed to federate via WIF"
  type        = string
  default     = "Toluwalemi/tolu-ai-digital-twin"
}
