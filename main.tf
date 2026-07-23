# Infrastructure as Code (IaC) Terraform Configuration
# Provisions GCP Cloud Firestore, Secret Manager, and Agent Cloud Run infrastructure

terraform {
  required_version = ">= 1.0.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

variable "project_id" {
  type        = string
  description = "Target GCP Project ID"
  default     = "slichtor-test-sandbox-667157"
}

variable "region" {
  type        = string
  description = "Primary GCP Deployment Region"
  default     = "us-central1"
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Cloud Firestore Native Database instance
resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
}

# Secret Manager instance for API Keys
resource "google_secret_manager_secret" "gemini_api_key" {
  secret_id = "GEMINI_API_KEY"
  replication {
    auto {}
  }
}

# Cloud Run Service deployment for Exercise Agent
resource "google_cloud_run_v2_service" "agent_service" {
  name     = "exercise-planner-agent-service"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    containers {
      image = "gcr.io/${var.project_id}/exercise-planner-agent:latest"
      env {
        name  = "GOOGLE_GENAI_USE_VERTEXAI"
        value = "1"
      }
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
    }
  }
}
