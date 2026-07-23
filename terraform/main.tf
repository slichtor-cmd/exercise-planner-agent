# Terraform Infrastructure as Code for Exercise Planner & Tracker Agent (ADK)

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  type        = string
  description = "GCP Project ID"
  default     = "exercise-planner-agent-prod"
}

variable "region" {
  type        = string
  description = "GCP Deployment Region"
  default     = "us-central1"
}

# 1. Cloud Service Account for ADK Engine
resource "google_service_account" "agent_sa" {
  account_id   = "exercise-agent-runner-sa"
  display_name = "Exercise Agent Cloud Run Service Account"
}

# 2. Cloud Firestore Database
resource "google_firestore_database" "default" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
}

# 3. Secret Manager for API Keys & Credentials
resource "google_secret_manager_secret" "api_key_secret" {
  secret_id = "gemini-api-key"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_iam_member" "secret_accessor" {
  secret_id = google_secret_manager_secret.api_key_secret.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.agent_sa.email}"
}

# 4. Cloud Run Service (ADK Engine Hosting)
resource "google_cloud_run_v2_service" "exercise_agent" {
  name     = "exercise-planner-agent"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.agent_sa.email

    containers {
      image = "gcr.io/${var.project_id}/exercise_planner_agent:latest"

      env {
        name  = "FIRESTORE_DB"
        value = google_firestore_database.default.name
      }
      env {
        name  = "OTEL_EXPORTER_OTLP_ENDPOINT"
        value = "https://cloudtrace.googleapis.com"
      }
      env {
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.api_key_secret.secret_id
            version = "latest"
          }
        }
      }

      resources {
        limits = {
          cpu    = "2000m"
          memory = "2Gi"
        }
      }
    }
  }

  depends_on = [
    google_firestore_database.default,
    google_secret_manager_secret_iam_member.secret_accessor
  ]
}

output "cloud_run_service_url" {
  value       = google_cloud_run_v2_service.exercise_agent.uri
  description = "Live HTTPS endpoint for ADK Exercise Planner Agent"
}
