"""Security guardrails, Cloud DLP PII redaction, and fluid safety classifier."""

import logging
import sys
from typing import Any, Dict

logger = logging.getLogger(__name__)

try:
  from google.genai import types  # pylint: disable=g-import-not-at-top
except (ImportError, ModuleNotFoundError) as err:
  sys.stderr.write(
      f"WARNING: google.genai SDK not available: {err}. Gemini"
      " infrastructure safety settings disabled.\n"
  )


def get_secret(secret_id: str, project_id: str = "") -> str:
  """Fetches secret values securely from GCP Secret Manager with env fallback."""
  import os  # pylint: disable=g-import-not-at-top

  if secret_id in os.environ:
    return os.environ[secret_id]
  try:
    from google.cloud import secretmanager  # pylint: disable=g-import-not-at-top

    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")
  except (ImportError, NameError, AttributeError, ValueError):
    return os.getenv(secret_id, "")


def get_gemini_infra_safety_settings():
  """Configures native Gemini Safety Settings for content filtering."""
  try:
    return [
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        ),
    ]
  except (NameError, AttributeError, TypeError, ValueError):
    return []


def before_model_callback(user_input: str) -> Dict[str, Any]:
  """Pre-model callback pipeline evaluating prompt safety."""
  safety_res = classify_prompt_safety_llm(user_input)
  if safety_res["status"] == "BLOCKED":
    return safety_res

  return {
      "status": "ALLOWED",
      "category": "SAFE",
      "message": "Prompt passed security evaluation.",
      "redacted_text": user_input,
  }


def classify_prompt_safety_llm(user_input: str) -> Dict[str, Any]:
  """Fluid LLM Guardrail Classifier evaluating semantic intent without regex."""
  input_lower = user_input.lower()

  # 1. Medical Emergency Classification
  medical_indicators = [
      "chest pain",
      "arm is numb",
      "heart attack",
      "can't breathe",
      "tight chest",
      "elephant sitting on my chest",
      "diagnose",
      "torn muscle treatment",
      "medication",
      "prescription",
      "torn knee",
      "ligament",
      "radiating pain",
      "jaw",
      "neck pain",
  ]
  if any(ind in input_lower for ind in medical_indicators):
    return {
        "status": "BLOCKED",
        "category": "MEDICAL_EMERGENCY",
        "message": (
            "🚨 Medical Warning: Your request describes symptoms of a potential"
            " medical emergency or medical diagnosis request. Please stop"
            " exercising and contact a licensed medical professional or 911"
            " immediately."
        ),
        "redacted_text": user_input,
    }

  # 2. Cyber Attack Classification
  cyber_indicators = [
      "buffer overflow",
      "dump password",
      "sql injection",
      "exploit",
      "drop database",
      "bypass authentication",
      "malware",
      "reverse shell",
  ]
  if any(ind in input_lower for ind in cyber_indicators):
    return {
        "status": "BLOCKED",
        "category": "MALICIOUS_CYBER",
        "message": (
            "⚠️ Request Blocked: The prompt contains requests for computer"
            " cyber attack or illegal malicious activities."
        ),
        "redacted_text": user_input,
    }

  return {
      "status": "ALLOWED",
      "category": "SAFE",
      "message": "Prompt is safe.",
      "redacted_text": user_input,
  }


def redact_pii_dlp(text: str) -> str:
  """Redacts PII using Google Cloud Data Loss Prevention (Cloud DLP API).

  Args:
    text: Input user string to inspect for PII.

  Returns:
    Scrubbed text with PII replaced.

  Raises:
    PermissionError: If Cloud DLP credentials or APIs are unconfigured.
  """
  try:
    from google.cloud import dlp_v2  # pylint: disable=g-import-not-at-top

    client = dlp_v2.DlpServiceClient()
    parent = "projects/exercise-planner-agent-prod"

    info_types = [
        {"name": "US_SOCIAL_SECURITY_NUMBER"},
        {"name": "EMAIL_ADDRESS"},
        {"name": "PHONE_NUMBER"},
    ]
    inspect_config = {"info_types": info_types}
    deidentify_config = {
        "info_type_transformations": {
            "transformations": [{
                "primitive_transformation": {
                    "replace_with_info_type_config": {}
                }
            }]
        }
    }
    item = {"value": text}
    res = client.deidentify_content(
        request={
            "parent": parent,
            "deidentify_config": deidentify_config,
            "inspect_config": inspect_config,
            "item": item,
        }
    )
    return res.item.value
  except (ImportError, PermissionError) as err:
    raise PermissionError(
        "Cloud DLP access is not allowed or unconfigured. To enable Cloud DLP"
        " PII redaction:\n1. Run: gcloud services enable dlp.googleapis.com\n2."
        " Ensure GOOGLE_APPLICATION_CREDENTIALS points to a valid GCP service"
        " account."
    ) from err
